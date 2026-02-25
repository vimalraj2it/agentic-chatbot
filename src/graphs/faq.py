from langgraph.graph import StateGraph, START, END
from src.graphs.state import AgentState
from src.services.llm_service import get_chat_completion
from src.nodes.shared_nodes import role_injection_node, gruadrail_node, user_profile_node, reference_docs_node, load_memory_node
from src.core.logging_config import get_logger

logger = get_logger(__name__)

async def set_active_intent(state: AgentState):
    return {"active_intent": "faq"}

async def faq_llm_node(state: AgentState):
    """FAQ Agent LLM node: Structures messages with reference docs"""
    logger.info("Node: faq_llm_node")
    
    messages = [
        {"role": "system", "content": state.get("role_rules", "")},
        {"role": "system", "content": state.get("user_profile", "")},
        {"role": "system", "content": state.get("guardrails", "")},
        {"role": "system", "content": f"# REFERENCE DOCUMENT\n{state.get('reference_docs', '')}"}
    ]
    
    # Add history and current user message
    messages += state.get("history", [])
    messages.append({"role": "user", "content": state["user_message"]})
    
    # Clean and send
    from src.services.llm_service import clean_messages
    cleaned_messages = clean_messages(messages)
    
    from src.core.config import settings
    response = await get_chat_completion(messages=cleaned_messages, model=settings.FAQ_MODEL)
    content = response.choices[0].message.content
    return {"assistant_response": content}

# Build FAQ Graph
builder = StateGraph(AgentState)
builder.add_node("set_intent", set_active_intent)
builder.add_node("role_injection", role_injection_node)
builder.add_node("gruadrail_node", gruadrail_node)
builder.add_node("user_profile", user_profile_node)
builder.add_node("reference_docs", reference_docs_node)
builder.add_node("load_memory", load_memory_node)
builder.add_node("llm", faq_llm_node)

builder.add_edge(START, "set_intent")
builder.add_edge("set_intent", "role_injection")
builder.add_edge("role_injection", "gruadrail_node")
builder.add_edge("gruadrail_node", "user_profile")
builder.add_edge("user_profile", "reference_docs")
builder.add_edge("reference_docs", "load_memory")
builder.add_edge("load_memory", "llm")
builder.add_edge("llm", END)

faq_agent_graph = builder.compile()


