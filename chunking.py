from typing import List, Optional
import re
from dataclasses import dataclass
import logging
from nltk.tokenize import sent_tokenize
import nltk

logger = logging.getLogger(__name__)

@dataclass
class ChunkingConfig:
    max_chunk_size: int = 1000
    min_chunk_size: int = 100
    overlap_size: int = 50
    strategy: str = "sentence"  # sentence, paragraph, or fixed

class ChunkingStrategy:
    def __init__(self, config: ChunkingConfig):
        self.config = config
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')

    def chunk_text(self, text: str) -> List[str]:
        if self.config.strategy == "sentence":
            return self._chunk_by_sentence(text)
        elif self.config.strategy == "paragraph":
            return self._chunk_by_paragraph(text)
        else:
            return self._chunk_by_fixed_size(text)

    def _chunk_by_sentence(self, text: str) -> List[str]:
        sentences = sent_tokenize(text)
        chunks = []
        current_chunk = []
        current_size = 0

        for sentence in sentences:
            sentence_size = len(sentence)
            
            if current_size + sentence_size > self.config.max_chunk_size:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                current_chunk = [sentence]
                current_size = sentence_size
            else:
                current_chunk.append(sentence)
                current_size += sentence_size

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return self._apply_overlap(chunks)

    def _chunk_by_paragraph(self, text: str) -> List[str]:
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = []
        current_size = 0

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            paragraph_size = len(paragraph)
            
            if current_size + paragraph_size > self.config.max_chunk_size:
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                current_chunk = [paragraph]
                current_size = paragraph_size
            else:
                current_chunk.append(paragraph)
                current_size += paragraph_size

        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        return self._apply_overlap(chunks)

    def _chunk_by_fixed_size(self, text: str) -> List[str]:
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = min(start + self.config.max_chunk_size, text_length)
            
            # Try to find a natural break point
            if end < text_length:
                # Look for the last period, space, or newline
                break_chars = [". ", " ", "\n"]
                for char in break_chars:
                    last_break = text.rfind(char, start, end)
                    if last_break != -1:
                        end = last_break + 1
                        break

            chunk = text[start:end].strip()
            if len(chunk) >= self.config.min_chunk_size:
                chunks.append(chunk)
            
            start = end - self.config.overlap_size

        return chunks

    def _apply_overlap(self, chunks: List[str]) -> List[str]:
        if not chunks or self.config.overlap_size == 0:
            return chunks

        overlapped_chunks = []
        for i, chunk in enumerate(chunks):
            if i > 0:
                # Get overlap from previous chunk
                prev_chunk = chunks[i-1]
                overlap_start = max(0, len(prev_chunk) - self.config.overlap_size)
                overlap = prev_chunk[overlap_start:]
                
                # Add overlap to current chunk
                chunk = overlap + " " + chunk

            overlapped_chunks.append(chunk)

        return overlapped_chunks 