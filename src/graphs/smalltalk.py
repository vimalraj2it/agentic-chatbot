from langgraph.graph import StateGraph, START, END
from src.graphs.state import AgentState
from src.services.llm_service import get_chat_completion
from src.nodes.shared_nodes import role_injection_node, gruadrail_node, user_profile_node, load_memory_node
from src.models.schemas import SmallTalkResponse
from src.core.logging_config import get_logger

logger = get_logger(__name__)

async def set_active_intent(state: AgentState):
    return {"active_intent": "smalltalk"}

async def smalltalk_llm_node(state: AgentState):
    """Smalltalk Agent LLM node: Structures messages as separate units"""
    logger.info("Node: smalltalk_llm_node")
    
    messages = [
        {"role": "system", "content": state.get("role_rules", "")},
        {"role": "system", "content": state.get("user_profile", "")},
        {"role": "system", "content": state.get("guardrails", "")}
    ]
    
    # Add history and current user message
    messages += state.get("history", [])
    messages.append({"role": "user", "content": state["user_message"]})
    
    # Clean and send
    from src.services.llm_service import clean_messages
    cleaned_messages = clean_messages(messages)
    
    from src.core.config import settings
    try:
        response = await get_chat_completion(
            messages=cleaned_messages, 
            model=settings.SMALLTALK_MODEL,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "smalltalk_response",
                    "schema": SmallTalkResponse.model_json_schema(),
                    "strict": True
                }
            }
        )
        
        content = response.choices[0].message.content
        data = SmallTalkResponse.model_validate_json(content)
        return {"assistant_response": data.message}
    except Exception as e:
        logger.error(f"Error in smalltalk_llm_node: {e}")
        return {"assistant_response": "Hey there! I'm doing a bit of system maintenance at the moment. How can I help you otherwise?"}

# Build Smalltalk Graph
builder = StateGraph(AgentState)
builder.add_node("set_intent", set_active_intent)
builder.add_node("role_injection", role_injection_node)
builder.add_node("gruadrail_node", gruadrail_node)
builder.add_node("user_profile", user_profile_node)
builder.add_node("load_memory", load_memory_node)
builder.add_node("llm", smalltalk_llm_node)

builder.add_edge(START, "set_intent")
builder.add_edge("set_intent", "role_injection")
builder.add_edge("role_injection", "gruadrail_node")
builder.add_edge("gruadrail_node", "user_profile")
builder.add_edge("user_profile", "load_memory")
builder.add_edge("load_memory", "llm")
builder.add_edge("llm", END)

smalltalk_agent_graph = builder.compile()


