from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
from src.services.llm_service import get_chat_completion
from src.services.memory_service import memory_service
from src.core.logging_config import get_logger
from src.core.config import settings

logger = get_logger(__name__)

from src.services.context_builder import context_builder

class AgentState(TypedDict):
    session_id: str
    user_id: str
    user_message: Any # Support multi-modal
    history: List[Dict[str, Any]]
    assistant_response: str
    model: str
    streaming: bool # Added to control flow for stream endpoints
    app_state: Optional[Dict[str, Any]]
    referenced_data: Optional[List[Dict[str, Any]]]
    files: Optional[List[Dict[str, Any]]]

async def load_memory_node(state: AgentState) -> Dict[str, Any]:
    """Retrieves last 5 messages for context"""
    logger.info(f"Node: load_memory_node - Session: {state['session_id']}")
    # Fetch last 5 messages for context
    history = await memory_service.get_history(state["session_id"], limit=5)
    return {"history": history}

async def context_injection_node(state: AgentState) -> Dict[str, Any]:
    """Formats PDF & User profile into prompt"""
    logger.info(f"Node: context_injection_node - User: {state['user_id']}")
    context = await memory_service.get_user_context(state["user_id"])
    user_info = context["user_info"]
    memory = context["memory"]
    
    # Use ContextBuilder to build enriched context
    enriched_context = context_builder.build_combined_context(
        user_info=user_info,
        memory=memory,
        app_state=state.get("app_state"),
        referenced_data=state.get("referenced_data"),
        files=state.get("files")
    )
    
    system_content = f"{settings.SYSTEM_RULES}\n\n"
    system_content += enriched_context
    
    # Role request logic
    if user_info.get("role") in ["User", "Anonymous", ""]:
        system_content += "\nIMPORTANT: The user's specific professional role is unknown. Please specifically ask them what their role or profession is so you can better assist them.\n"
        
    system_msg = {"role": "system", "content": system_content}
    
    # Prepend system msg to history
    return {"history": [system_msg] + state["history"]}

async def call_llm_node(state: AgentState) -> Dict[str, Any]:
    """Generates AI response using LLM"""
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
builder.add_conditional_edges(
    "inject_context", 
    should_continue,
    {
        "call_llm": "call_llm",
        END: END
    }
)
builder.add_edge("call_llm", END)

graph = builder.compile()

# Generate visualization on module load

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
        
        # Add descriptive labels dynamically from node function docstrings
        import re
        node_pattern = re.compile(r"([a-zA-Z0-9_]+)(\(.*?\)|\[.*?\])")
        
        # Extract nodes directly from the graph object to ensure automation
        for node_id, node in graph.get_graph().nodes.items():
            if node_id in ["__start__", "__end__"]:
                continue
                
            # Prioritize the original function over the LangGraph wrapper
            runnable = node.data
            func = getattr(runnable, "func", None)
            
            # If it's a wrapped function, get doc from the original function
            if func:
                docstring = getattr(func, "__doc__", None)
            else:
                docstring = getattr(runnable, "__doc__", None)
            
            # Filter out generic LangGraph docstrings
            if docstring and ("RunnableCallable" in docstring or "RunnableLambda" in docstring):
                docstring = None
            
            if docstring:
                title = node_id.replace("_", " ").title()
                # Clean docstring (strip whitespace and newlines)
                clean_doc = docstring.strip() if docstring else ""
                label = f"<b>{title}</b><br/><i>{clean_doc}</i>"
                
                # Replace definitions in Mermaid content
                title = node_id.replace("_", " ").title()
                # Clean docstring (strip whitespace and newlines)
                clean_doc = docstring.strip() if docstring else ""
                label = f"<b>{title}</b><br/><i>{clean_doc}</i>"
                
                # Very robust replacement: matches node_id followed by any bracket content
                # e.g., load_memory(any_text) -> load_memory("title<br/>desc")
                # We use \b to ensure we match the exact node ID word
                pattern = rf'\b{node_id}([(\[]+)(?:.*?)(([)\]]+))'
                
                # Check if it matches before replacing to provide better debug info
                if re.search(pattern, mermaid_content):
                    logger.info(f"Replacing definition for node: {node_id}")
                    mermaid_content = re.sub(pattern, rf'{node_id}\1"{label}"\2', mermaid_content)
                else:
                    logger.warning(f"Could not find definition for node {node_id} using robust pattern")
                    # Fallback for some mermaid versions that might use different styles
                    mermaid_content = re.sub(rf'\b{node_id}\b', f'{node_id}("{label}")', mermaid_content, count=1)

        # Robust replacements for START/END
        mermaid_content = re.sub(r'__start__([(\[]+)(?:.*?)(([)\]]+))', r'__start__([<b>START</b>])', mermaid_content)
        mermaid_content = re.sub(r'__end__([(\[]+)(?:.*?)(([)\]]+))', r'__end__([<b>END</b>])', mermaid_content)
        
        # Final cleanup for START/END if regex above missed (e.g. if they were already partially replaced)
        if "__start__" in mermaid_content and "<b>START</b>" not in mermaid_content:
            mermaid_content = mermaid_content.replace("__start__", "__start__([<b>START</b>])", 1)
        if "__end__" in mermaid_content and "<b>END</b>" not in mermaid_content:
            mermaid_content = mermaid_content.replace("__end__", "__end__([<b>END</b>])", 1)

        # Debug log: show final structure of a few nodes
        logger.info(f"Final Mermaid sample: {mermaid_content[:1000]}")

        with open(os.path.join(output_dir, "flow.md"), "w") as f:
            f.write(f"```mermaid\n{mermaid_content}\n```")
        logger.info(f"Graph visualization saved as Mermaid: {output_dir}/flow.md")
        
        # 2. Try to save as PNG (Enhanced with labels via mermaid.ink)
        try:
            import base64
            import urllib.request
            
            # Base64 encode the mermaid string for the external rendering service
            encoded_mermaid = base64.b64encode(mermaid_content.encode('utf-8')).decode('utf-8')
            mermaid_ink_url = f"https://mermaid.ink/img/{encoded_mermaid}"
            
            # Set a User-Agent to avoid 403 Forbidden from mermaid.ink
            req = urllib.request.Request(mermaid_ink_url, headers={'User-Agent': 'Mozilla/5.0'})
            
            # Set a timeout for the request
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    with open(os.path.join(output_dir, "flow.png"), "wb") as f:
                        f.write(response.read())
                    logger.info(f"Graph visualization saved as labeled PNG: {output_dir}/flow.png")
                else:
                    raise Exception(f"Mermaid.ink returned status {response.status}")
        
        except Exception as e:
            logger.warning(f"External labeled-PNG generation failed, falling back to default: {e}")
            try:
                # Fallback: Default unlabelled PNG (Requires pygraphviz/graphviz)
                png_bytes = graph.get_graph().draw_mermaid_png()
                with open(os.path.join(output_dir, "flow.png"), "wb") as f:
                    f.write(png_bytes)
                logger.info(f"Graph visualization saved as default PNG: {output_dir}/flow.png")
            except Exception as fe:
                logger.warning(f"Default PNG generation also failed (missing dependencies?): {fe}")

    except Exception as e:
        logger.error(f"Failed to generate graph visualization: {e}")

save_graph_visualization()
