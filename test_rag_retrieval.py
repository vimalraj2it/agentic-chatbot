import asyncio
import os
from src.core.database import db
from src.services.document_service import document_service
from src.core.logging_config import get_logger

logger = get_logger(__name__)

async def verify_rag():
    # 1. Initialize DB connection
    await db.connect_to_storage()
    
    try:
        # 2. List and sync documents
        print("\n--- Syncing Documents ---")
        docs = await document_service.list_documents()
        test_doc = None
        for d in docs:
            print(f"Found: {d['filename']} - Status: {d['status']}")
            if "kotak" in d['filename'].lower():
                test_doc = d
        
        if not test_doc:
            print("ERROR: cc_kotak_cards.pdf not found in reference-file/")
            return

        # 3. Load document into FAISS if needed
        save_path = os.path.join(document_service.index_dir, f"{test_doc['id']}.faiss")
        index_missing = not os.path.exists(save_path) or not os.listdir(save_path)
        
        if test_doc['status'] != 'loaded' or index_missing:
            print(f"\n--- Loading {test_doc['filename']} into FAISS (Force={index_missing}) ---")
            await document_service.load_document(test_doc['id'])
        else:
            print(f"\n--- {test_doc['filename']} is already loaded ---")

        # 4. Perform Search
        query = "What are the features of Kotak credit cards?"
        print(f"\n--- Searching FAISS for: '{query}' ---")
        results = await document_service.search_documents(query, top_k=3)
        
        if not results:
            print("No results found.")
        else:
            for i, res in enumerate(results):
                print(f"\nResult {i+1} (Score: {res['score']:.4f}):")
                print(f"Source: {res['filename']}")
                print(f"Content: {res['content'][:200]}...")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        await db.close_storage()

if __name__ == "__main__":
    asyncio.run(verify_rag())
