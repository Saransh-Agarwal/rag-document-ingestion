import logging
from typing import List, Tuple, Dict, Any
import json

logger = logging.getLogger(__name__)

class MockVectorStorage:
    """Mock vector storage for demonstration purposes"""
    
    def __init__(self):
        self.storage = []
        self.collection_created = False
    
    def ensure_collection(self):
        """Mock collection creation"""
        if not self.collection_created:
            logger.info("Created mock collection: rag_chunks")
            self.collection_created = True
        else:
            logger.info("Using existing mock collection: rag_chunks")
    
    def batch_insert_chunks(self, chunks_data: List[Tuple[str, int, str, List[float]]]):
        """Mock batch insert for chunks"""
        try:
            self.ensure_collection()
            
            for file_id, chunk_index, chunk_text, embedding in chunks_data:
                record = {
                    "id": len(self.storage) + 1,  # Auto-generated ID
                    "file_id": file_id,
                    "chunk_index": chunk_index,
                    "chunk_text": chunk_text[:100] + "..." if len(chunk_text) > 100 else chunk_text,  # Truncate for display
                    "embedding_dim": len(embedding),
                    "embedding_sample": embedding[:5]  # Show first 5 values
                }
                self.storage.append(record)
            
            logger.info(f"Mock: Inserted batch of {len(chunks_data)} chunks")
            logger.info(f"Mock: Total records in storage: {len(self.storage)}")
            
            # Log sample of what was stored
            if chunks_data:
                sample_record = self.storage[-1]
                logger.info(f"Mock: Sample stored record: {json.dumps(sample_record, indent=2)}")
                
        except Exception as e:
            logger.error(f"Mock storage error: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        return {
            "total_records": len(self.storage),
            "collections": ["rag_chunks"] if self.collection_created else [],
            "sample_records": self.storage[:3] if self.storage else []
        }

# Global mock storage instance
mock_storage = MockVectorStorage() 