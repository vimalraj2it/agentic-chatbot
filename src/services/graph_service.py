from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, START, END
from src.services.llm_service import get_chat_completion
from src.services.memory_service import memory_service
from src.core.logging_config import get_logger

logger = get_logger(__name__)

from src.core.config import settings

class AgentState(TypedDict):
    session_id: str
    user_id: str
    user_message: Any # Support multi-modal
    history: List[Dict[str, Any]]
    assistant_response: str
    model: str
    streaming: bool # Added to control flow for stream endpoints

async def load_memory_node(state: AgentState) -> Dict[str, Any]:
    logger.info(f"Node: load_memory_node - Session: {state['session_id']}")
    # Fetch last 5 messages for context
    history = await memory_service.get_history(state["session_id"], limit=5)
    return {"history": history}

async def context_injection_node(state: AgentState) -> Dict[str, Any]:
    logger.info(f"Node: context_injection_node - User: {state['user_id']}")
    context = await memory_service.get_user_context(state["user_id"])
    user_info = context["user_info"]
    memory = context["memory"]
    
    system_content = f"{settings.SYSTEM_RULES}\n\n"
    system_content += f"User Context:\n- Name: {user_info['name']}\n- Role: {user_info['role']}\n"
    if memory:
        system_content += f"\nPast Conversation Topics: {', '.join(memory)}\n"
    
    # Role request logic
    if user_info.get("role") in ["User", "Anonymous", ""]:
        system_content += "\nIMPORTANT: The user's specific professional role is unknown. Please specifically ask them what their role or profession is so you can better assist them.\n"
        
    system_msg = {"role": "system", "content": system_content}
    
    # Prepend system msg to history
    return {"history": [system_msg] + state["history"]}

async def call_llm_node(state: AgentState) -> Dict[str, Any]:
    logger.info("Node: call_llm_node")
    messages = state["history"] + [{"role": "user", "content": state["user_message"]}]
    response = await get_chat_completion(messages=messages, model=state.get("model"))
    return {"assistant_response": response.choices[0].message.content}

def should_continue(state: AgentState):
    """
    Conditional edge: if streaming=True, stop after context injection.
    Otherwise, proceed to call the LLM.
    """
    if state.get("streaming"):
        return END
    return "call_llm"

builder = StateGraph(AgentState)
builder.add_node("load_memory", load_memory_node)
builder.add_node("inject_context", context_injection_node)
builder.add_node("call_llm", call_llm_node)

builder.add_edge(START, "load_memory")
builder.add_edge("load_memory", "inject_context")
builder.add_conditional_edges("inject_context", should_continue)
builder.add_edge("call_llm", END)

graph = builder.compile()

def save_graph_visualization(output_dir: str = "graph"):
    """
    Attempts to save the graph visualization to the specified directory.
    Saves both a PNG (if dependencies allow) and a Mermaid markdown file.
    """
    try:
        import os
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # 1. Save as Mermaid Markdown (Always works)
        mermaid_content = graph.get_graph().draw_mermaid()
        with open(os.path.join(output_dir, "flow.md"), "w") as f:
            f.write(f"```mermaid\n{mermaid_content}\n```")
        logger.info(f"Graph visualization saved as Mermaid: {output_dir}/flow.md")
        
        # 2. Try to save as PNG (Requires pygraphviz/graphviz)
        try:
            png_bytes = graph.get_graph().draw_mermaid_png()
            with open(os.path.join(output_dir, "flow.png"), "wb") as f:
                f.write(png_bytes)
            logger.info(f"Graph visualization saved as PNG: {output_dir}/flow.png")
        except Exception as e:
            logger.warning(f"Could not save graph as PNG (missing dependencies?): {e}")

    except Exception as e:
        logger.error(f"Failed to generate graph visualization: {e}")
