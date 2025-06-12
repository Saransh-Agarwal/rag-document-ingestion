from temporalio import workflow
from temporalio.exceptions import ApplicationError
import logging
from typing import Dict, Any
from activities import (
    fetch_document, parse_document, generate_embeddings, store_in_milvus,
    DocumentFetchError, DocumentParseError, EmbeddingError, StorageError,
    metrics
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@workflow.defn
class IngestDocumentWorkflow:
    @workflow.run
    async def run(self, file_id: str, url: str) -> Dict[str, Any]:
        with metrics.measure_workflow(file_id, {
            "file_id": file_id,
            "url": url
        }) as workflow_metrics:
            try:
                # Fetch document
                file_path = await workflow.execute_activity(
                    fetch_document,
                    url,
                    schedule_to_close_timeout=120,
                    retry_policy={
                        "maximum_attempts": 3,
                        "initial_interval": 1,
                        "maximum_interval": 10,
                        "backoff_coefficient": 2,
                    },
                )
                logger.info(f"Document fetched successfully for file_id: {file_id}")

                # Parse document
                chunks = await workflow.execute_activity(
                    parse_document,
                    file_path,
                    schedule_to_close_timeout=120,
                    retry_policy={
                        "maximum_attempts": 2,
                        "initial_interval": 1,
                        "maximum_interval": 5,
                    },
                )
                logger.info(f"Document parsed into {len(chunks)} chunks for file_id: {file_id}")

                # Generate embeddings
                embeddings = await workflow.execute_activity(
                    generate_embeddings,
                    chunks,
                    schedule_to_close_timeout=120,
                    retry_policy={
                        "maximum_attempts": 3,
                        "initial_interval": 1,
                        "maximum_interval": 10,
                        "backoff_coefficient": 2,
                    },
                )
                logger.info(f"Generated embeddings for {len(embeddings)} chunks for file_id: {file_id}")

                # Store in Milvus
                result = await workflow.execute_activity(
                    store_in_milvus,
                    file_id, chunks, embeddings,
                    schedule_to_close_timeout=180,
                    retry_policy={
                        "maximum_attempts": 3,
                        "initial_interval": 1,
                        "maximum_interval": 10,
                        "backoff_coefficient": 2,
                    },
                )
                logger.info(f"Successfully completed workflow for file_id: {file_id}")
                
                # Log final metrics
                metrics.log_workflow_metrics()
                return result

            except DocumentFetchError as e:
                logger.error(f"Document fetch error for file_id {file_id}: {e}")
                workflow_metrics.metadata["error_type"] = "fetch_error"
                return {"status": "error", "error_type": "fetch_error", "error": str(e)}
            except DocumentParseError as e:
                logger.error(f"Document parse error for file_id {file_id}: {e}")
                workflow_metrics.metadata["error_type"] = "parse_error"
                return {"status": "error", "error_type": "parse_error", "error": str(e)}
            except EmbeddingError as e:
                logger.error(f"Embedding generation error for file_id {file_id}: {e}")
                workflow_metrics.metadata["error_type"] = "embedding_error"
                return {"status": "error", "error_type": "embedding_error", "error": str(e)}
            except StorageError as e:
                logger.error(f"Storage error for file_id {file_id}: {e}")
                workflow_metrics.metadata["error_type"] = "storage_error"
                return {"status": "error", "error_type": "storage_error", "error": str(e)}
            except Exception as e:
                logger.error(f"Unexpected error for file_id {file_id}: {e}")
                workflow_metrics.metadata["error_type"] = "unknown_error"
                return {"status": "error", "error_type": "unknown_error", "error": str(e)} 