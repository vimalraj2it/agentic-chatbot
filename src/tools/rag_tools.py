"""
RAG Tools — Search through the knowledge base.
"""

from typing import List, Dict, Any, Optional
from src.services.document_service import document_service
from src.core.logging_config import get_logger, log_execution

logger = get_logger(__name__)

async def search_knowledge_base(query: str, top_k: int = 3) -> str:
    """
    Search documents for relevant information.
    """
    logger.info(f"Searching knowledge base for: {query}")
    try:
        results = await document_service.search(query, top_k=top_k)
        if not results:
            return "No relevant documents found."
        
        # Format results for the agent
        formatted = []
        for doc in results:
            formatted.append(f"Source: {doc.get('metadata', {}).get('filename', 'Unknown')}\nContent: {doc.get('content')}")
        
        return "\n\n---\n\n".join(formatted)
    except Exception as e:
        logger.error(f"Error searching knowledge base: {e}")
        return f"Error occurred during search: {str(e)}"
@log_execution
async def index_website(base_url: str) -> Dict[str, Any]:
    """
    Discovers URLs from a website's sitemap and indexes them into the RAG system.
    """
    from src.services.scraping_service import scraping_service
    from src.rag.index_documents import pinecone_service
    
    logger.info(f"Triggering website indexing for {base_url}")
    
    urls = await scraping_service.discover_urls(base_url)
    if not urls:
        return {"status": "error", "message": f"No URLs discovered for {base_url}"}
        
    # Trigger background indexing
    await pinecone_service.index_from_urls(urls)
    
    return {
        "status": "success",
        "message": f"Successfully queued indexing for {len(urls)} URLs from {base_url}",
        "url_count": len(urls)
    }
