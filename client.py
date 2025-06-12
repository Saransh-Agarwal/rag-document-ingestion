import argparse
import asyncio
from temporalio.client import Client
from config import TEMPORAL_ADDRESS

async def main(file_id: str, url: str):
    client = await Client.connect(TEMPORAL_ADDRESS)
    handle = await client.start_workflow(
        "workflow.IngestDocumentWorkflow.run",
        file_id,
        url,
        id=f"ingest-{file_id}",
        task_queue="rag-ingest-task-queue",
    )
    print(f"Started workflow {handle.id} (run_id={handle.run_id})")
    result = await handle.result()
    print("Workflow result:", result)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trigger RAG Ingest Workflow")
    parser.add_argument("--file_id", required=True, help="Unique file ID")
    parser.add_argument("--url", required=True, help="File URL")
    args = parser.parse_args()
    asyncio.run(main(args.file_id, args.url)) 