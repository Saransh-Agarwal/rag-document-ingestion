import pytest
import os
import tempfile
from unittest.mock import Mock, patch, AsyncMock
from activities import (
    fetch_document, parse_document, generate_embeddings, store_in_milvus,
    DocumentFetchError, DocumentParseError, EmbeddingError, StorageError
)
from workflow import IngestDocumentWorkflow
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

# Test data
TEST_FILE_ID = "test123"
TEST_URL = "https://example.com/test.pdf"
TEST_CHUNKS = ["This is chunk 1", "This is chunk 2"]
TEST_EMBEDDINGS = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]

@pytest.fixture
def mock_temp_file():
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(b"Test PDF content")
        yield f.name
    os.unlink(f.name)

@pytest.mark.asyncio
async def test_fetch_document_success():
    with patch("aiohttp.ClientSession") as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=b"Test content")
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response

        file_path = await fetch_document(TEST_URL)
        assert os.path.exists(file_path)
        os.unlink(file_path)

@pytest.mark.asyncio
async def test_fetch_document_unsupported_type():
    with pytest.raises(DocumentFetchError):
        await fetch_document("https://example.com/test.txt")

@pytest.mark.asyncio
async def test_parse_document_success(mock_temp_file):
    with patch("unstructured.partition.auto.partition") as mock_partition:
        mock_element = Mock()
        mock_element.text = "Test content"
        mock_partition.return_value = [mock_element]

        chunks = await parse_document(mock_temp_file)
        assert len(chunks) == 1
        assert chunks[0] == "Test content"

@pytest.mark.asyncio
async def test_generate_embeddings_success():
    with patch("openai.AsyncOpenAI") as mock_client:
        mock_response = AsyncMock()
        mock_response.data = [
            Mock(embedding=[0.1, 0.2, 0.3]),
            Mock(embedding=[0.4, 0.5, 0.6])
        ]
        mock_client.return_value.embeddings.create.return_value = mock_response

        embeddings = await generate_embeddings(TEST_CHUNKS)
        assert len(embeddings) == 2
        assert len(embeddings[0]) == 3

@pytest.mark.asyncio
async def test_store_in_milvus_success():
    with patch("milvus_utils.batch_insert_chunks") as mock_insert:
        result = await store_in_milvus(TEST_FILE_ID, TEST_CHUNKS, TEST_EMBEDDINGS)
        assert result["status"] == "success"
        assert result["file_id"] == TEST_FILE_ID
        assert result["chunks_stored"] == len(TEST_CHUNKS)

@pytest.mark.asyncio
async def test_workflow_integration():
    async with WorkflowEnvironment() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[IngestDocumentWorkflow],
            activities=[
                fetch_document,
                parse_document,
                generate_embeddings,
                store_in_milvus
            ]
        ):
            # Mock the activities
            env.mock_activity(fetch_document, return_value="test.pdf")
            env.mock_activity(parse_document, return_value=TEST_CHUNKS)
            env.mock_activity(generate_embeddings, return_value=TEST_EMBEDDINGS)
            env.mock_activity(store_in_milvus, return_value={
                "status": "success",
                "file_id": TEST_FILE_ID,
                "chunks_stored": len(TEST_CHUNKS)
            })

            # Run the workflow
            result = await env.client.execute_workflow(
                IngestDocumentWorkflow.run,
                TEST_FILE_ID,
                TEST_URL,
                id="test-workflow",
                task_queue="test-queue"
            )

            assert result["status"] == "success"
            assert result["file_id"] == TEST_FILE_ID
            assert result["chunks_stored"] == len(TEST_CHUNKS) 