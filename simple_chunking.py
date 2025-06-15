from typing import List
from dataclasses import dataclass
import logging
import re

logger = logging.getLogger(__name__)

@dataclass
class SimpleChunkingConfig:
    max_chunk_size: int = 1000
    min_chunk_size: int = 100
    overlap_size: int = 50

class SimpleChunkingStrategy:
    def __init__(self, config: SimpleChunkingConfig):
        self.config = config

    def chunk_text(self, text: str) -> List[str]:
        """Simple text chunking without external dependencies"""
        # Split by sentences using simple regex
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        current_chunk = []
        current_size = 0

        for sentence in sentences:
            sentence_size = len(sentence)
            
            if current_size + sentence_size > self.config.max_chunk_size:
                if current_chunk:
                    chunks.append(". ".join(current_chunk) + ".")
                current_chunk = [sentence]
                current_size = sentence_size
            else:
                current_chunk.append(sentence)
                current_size += sentence_size

        if current_chunk:
            chunks.append(". ".join(current_chunk) + ".")

        # Filter out chunks that are too small
        chunks = [chunk for chunk in chunks if len(chunk) >= self.config.min_chunk_size]
        
        logger.info(f"Created {len(chunks)} chunks using simple strategy")
        return chunks 