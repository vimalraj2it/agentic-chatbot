import os
from typing import List, Dict, Any
from pinecone import Pinecone, ServerlessSpec
from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from src.core.config import settings
from src.core.logging_config import get_logger, log_execution

logger = get_logger(__name__)

@log_execution
class PineconeIndexer:
    def __init__(self):
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index_name = "chat-app-kb"
        self.embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={'device': settings.EMBEDDING_DEVICE},
            encode_kwargs={'normalize_embeddings': settings.EMBEDDING_NORMALIZE}
        )
        
        # Ensure index exists
        if self.index_name not in self.pc.list_indexes().names():
            logger.info(f"Creating Pinecone index: {self.index_name}")
            self.pc.create_index(
                name=self.index_name,
                dimension=384, # bge-small-en dimension
                metric="cosine",
                spec=ServerlessSpec(
                    cloud=settings.PINECONE_CLOUD,
                    region=settings.PINECONE_REGION
                )
            )
        
        self.index = self.pc.Index(self.index_name)

    @log_execution
    def load_documents(self, directory: str) -> List[Any]:
        """Loads documents from a directory."""
        logger.info(f"Loading documents from {directory}")
        loader = DirectoryLoader(
            directory,
            glob="**/*.txt",
            loader_cls=TextLoader
        )
        # Also support PDF if needed
        # loader_pdf = DirectoryLoader(directory, glob="**/*.pdf", loader_cls=PyPDFLoader)
        
        return loader.load()

    @log_execution
    def chunk_documents(self, documents: List[Any]) -> List[Any]:
        """Chunks documents into smaller pieces."""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
        chunks = text_splitter.split_documents(documents)
        logger.info(f"Created {len(chunks)} chunks from {len(documents)} documents")
        return chunks

    @log_execution
    async def index_documents(self, directory: str):
        """Full pipeline: Load -> Chunk -> Embed -> Upload."""
        docs = self.load_documents(directory)
        if not docs:
            logger.warning("No documents found to index.")
            return
            
        chunks = self.chunk_documents(docs)
        
        logger.info(f"Indexing {len(chunks)} chunks to Pinecone...")
        
        # Batching upserts
        batch_size = 100
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            texts = [chunk.page_content for chunk in batch]
            metadatas = [
                {
                    "text": chunk.page_content,
                    "source": chunk.metadata.get("source", "unknown"),
                    "chunk": i + j
                }
                for j, chunk in enumerate(batch)
            ]
            
            embeddings = self.embeddings.embed_documents(texts)
            
            ids = [f"chunk_{i + j}" for j in range(len(batch))]
            
            upserts = [
                (ids[j], embeddings[j], metadatas[j])
                for j in range(len(batch))
            ]
            
            self.index.upsert(vectors=upserts)
            
        logger.info("Indexing complete.")

    @log_execution
    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Searches the Pinecone index for the given query."""
        logger.info(f"Searching Pinecone for: {query}")
        
        # Embed the query
        query_embedding = self.embeddings.embed_query(query)
        
        # Query Pinecone
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        formatted_results = []
        for res in results["matches"]:
            formatted_results.append({
                "content": res["metadata"]["text"],
                "source": res["metadata"].get("source", "unknown"),
                "score": res["score"]
            })
            
        return formatted_results

    @log_execution
    async def index_from_urls(self, urls: List[str]):
        """Scrapes, cleans, and indexes content from a list of URLs."""
        from src.services.scraping_service import scraping_service
        
        logger.info(f"Starting bulk indexing for {len(urls)} URLs")
        
        all_chunks_data = []
        
        for url in urls:
            data = await scraping_service.scrape_and_clean(url)
            if not data or not data.get("content"):
                continue
            
            # Create a virtual "document" for chunking
            from langchain.schema import Document
            
            # Combine title and content for better context
            full_text = f"Title: {data['title']}\nURL: {data['url']}\n\n{data['content']}"
            
            # Also add sections for more granular indexing if content is large
            for section in data.get("sections", []):
                section_text = f"Page: {data['title']}\nSection: {section['title']}\nURL: {data['url']}\n\n{section['content']}"
                all_chunks_data.append(Document(page_content=section_text, metadata={"source": data['url'], "title": data['title'], "section": section['title']}))
            
            if not data.get("sections"):
                all_chunks_data.append(Document(page_content=full_text, metadata={"source": data['url'], "title": data['title']}))

        if not all_chunks_data:
            logger.warning("No content extracted from URLs.")
            return

        chunks = self.chunk_documents(all_chunks_data)
        
        logger.info(f"Indexing {len(chunks)} chunks from URLs to Pinecone...")
        
        # Reuse existing batching logic
        batch_size = 100
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            texts = [chunk.page_content for chunk in batch]
            metadatas = [
                {
                    "text": chunk.page_content,
                    "source": chunk.metadata.get("source", "unknown"),
                    "title": chunk.metadata.get("title", "unknown"),
                    "section": chunk.metadata.get("section", ""),
                    "chunk": i + j
                }
                for j, chunk in enumerate(batch)
            ]
            
            embeddings = self.embeddings.embed_documents(texts)
            import re
            ids = [f"web_{re.sub(r'[^a-zA-Z0-9]', '_', batch[j].metadata.get('source', ''))}_{i + j}" for j in range(len(batch))]
            
            upserts = [(ids[j], embeddings[j], metadatas[j]) for j in range(len(batch))]
            self.index.upsert(vectors=upserts)
            
        logger.info("Web indexing complete.")

# Global instance for easy access
pinecone_service = PineconeIndexer()

async def run_indexing(directory: str = "data/kb"):
    indexer = PineconeIndexer()
    await indexer.index_documents(directory)

if __name__ == "__main__":
    import asyncio
    # Create mock data dir if it doesn't exist
    os.makedirs("data/kb", exist_ok=True)
    asyncio.run(run_indexing())
