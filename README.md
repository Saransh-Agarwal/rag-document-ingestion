# RAG Document Ingestion Pipeline

A robust and scalable document ingestion pipeline built with Temporal.io, leveraging Python's asyncio for efficient concurrent processing. This system processes documents from various sources, generates embeddings, and stores them in a Milvus vector database for subsequent use in RAG (Retrieval Augmented Generation) workflows.

## Features

- **Document Processing**: Supports multiple document types (.pdf, .docx, .doc, .xlsx, .xls)
- **Sophisticated Chunking**: Multiple chunking strategies (sentence-based, paragraph-based, fixed-size) with configurable overlap
- **Rate Limiting**: Token bucket rate limiter for API calls
- **Monitoring**: Comprehensive metrics collection and logging
- **Error Handling**: Robust error handling with custom exceptions and retry policies
- **Concurrent Processing**: Efficient async/await patterns for I/O-bound operations
- **Vector Storage**: Milvus integration for efficient vector storage and retrieval

## Prerequisites

- Python 3.8+
- Docker and Docker Compose
- OpenAI API key
- Milvus instance (included in docker-compose)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd rag-ingest
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy the example config file and update it with your settings:
```bash
cp config.py.example config.py
```

## Configuration

Update `config.py` with your settings:
```python
OPENAI_API_KEY = "your-api-key"
MILVUS_HOST = "localhost"
MILVUS_PORT = 19530
```

## Running the Services

1. Start the required services using Docker Compose:
```bash
docker-compose up -d
```

This will start:
- Temporal server and UI
- Milvus vector database
- Required dependencies (PostgreSQL, etc.)

2. Start the worker:
```bash
python worker.py
```

3. Run the client to process a document:
```bash
python client.py --file-id "doc123" --url "https://example.com/document.pdf"
```

## Architecture

### Components

1. **Temporal Workflow**
   - Orchestrates the document processing pipeline
   - Handles retries and error recovery
   - Maintains workflow state

2. **Activities**
   - `fetch_document`: Downloads document from URL
   - `parse_document`: Extracts and chunks text using Unstructured.io
   - `generate_embeddings`: Creates embeddings using OpenAI API
   - `store_in_milvus`: Stores chunks and embeddings in Milvus

3. **Utilities**
   - Rate Limiter: Manages API call rates
   - Chunking Strategy: Configurable text chunking
   - Monitoring: Metrics collection and logging

### Concurrency Model

The system leverages Python's asyncio for efficient concurrent processing:
- Activities run concurrently within the worker
- Rate limiting prevents API overload
- Batch processing for Milvus operations

## Error Handling

The system implements comprehensive error handling:
- Custom exceptions for different error types
- Retry policies for transient failures
- Detailed error logging and metrics

## Monitoring

Metrics are collected for:
- Activity durations
- Success/failure rates
- Processing times
- Resource usage

View metrics in the logs or integrate with your monitoring system.

## Testing

Run the test suite:
```bash
pytest test_workflow.py -v
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License

## Acknowledgments

- Temporal.io for workflow orchestration
- Unstructured.io for document parsing
- OpenAI for embeddings
- Milvus for vector storage
