import aiohttp
import tempfile
import os
import logging
from typing import List, Dict, Any
from temporalio import activity
from temporalio.exceptions import ApplicationError
from unstructured.partition.auto import partition
from openai import AsyncOpenAI
from milvus_utils import batch_insert_chunks
from config import OPENAI_API_KEY
from rate_limiter import TokenBucketRateLimiter
from chunking import ChunkingStrategy, ChunkingConfig
from monitoring import WorkflowMetrics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize rate limiter for OpenAI API
openai_rate_limiter = TokenBucketRateLimiter(tokens_per_second=3, bucket_size=10)

# Initialize chunking strategy
chunking_strategy = ChunkingStrategy(ChunkingConfig(
    max_chunk_size=1000,
    min_chunk_size=100,
    overlap_size=50,
    strategy="sentence"
))

# Initialize metrics
metrics = WorkflowMetrics()

# Custom exceptions
class DocumentFetchError(ApplicationError):
    def __init__(self, message: str):
        super().__init__(message, type="DocumentFetchError")

class DocumentParseError(ApplicationError):
    def __init__(self, message: str):
        super().__init__(message, type="DocumentParseError")

class EmbeddingError(ApplicationError):
    def __init__(self, message: str):
        super().__init__(message, type="EmbeddingError")

class StorageError(ApplicationError):
    def __init__(self, message: str):
        super().__init__(message, type="StorageError")

SUPPORTED_TYPES = {".pdf", ".docx", ".doc", ".xlsx", ".xls"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit

@activity.defn
async def fetch_document(url: str) -> str:
    with metrics.measure_activity("fetch_document", {"url": url}) as activity_metrics:
        ext = os.path.splitext(url)[-1].lower()
        if ext not in SUPPORTED_TYPES:
            raise DocumentFetchError(f"Unsupported file type: {ext}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        raise DocumentFetchError(f"Failed to fetch file: HTTP {resp.status}")
                    
                    content_length = int(resp.headers.get('content-length', 0))
                    if content_length > MAX_FILE_SIZE:
                        raise DocumentFetchError(f"File too large: {content_length} bytes")
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as f:
                        f.write(await resp.read())
                        logger.info(f"Successfully downloaded file to {f.name}")
                        activity_metrics.metadata["file_size"] = content_length
                        return f.name
        except aiohttp.ClientError as e:
            raise DocumentFetchError(f"Network error while fetching document: {e}")
        except Exception as e:
            raise DocumentFetchError(f"Error fetching document: {e}")

@activity.defn
async def parse_document(file_path: str) -> List[str]:
    with metrics.measure_activity("parse_document", {"file_path": file_path}) as activity_metrics:
        try:
            elements = partition(filename=file_path)
            text = " ".join([el.text for el in elements if hasattr(el, "text") and el.text.strip()])
            
            # Use sophisticated chunking
            chunks = chunking_strategy.chunk_text(text)
            
            if not chunks:
                raise DocumentParseError("No text chunks parsed from document")
            
            logger.info(f"Successfully parsed {len(chunks)} chunks from document")
            activity_metrics.metadata["chunk_count"] = len(chunks)
            return chunks
        except Exception as e:
            raise DocumentParseError(f"Error parsing document: {e}")
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"Cleaned up temporary file: {file_path}")

@activity.defn
async def generate_embeddings(chunks: List[str]) -> List[List[float]]:
    with metrics.measure_activity("generate_embeddings", {"chunk_count": len(chunks)}) as activity_metrics:
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        try:
            embeddings = []
            for chunk in chunks:
                # Apply rate limiting
                await openai_rate_limiter.acquire()
                
                response = await client.embeddings.create(
                    input=[chunk],
                    model="text-embedding-ada-002"
                )
                embeddings.extend([d.embedding for d in response.data])
            
            logger.info(f"Generated {len(embeddings)} embeddings")
            activity_metrics.metadata["embedding_count"] = len(embeddings)
            return embeddings
        except Exception as e:
            raise EmbeddingError(f"Error generating embeddings: {e}")

@activity.defn
async def store_in_milvus(file_id: str, chunks: List[str], embeddings: List[List[float]]) -> Dict[str, Any]:
    with metrics.measure_activity("store_in_milvus", {
        "file_id": file_id,
        "chunk_count": len(chunks)
    }) as activity_metrics:
        try:
            # Prepare data for batch insert
            chunks_data = [
                (file_id, idx, chunk, embedding)
                for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings))
            ]
            
            # Perform batch insert
            batch_insert_chunks(chunks_data)
            
            logger.info(f"Successfully stored {len(chunks)} chunks for file {file_id}")
            activity_metrics.metadata["chunks_stored"] = len(chunks)
            return {
                "status": "success",
                "file_id": file_id,
                "chunks_stored": len(chunks)
            }
        except Exception as e:
            raise StorageError(f"Error storing in Milvus: {e}") 