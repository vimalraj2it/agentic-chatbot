"""
RAG Tools — Search through the knowledge base.
"""

from typing import List, Dict, Any
from src.services.document_service import document_service
from src.core.logging_config import get_logger

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
