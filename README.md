# RAG Document Ingestion Pipeline

A robust and scalable document ingestion pipeline built with Temporal.io, leveraging Python's asyncio for efficient concurrent processing. This system processes documents from various sources, generates embeddings, and stores them in a Milvus vector database for subsequent use in RAG (Retrieval Augmented Generation) workflows.

## 🚀 Features

- **Document Processing**: Supports multiple document types (.pdf, .docx, .doc, .xlsx, .xls, .txt)
- **Sophisticated Chunking**: Multiple chunking strategies (sentence-based, paragraph-based, fixed-size) with configurable overlap
- **Rate Limiting**: Token bucket rate limiter for API calls
- **Monitoring**: Comprehensive metrics collection and logging
- **Error Handling**: Robust error handling with custom exceptions and retry policies
- **Concurrent Processing**: Efficient async/await patterns for I/O-bound operations
- **Vector Storage**: Milvus integration for efficient vector storage and retrieval
- **Mock Mode**: Can run without OpenAI API key using mock embeddings for testing

## 📋 Prerequisites

- Python 3.8+
- Docker and Docker Compose
- OpenAI API key (optional - can use mock embeddings)

## 🛠️ Installation & Setup

### 1. Clone and Setup Environment

```bash
git clone <repository-url>
cd rag-document-ingestion
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configuration

Copy the example config and update with your settings:
```bash
cp config.py.example config.py
```

Edit `config.py`:
```python
OPENAI_API_KEY = "your-api-key"  # Optional - leave as-is for mock mode
MILVUS_HOST = "localhost"
MILVUS_PORT = 19530
TEMPORAL_ADDRESS = "localhost:7233"
```

### 3. Start Infrastructure Services

```bash
docker-compose up -d
```

This starts:
- Temporal server and UI (http://localhost:8080)
- Milvus vector database (localhost:19530)
- PostgreSQL database for Temporal
- MinIO for Milvus storage

### 4. Verify Services

```bash
docker-compose ps
```

All services should show "Up" status.

## 🏃‍♂️ Running the Pipeline

### 1. Start the Temporal Worker

```bash
python worker.py
```

### 2. Start Sample Document Server (for testing)

In a new terminal:
```bash
python simple_server.py
```

### 3. Trigger a Workflow

In another terminal:
```bash
python client.py --file-id "sample-doc-001" --url "http://localhost:8000/sample_document.txt"
```

## 🏗️ Architecture & Design

### System Components

1. **Temporal Workflow Engine**
   - Orchestrates the entire document processing pipeline
   - Handles retries, error recovery, and state management
   - Provides visibility through the Temporal UI

2. **Activities (Processing Steps)**
   - `fetch_document`: Downloads documents with validation and size limits
   - `parse_document`: Extracts and chunks text using Unstructured.io
   - `generate_embeddings`: Creates vector embeddings (OpenAI or mock)
   - `store_in_milvus`: Batch stores chunks and embeddings

3. **Supporting Utilities**
   - Rate Limiter: Token bucket algorithm for API rate limiting
   - Chunking Strategy: Configurable text segmentation
   - Monitoring: Comprehensive metrics collection
   - Mock Embeddings: Testing without external API dependencies

### Workflow Structure

```python
@workflow.defn
class IngestDocumentWorkflow:
    async def run(self, file_id: str, url: str):
        # 1. Fetch document from URL
        file_path = await workflow.execute_activity(fetch_document, url)
        
        # 2. Parse and chunk document
        chunks = await workflow.execute_activity(parse_document, file_path)
        
        # 3. Generate embeddings
        embeddings = await workflow.execute_activity(generate_embeddings, chunks)
        
        # 4. Store in vector database
        result = await workflow.execute_activity(store_in_milvus, file_id, chunks, embeddings)
        
        return result
```

### Asyncio Concurrency Model

The system leverages Python's asyncio for efficient concurrent processing:

- **Non-blocking I/O**: All network operations (HTTP requests, API calls, database writes) use async/await
- **Rate Limiting**: Prevents API overload while maintaining high throughput
- **Batch Processing**: Groups operations for better performance
- **Resource Efficiency**: Single worker process handles multiple concurrent workflows

### Error Handling Strategy

Custom exception hierarchy for different failure scenarios:

```python
class DocumentFetchError(ApplicationError):  # Network/download issues
class DocumentParseError(ApplicationError):  # Text extraction failures  
class EmbeddingError(ApplicationError):      # API/embedding issues
class StorageError(ApplicationError):        # Database problems
```

Each activity includes retry policies with exponential backoff:
- Transient errors: Automatic retries with backoff
- Permanent errors: Immediate failure with detailed logging
- Timeout handling: Configurable timeouts per activity

### Milvus Schema Design

```python
Collection: "rag_chunks"
Fields:
- file_id (VARCHAR): Document identifier
- chunk_index (INT64): Chunk sequence number  
- chunk_text (VARCHAR): Original text content
- embedding (FLOAT_VECTOR[1536]): Vector embedding
```

Benefits:
- Efficient similarity search on embeddings
- Metadata filtering by file_id
- Ordered chunk retrieval by index
- Scalable vector storage

### Key Design Decisions

1. **Temporal for Orchestration**: Provides reliability, visibility, and state management
2. **Asyncio for Concurrency**: Maximizes I/O throughput without thread overhead
3. **Batch Processing**: Reduces database round-trips and improves performance
4. **Custom Exceptions**: Enable specific error handling and better debugging
5. **Mock Mode**: Allows testing without external API dependencies
6. **Modular Architecture**: Clean separation of concerns for maintainability

## 📊 Monitoring & Observability

### Metrics Collected

- Activity execution times and success rates
- Document processing throughput
- Embedding generation performance
- Storage operation metrics
- Error rates by type

### Logging

Structured logging at multiple levels:
- INFO: Normal operation progress
- DEBUG: Detailed execution traces  
- ERROR: Failures with context
- WARN: Recoverable issues

### Temporal UI

Access the Temporal UI at http://localhost:8080 to:
- Monitor workflow executions
- View activity details and retries
- Debug failures with full stack traces
- Analyze performance metrics

## 🧪 Testing

Run the test suite:
```bash
pytest test_workflow.py -v
```

Tests cover:
- Individual activity functionality
- Error handling scenarios
- Integration workflow execution
- Mock embedding generation

## 📁 Project Structure

```
rag-document-ingestion/
├── activities.py          # Temporal activities (fetch, parse, embed, store)
├── workflow.py           # Temporal workflow definition
├── worker.py             # Temporal worker runner
├── client.py             # Workflow trigger script
├── milvus_utils.py       # Vector database utilities
├── rate_limiter.py       # API rate limiting
├── chunking.py           # Text chunking strategies
├── monitoring.py         # Metrics collection
├── mock_embeddings.py    # Mock embeddings for testing
├── simple_server.py      # Test document server
├── config.py.example     # Configuration template
├── docker-compose.yml    # Infrastructure setup
├── requirements.txt      # Python dependencies
├── test_workflow.py      # Test suite
└── README.md            # This file
```

## 🔧 Configuration Options

### Chunking Strategy
```python
ChunkingConfig(
    max_chunk_size=1000,    # Maximum characters per chunk
    min_chunk_size=100,     # Minimum characters per chunk  
    overlap_size=50,        # Character overlap between chunks
    strategy="sentence"     # "sentence", "paragraph", or "fixed"
)
```

### Rate Limiting
```python
TokenBucketRateLimiter(
    tokens_per_second=3,    # API calls per second
    bucket_size=10          # Burst capacity
)
```

### Retry Policies
```python
retry_policy={
    "maximum_attempts": 3,
    "initial_interval": 1,
    "maximum_interval": 10,
    "backoff_coefficient": 2
}
```

## 🚨 Troubleshooting

### Common Issues

1. **Services not starting**: Check Docker is running and ports are available
2. **Worker connection failed**: Ensure Temporal server is running on port 7233
3. **Milvus connection error**: Verify Milvus is healthy and accessible
4. **Document fetch failed**: Check URL accessibility and file type support
5. **Embedding errors**: Verify OpenAI API key or use mock mode

### Debug Commands

```bash
# Check service status
docker-compose ps

# View service logs
docker-compose logs temporal
docker-compose logs milvus

# Test document server
curl http://localhost:8000/sample_document.txt

# Check Temporal UI
open http://localhost:8080
```

## 🎯 Production Considerations

### Scalability
- Deploy multiple workers for higher throughput
- Use Temporal Cloud for managed orchestration
- Scale Milvus cluster for large datasets
- Implement connection pooling

### Security
- Secure API keys with proper secret management
- Use TLS for all network communications
- Implement authentication for Temporal UI
- Validate and sanitize all inputs

### Monitoring
- Integrate with Prometheus/Grafana
- Set up alerting for failures
- Monitor resource usage
- Track business metrics

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📞 Support

For questions or issues:
- Check the troubleshooting section
- Review Temporal documentation
- Open an issue on GitHub
