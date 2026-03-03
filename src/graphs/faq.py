from langgraph.graph import StateGraph, START, END
from src.graphs.state import AgentState
from src.services.llm_service import get_chat_completion
from src.nodes.shared_nodes import role_injection_node, gruadrail_node, user_profile_node, load_memory_node
from src.nodes.rag_nodes import reference_docs_faiss_node, reference_docs_pinecone_node, reference_docs_node
from src.core.logging_config import get_logger
from src.core.config import settings
from src.services.llm_service import clean_messages
from src.models.schemas import FAQResponse

logger = get_logger(__name__)

async def set_active_intent(state: AgentState):
    return {"active_intent": "faq"}

async def router_condition_for_reference_docs(state: AgentState):
    rag_type = settings.RAG_TYPE 
    if rag_type == "text":
        return "text"
    elif rag_type == "FAISS": 
        return "Basic_RAG_FAISS"   
    elif rag_type == "Pinecone":
        return "RAG_Pinecone"
    else:
        return "text"
    

async def faq_llm_node(state: AgentState):
    """FAQ Agent LLM node: Structures messages with reference docs"""
    logger.info("Node: faq_llm_node")
    
    messages = [
        {"role": "system", "content": state.get("role_rules", "")},
        {"role": "system", "content": state.get("user_profile", "")},
        {"role": "system", "content": state.get("guardrails", "")},
        {"role": "system", "content": f"# REFERENCE DOCUMENT\n{state.get('reference_docs', '')}"},
        {"role": "system", "content": "# OUTPUT FORMAT\nResponse MUST be a valid JSON object.\nFormat: {\"message\": \"your answer here\", \"score\": 0.9}\nCONFIDENCE SCORE: Must be a float between 0.0 and 1.0."}
    ]
    
    # Add history and current user message
    messages += state.get("history", [])
    
    # Use expanded query if available for better context in generation
    user_msg = state["user_message"]
    if state.get("expanded_queries"):
        user_msg = state["expanded_queries"][0]["query"]
        logger.info(f"Using expanded query for FAQ generation: {user_msg}")
        
    messages.append({"role": "user", "content": user_msg})
    # Clean and send
    cleaned_messages = clean_messages(messages)
    
    try:
        response = await get_chat_completion(
            messages=cleaned_messages, 
            model=settings.FAQ_MODEL,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "faq_response",
                    "schema": FAQResponse.model_json_schema(),
                    "strict": True
                }
            }
        )
        
        content = response.choices[0].message.content
        data = FAQResponse.model_validate_json(content)
        return {"assistant_response": data.message}
    except Exception as e:
        logger.error(f"Error in faq_llm_node: {e}")
        return {"assistant_response": "I'm sorry, I'm having trouble connecting to my knowledge base right now. Please try again in a moment."}

# Build FAQ Graph
builder = StateGraph(AgentState)
builder.add_node("set_intent", set_active_intent)
builder.add_node("role_injection", role_injection_node)
builder.add_node("gruadrail_node", gruadrail_node)
builder.add_node("user_profile", user_profile_node)

builder.add_node("reference_docs", reference_docs_node)
builder.add_node("reference_docs_faiss", reference_docs_faiss_node)
builder.add_node("reference_docs_pinecone", reference_docs_pinecone_node)
builder.add_node("load_memory", load_memory_node)
builder.add_node("llm", faq_llm_node)

builder.add_edge(START, "set_intent")
builder.add_edge("set_intent", "role_injection")
builder.add_edge("role_injection", "gruadrail_node")
builder.add_edge("gruadrail_node", "user_profile")

builder.add_conditional_edges(
    "user_profile",
    router_condition_for_reference_docs,
    {
        "text": "reference_docs",
        "Basic_RAG_FAISS": "reference_docs_faiss",
        "RAG_Pinecone": "reference_docs_pinecone"
    }
)
#builder.add_edge("user_profile", "reference_docs")
builder.add_edge("reference_docs", "load_memory")
builder.add_edge("reference_docs_faiss", "load_memory")
builder.add_edge("reference_docs_pinecone", "load_memory")
builder.add_edge("load_memory", "llm")
builder.add_edge("llm", END)

faq_agent_graph = builder.compile()


