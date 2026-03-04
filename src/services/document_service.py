import os
import shutil
from typing import List, Dict, Optional
from datetime import datetime
from uuid import uuid4
from fastapi import UploadFile
from src.core.database import db
from src.core.config import settings
from src.core.logging_config import get_logger
from src.models.mongodb import DocumentDoc

# FAISS and LangChain imports
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = get_logger(__name__)

class DocumentService:
    def __init__(self):
        self.base_dir = "reference-file"
        self.index_dir = "vector_store"
        os.makedirs(self.base_dir, exist_ok=True)
        os.makedirs(self.index_dir, exist_ok=True)
        
        # Use BGE-small-en for embeddings as requested, now from config
        self.embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={'device': settings.EMBEDDING_DEVICE},
            encode_kwargs={'normalize_embeddings': settings.EMBEDDING_NORMALIZE}
        )
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        self._indices = {} # Cache for loaded indices: {doc_id: vector_store}

    @property
    def docs_col(self):
        if db.db is None:
            logger.warning("Database not initialized, returning placeholder or error might occur")
            # In a real app, db.connect_to_storage() is called on startup.
            # If we approach here during tests, we might need to handle it.
            raise RuntimeError("Database not initialized. Ensure connect_to_storage() was called.")
        return db.db["documents"]

    async def list_documents(self) -> List[Dict]:
        """Lists all documents from MongoDB and syncs with disk"""
        logger.info("Listing and syncing documents")
        
        # Ensure directories exist
        os.makedirs(self.base_dir, exist_ok=True)
        
        # Get files from disk
        disk_files = {f for f in os.listdir(self.base_dir) if f.endswith(".pdf")}
        
        # Get documents from DB
        db_docs = await self.docs_col.find({}).to_list(length=1000)
        db_filenames = {doc["filename"] for doc in db_docs}
        
        # Add missing files to DB
        for filename in disk_files - db_filenames:
            doc = DocumentDoc(
                filename=filename,
                file_path=os.path.join(self.base_dir, filename),
                status="unloaded"
            )
            await self.docs_col.insert_one(doc.model_dump())
        
        # Re-fetch after sync
        return await self.docs_col.find({}).to_list(length=1000)

    async def upload_document(self, file: UploadFile) -> str:
        """Saves a file to disk and registers it in MongoDB"""
        logger.info(f"Uploading document: {file.filename}")
        file_path = os.path.join(self.base_dir, file.filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        doc = DocumentDoc(
            filename=file.filename,
            file_path=file_path,
            status="unloaded"
        )
        await self.docs_col.update_one(
            {"filename": file.filename},
            {"$set": doc.model_dump()},
            upsert=True
        )
        # Fetch back for ID if upserted
        res = await self.docs_col.find_one({"filename": file.filename})
        return res["id"]

    async def load_document(self, doc_id: str):
        """Indexes a document in FAISS"""
        logger.info(f"Loading document into FAISS: {doc_id}")
        doc = await self.docs_col.find_one({"id": doc_id})
        if not doc:
            raise ValueError("Document not found")

        await self.docs_col.update_one({"id": doc_id}, {"$set": {"status": "loading"}})
        
        try:
            loader = PyPDFLoader(doc["file_path"])
            pages = loader.load()
            texts = self.text_splitter.split_documents(pages)
            
            # Create FAISS index for this specific document
            vector_store = FAISS.from_documents(texts, self.embeddings)
            save_path = os.path.join(self.index_dir, f"{doc_id}.faiss")
            vector_store.save_local(save_path)
            
            await self.docs_col.update_one(
                {"id": doc_id},
                {"$set": {"status": "loaded", "updated_at": datetime.utcnow()}}
            )
        except Exception as e:
            logger.error(f"Error loading document: {e}")
            await self.docs_col.update_one({"id": doc_id}, {"$set": {"status": "error"}})
            raise

    async def unload_document(self, doc_id: str):
        """Removes a document's FAISS index"""
        logger.info(f"Unloading document from FAISS: {doc_id}")
        save_path = os.path.join(self.index_dir, f"{doc_id}.faiss")
        
        if os.path.exists(save_path):
            if os.path.isdir(save_path):
                shutil.rmtree(save_path)
            else:
                os.remove(save_path)
            
        await self.docs_col.update_one(
            {"id": doc_id},
            {"$set": {"status": "unloaded", "updated_at": datetime.utcnow()}}
        )

    async def delete_document(self, doc_id: str):
        """Deletes document from FAISS, DB, and disk"""
        logger.info(f"Deleting document: {doc_id}")
        doc = await self.docs_col.find_one({"id": doc_id})
        if not doc:
            return

        # 1. Unload from FAISS
        await self.unload_document(doc_id)
        
        # 2. Delete from disk
        if os.path.exists(doc["file_path"]):
            os.remove(doc["file_path"])
            
        # 3. Delete from DB
        await self.docs_col.delete_one({"id": doc_id})
        
        # 4. Remove from cache
        if doc_id in self._indices:
            del self._indices[doc_id]

    async def search_documents(self, query: str, top_k: int = 5) -> List[Dict]:
        """Searches across all loaded documents and returns top snippets"""
        logger.info(f"Searching FAISS for: {query}")
        
        # Get all loaded documents
        loaded_docs = await self.docs_col.find({"status": "loaded"}).to_list(length=100)
        if not loaded_docs:
            logger.warning("No documents loaded in FAISS")
            return []
            
        all_results = []
        
        for doc in loaded_docs:
            doc_id = doc["id"]
            filename = doc["filename"]
            
            # Load index from cache or disk
            if doc_id not in self._indices:
                save_path = os.path.join(self.index_dir, f"{doc_id}.faiss")
                if os.path.exists(save_path):
                    try:
                        self._indices[doc_id] = FAISS.load_local(
                            save_path, 
                            self.embeddings, 
                            allow_dangerous_deserialization=True
                        )
                    except Exception as e:
                        logger.error(f"Error loading index for {filename}: {e}")
                        continue
                else:
                    logger.warning(f"Index file missing for loaded document: {filename}")
                    continue
            
            # Search in this document's index
            vector_store = self._indices[doc_id]
            results_with_scores = vector_store.similarity_search_with_score(query, k=top_k)
            
            for doc_snippet, score in results_with_scores:
                all_results.append({
                    "content": doc_snippet.page_content,
                    "metadata": doc_snippet.metadata,
                    "score": float(score),
                    "filename": filename
                })
        
        # Sort by score (lower is better for L2 distance, but FAISS by default usually returns scores where smaller is more similar)
        # LangChain's similarity_search_with_score returns (doc, score)
        # Sort so most relevant are at the top
        all_results.sort(key=lambda x: x["score"])
        
        return all_results[:top_k]

document_service = DocumentService()
