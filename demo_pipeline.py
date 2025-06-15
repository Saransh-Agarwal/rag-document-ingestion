#!/usr/bin/env python3
"""
Standalone demo of the RAG Document Ingestion Pipeline
This script demonstrates the core functionality without requiring Temporal infrastructure
"""
import asyncio
import logging
import sys
import os
from typing import List, Dict, Any

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from activities import (
    fetch_document, parse_document, generate_embeddings, store_in_milvus,
    DocumentFetchError, DocumentParseError, EmbeddingError, StorageError
)
from monitoring import WorkflowMetrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DemoPipeline:
    def __init__(self):
        self.metrics = WorkflowMetrics()
    
    async def run_pipeline(self, file_id: str, url: str) -> Dict[str, Any]:
        """Run the complete document ingestion pipeline"""
        
        logger.info(f"🚀 Starting RAG Document Ingestion Pipeline")
        logger.info(f"📄 File ID: {file_id}")
        logger.info(f"🔗 URL: {url}")
        
        with self.metrics.measure_workflow(file_id, {
            "file_id": file_id,
            "url": url
        }) as workflow_metrics:
            try:
                # Step 1: Fetch Document
                logger.info("📥 Step 1: Fetching document...")
                file_path = await fetch_document(url)
                logger.info(f"✅ Document fetched successfully: {file_path}")
                
                # Step 2: Parse Document
                logger.info("📝 Step 2: Parsing and chunking document...")
                chunks = await parse_document(file_path)
                logger.info(f"✅ Document parsed into {len(chunks)} chunks")
                
                # Step 3: Generate Embeddings
                logger.info("🧠 Step 3: Generating embeddings...")
                embeddings = await generate_embeddings(chunks)
                logger.info(f"✅ Generated {len(embeddings)} embeddings")
                
                # Step 4: Store in Milvus
                logger.info("💾 Step 4: Storing in vector database...")
                result = await store_in_milvus(file_id, chunks, embeddings)
                logger.info(f"✅ Successfully stored {result['chunks_stored']} chunks")
                
                # Log final metrics
                self.metrics.log_workflow_metrics()
                
                logger.info("🎉 Pipeline completed successfully!")
                return result
                
            except DocumentFetchError as e:
                logger.error(f"❌ Document fetch error: {e}")
                workflow_metrics.metadata["error_type"] = "fetch_error"
                return {"status": "error", "error_type": "fetch_error", "error": str(e)}
            except DocumentParseError as e:
                logger.error(f"❌ Document parse error: {e}")
                workflow_metrics.metadata["error_type"] = "parse_error"
                return {"status": "error", "error_type": "parse_error", "error": str(e)}
            except EmbeddingError as e:
                logger.error(f"❌ Embedding generation error: {e}")
                workflow_metrics.metadata["error_type"] = "embedding_error"
                return {"status": "error", "error_type": "embedding_error", "error": str(e)}
            except StorageError as e:
                logger.error(f"❌ Storage error: {e}")
                workflow_metrics.metadata["error_type"] = "storage_error"
                return {"status": "error", "error_type": "storage_error", "error": str(e)}
            except Exception as e:
                logger.error(f"❌ Unexpected error: {e}")
                workflow_metrics.metadata["error_type"] = "unknown_error"
                return {"status": "error", "error_type": "unknown_error", "error": str(e)}

async def main():
    """Main demo function"""
    
    # Demo parameters
    file_id = "demo-sample-001"
    url = "http://localhost:8000/sample_document.txt"
    
    # Create and run pipeline
    pipeline = DemoPipeline()
    result = await pipeline.run_pipeline(file_id, url)
    
    # Print final result
    print("\n" + "="*60)
    print("📊 FINAL RESULT:")
    print("="*60)
    for key, value in result.items():
        print(f"{key}: {value}")
    print("="*60)
    
    return result

if __name__ == "__main__":
    print("🔥 RAG Document Ingestion Pipeline Demo")
    print("="*60)
    print("This demo shows the complete pipeline functionality")
    print("using mock embeddings (no OpenAI API key required)")
    print("="*60)
    
    try:
        result = asyncio.run(main())
        if result.get("status") == "success":
            print("\n✅ Demo completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Demo failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Demo failed with error: {e}")
        sys.exit(1) 