from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType
from config import MILVUS_HOST, MILVUS_PORT
import logging
from typing import List, Tuple
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

COLLECTION_NAME = "rag_chunks"
VECTOR_DIM = 1536  # OpenAI embedding size
BATCH_SIZE = 100  # Number of records to insert in one batch

fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema(name="file_id", dtype=DataType.VARCHAR, max_length=128, is_primary=False),
    FieldSchema(name="chunk_index", dtype=DataType.INT64, is_primary=False),
    FieldSchema(name="chunk_text", dtype=DataType.VARCHAR, max_length=16384, is_primary=False),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=VECTOR_DIM, is_primary=False),
]
schema = CollectionSchema(fields, description="RAG document chunks")

def connect_milvus():
    try:
        connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)
        logger.info("Successfully connected to Milvus")
    except Exception as e:
        logger.error(f"Failed to connect to Milvus: {e}")
        raise

def ensure_collection():
    try:
        connect_milvus()
        if COLLECTION_NAME not in Collection.list_collections():
            Collection(COLLECTION_NAME, schema)
            logger.info(f"Created new collection: {COLLECTION_NAME}")
        else:
            logger.info(f"Using existing collection: {COLLECTION_NAME}")
    except Exception as e:
        logger.error(f"Error ensuring collection exists: {e}")
        raise

def batch_insert_chunks(chunks_data: List[Tuple[str, int, str, List[float]]]):
    """
    Insert multiple chunks in batches for better performance
    chunks_data: List of tuples (file_id, chunk_index, chunk_text, embedding)
    """
    try:
        ensure_collection()
        col = Collection(COLLECTION_NAME)
        
        # Prepare batch data
        file_ids, chunk_indices, chunk_texts, embeddings = [], [], [], []
        
        for file_id, chunk_index, chunk_text, embedding in chunks_data:
            file_ids.append(file_id)
            chunk_indices.append(chunk_index)
            chunk_texts.append(chunk_text)
            embeddings.append(embedding)
            
            # Insert when batch size is reached
            if len(file_ids) >= BATCH_SIZE:
                # Note: We don't include the primary key 'id' as it's auto-generated
                data = [file_ids, chunk_indices, chunk_texts, embeddings]
                col.insert(data)
                logger.info(f"Inserted batch of {len(file_ids)} chunks")
                file_ids, chunk_indices, chunk_texts, embeddings = [], [], [], []
        
        # Insert remaining chunks
        if file_ids:
            # Note: We don't include the primary key 'id' as it's auto-generated
            data = [file_ids, chunk_indices, chunk_texts, embeddings]
            col.insert(data)
            logger.info(f"Inserted final batch of {len(file_ids)} chunks")
            
    except Exception as e:
        logger.error(f"Error in batch insert: {e}")
        raise

async def insert_chunk(file_id: str, chunk_index: int, chunk_text: str, embedding: List[float]):
    """
    Single chunk insert - maintained for backward compatibility
    """
    try:
        ensure_collection()
        col = Collection(COLLECTION_NAME)
        # Note: We don't include the primary key 'id' as it's auto-generated
        data = [[file_id], [chunk_index], [chunk_text], [embedding]]
        col.insert(data)
        logger.debug(f"Inserted chunk {chunk_index} for file {file_id}")
    except Exception as e:
        logger.error(f"Error inserting chunk: {e}")
        raise 