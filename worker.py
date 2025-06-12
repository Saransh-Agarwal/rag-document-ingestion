import asyncio
from temporalio.worker import Worker
from temporalio.client import Client
from config import TEMPORAL_ADDRESS
from workflow import IngestDocumentWorkflow
import activities

async def main():
    client = await Client.connect(TEMPORAL_ADDRESS)
    worker = Worker(
        client,
        task_queue="rag-ingest-task-queue",
        workflows=[IngestDocumentWorkflow],
        activities=[
            activities.fetch_document,
            activities.parse_document,
            activities.generate_embeddings,
            activities.store_in_milvus,
        ],
    )
    print("Worker started. Waiting for tasks...")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main()) 