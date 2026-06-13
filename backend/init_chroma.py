import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.chroma_client import chroma_service
from app.utils.document_ingestion import DocumentIngestion, get_default_policies


async def init_chroma():
    print("Initializing ChromaDB...")

    # Ingest default policies
    policies = get_default_policies()

    for policy in policies:
        print(f"Ingesting policy: {policy['title']}")
        chunks = []
        metadatas = []
        ids = []

        # Simple chunking by sections
        sections = policy["content"].split("\n## ")
        for i, section in enumerate(sections):
            if section.strip():
                chunks.append(section.strip())
                metadatas.append({
                    "document_id": policy["id"],
                    "title": policy["title"],
                    "header": section.split("\n")[0].strip() if "\n" in section else "General",
                    "doc_type": "policy",
                    "chunk_index": i,
                })
                ids.append(f"{policy['id']}_chunk_{i}")

        if chunks:
            chroma_service.add_documents(
                collection_name="policies",
                documents=chunks,
                metadatas=metadatas,
                ids=ids,
            )
            print(f"  Added {len(chunks)} chunks")

    print("\nChromaDB initialized successfully!")
    print(f"Collections: {chroma_service.list_collections()}")


if __name__ == "__main__":
    asyncio.run(init_chroma())
