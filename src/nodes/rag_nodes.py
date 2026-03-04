from typing import Dict, Any
from src.graphs.state import AgentState
from src.services.prompt_service import prompt_service
from src.services.memory_service import memory_service
from src.services.context_builder import context_builder
from src.services.document_service import document_service
from src.core.logging_config import get_logger

logger = get_logger(__name__)

async def reference_docs_faiss_node(state: AgentState) -> Dict[str, Any]:
    """Retrieves and renders reference documents using FAISS"""
    logger.info(f"Node: reference_docs_faiss_node - User: {state['user_id']}")
    
    # Identify query for retrieval
    query = state["user_message"]
    if state.get("expanded_queries"):
        query = state['expanded_queries'][0]['query']
        logger.info(f"Utilizing Expanded Query for FAISS: {query}")
    
    # Call FAISS search service
    retrieved_results = await document_service.search_documents(query, top_k=5)
    
    # Format retrieved snippets
    faiss_context = ""
    if retrieved_results:
        faiss_context = "\n\n".join([
            f"--- Snippet from {res['filename']} (Score: {res['score']:.4f}) ---\n{res['content']}"
            for res in retrieved_results
        ])
        logger.info(f"Retrieved {len(retrieved_results)} snippets from FAISS")
    else:
        logger.info("No snippets retrieved from FAISS")

    context = await memory_service.get_user_context(state["user_id"])
    
    context_parts = context_builder.build_context_dict(
        user_info=context["user_info"],
        memory=context["memory"],
        app_state=state.get("app_state"),
        referenced_data=state.get("referenced_data"),
        files=state.get("files")
    )
    
    # Render with FAISS context
    # If FAISS context exists, prepend it to the reference documents
    reference_docs = prompt_service.render_template("reference_document.jinja2", **context_parts)
    if faiss_context:
        reference_docs = f"{faiss_context}\n\n# GENERAL CONTEXT\n{reference_docs}"
        
    return {"reference_docs": reference_docs}

async def reference_docs_pinecone_node(state: AgentState) -> Dict[str, Any]:
    """Retrieves and renders reference documents using Pinecone"""
    logger.info(f"Node: reference_docs_pinecone_node - User: {state['user_id']}")
    if state.get("expanded_queries"):
        queries_str = ", ".join([f"'{q['query']}' ({q['score']})" for q in state['expanded_queries']])
        logger.info(f"Utilizing Expanded Queries for Pinecone: {queries_str}")
    
    # Placeholder for Pinecone-specific retrieval logic
    # In a real implementation, you would call a Pinecone search service here
    
    context = await memory_service.get_user_context(state["user_id"])
    
    context_parts = context_builder.build_context_dict(
        user_info=context["user_info"],
        memory=context["memory"],
        app_state=state.get("app_state"),
        referenced_data=state.get("referenced_data"),
        files=state.get("files")
    )
    
    # Render with Pinecone context if needed
    reference_docs = prompt_service.render_template("reference_document.jinja2", **context_parts)
    return {"reference_docs": reference_docs}

async def reference_docs_node(state: AgentState) -> Dict[str, Any]:
    """Retrieves and renders reference documents (default text)"""
    logger.info(f"Node: reference_docs_node - User: {state['user_id']}")
    if state.get("expanded_queries"):
        queries_str = ", ".join([f"'{q['query']}' ({q['score']})" for q in state['expanded_queries']])
        logger.info(f"Utilizing Expanded Queries for Default Text: {queries_str}")
    context = await memory_service.get_user_context(state["user_id"])
    
    context_parts = context_builder.build_context_dict(
        user_info=context["user_info"],
        memory=context["memory"],
        app_state=state.get("app_state"),
        referenced_data=state.get("referenced_data"),
        files=state.get("files")
    )
    
    reference_docs = prompt_service.render_template("reference_document.jinja2", **context_parts)
    return {"reference_docs": reference_docs}
