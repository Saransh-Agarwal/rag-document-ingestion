import random
import asyncio
from typing import List
import logging

logger = logging.getLogger(__name__)

class MockOpenAIClient:
    """Mock OpenAI client for testing purposes"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        
    async def embeddings_create(self, input: List[str], model: str = "text-embedding-ada-002") -> List[List[float]]:
        """Generate mock embeddings for testing"""
        await asyncio.sleep(0.1)  # Simulate API delay
        
        embeddings = []
        for text in input:
            # Generate deterministic mock embeddings based on text hash
            random.seed(hash(text) % (2**32))
            embedding = [random.uniform(-1, 1) for _ in range(1536)]  # OpenAI ada-002 dimension
            embeddings.append(embedding)
            
        logger.info(f"Generated {len(embeddings)} mock embeddings")
        return embeddings

class MockEmbeddingsResponse:
    def __init__(self, embeddings: List[List[float]]):
        self.data = [MockEmbeddingData(emb) for emb in embeddings]

class MockEmbeddingData:
    def __init__(self, embedding: List[float]):
        self.embedding = embedding

async def create_mock_embeddings(input_texts: List[str], model: str = "text-embedding-ada-002") -> MockEmbeddingsResponse:
    """Create mock embeddings response"""
    client = MockOpenAIClient()
    embeddings = await client.embeddings_create(input_texts, model)
    return MockEmbeddingsResponse(embeddings) 