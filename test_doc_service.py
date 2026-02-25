import asyncio
from src.core.database import db
from src.services.document_service import document_service

async def test():
    await db.connect_to_storage()
    try:
        docs = await document_service.list_documents()
        print(f"Documents found: {len(docs)}")
        for doc in docs:
            print(f"- {doc['filename']}: {doc['status']}")
    finally:
        await db.close_storage()

if __name__ == "__main__":
    asyncio.run(test())
