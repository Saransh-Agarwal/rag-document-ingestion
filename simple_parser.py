import os
import logging
from typing import List

logger = logging.getLogger(__name__)

def simple_parse_text_file(file_path: str) -> str:
    """Simple text file parser"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        logger.info(f"Successfully parsed text file: {len(content)} characters")
        return content
    except UnicodeDecodeError:
        # Try with different encoding
        with open(file_path, 'r', encoding='latin-1') as f:
            content = f.read()
        logger.info(f"Successfully parsed text file with latin-1 encoding: {len(content)} characters")
        return content

def parse_document_simple(file_path: str) -> str:
    """Parse document using simple methods"""
    ext = os.path.splitext(file_path)[-1].lower()
    
    if ext == '.txt':
        return simple_parse_text_file(file_path)
    else:
        # For other file types, try to read as text
        try:
            return simple_parse_text_file(file_path)
        except Exception as e:
            logger.warning(f"Could not parse {ext} file as text: {e}")
            # Return a placeholder text for demo purposes
            return f"Demo content for {ext} file. This would normally be parsed using appropriate libraries." 