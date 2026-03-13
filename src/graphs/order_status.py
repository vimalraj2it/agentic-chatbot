"""
Order Status Agent — Multi-step workflow for order tracking.
"""

from typing import Dict, Any, List
from langgraph.graph import StateGraph, START, END
from src.graphs.state import AgentState
from src.tools.registry import tool_registry
from src.core.logging_config import get_logger, log_execution
from src.services.prompt_service import prompt_service

logger = get_logger(__name__)


# ── Nodes ──────────────────────────────────────────────────────

@log_execution
async def set_active_intent(state: AgentState):
    """Ensure the orchestrator knows we are in order_status."""
    return {"active_intent": "order_status"}


@log_execution
async def list_orders_node(state: AgentState):
    """Retrieves all orders for the user and presents them as a list."""
    logger.info("Node: list_orders_node")
    orders = await tool_registry.invoke("list_orders", {"user_id": state["user_id"], "session_id": state["session_id"]})
    
    if not orders:
        msg = prompt_service.render_template("order_messages.jinja2", type="not_found")
        return {"assistant_response": msg, "workflow_state": None}
    
    msg = prompt_service.render_template("order_messages.jinja2", type="list", orders=orders)
    
    return {
        "assistant_response": msg,
        "workflow_state": {"agent": "order_status_agent", "step": "awaiting_selection", "data": {"orders": orders}}
    }


@log_execution
async def handle_selection_node(state: AgentState):
    """Processes user response to order selection."""
    logger.info("Node: handle_selection_node")
    user_input = state["user_message"].strip()
    orders = state["workflow_state"]["data"]["orders"]
    
    # Simple number parser
    selected_order = None
    try:
        idx = int(user_input) - 1
        if 0 <= idx < len(orders):
            selected_order = orders[idx]
    except ValueError:
        # Check if they typed the partial or full ID
        for o in orders:
            if user_input.upper() in o["order_id"]:
                selected_order = o
                break

    if not selected_order:
        msg = prompt_service.render_template("order_messages.jinja2", type="selection_error")
        return {
            "assistant_response": msg,
            # keep same workflow state to retry
        }

    status_info = await tool_registry.invoke(
        "get_order_status",
        user_id=state["user_id"],
        session_id=state["session_id"],
        order_id=selected_order["order_id"]
    )
    
    if not status_info:
        msg = prompt_service.render_template("order_messages.jinja2", type="not_found_details")
        return {"assistant_response": msg, "workflow_state": None}

    response = prompt_service.render_template("order_messages.jinja2", type="details", status_info=status_info)
    
    return {
        "assistant_response": response,
        "workflow_state": None # Completed
    }


# ── Routing ────────────────────────────────────────────────────

def route_order_step(state: AgentState):
    """Route based on whether we need selection or status."""
    ws = state.get("workflow_state")
    if not ws:
        return "list_orders"
    
    if ws["step"] == "awaiting_selection":
        return "get_status"
    
    return END


# ── Construction ───────────────────────────────────────────────

builder = StateGraph(AgentState)

builder.add_node("set_intent", set_active_intent)
builder.add_node("list_orders", list_orders_node)
builder.add_node("get_status", handle_selection_node)

builder.add_edge(START, "set_intent")
builder.add_conditional_edges(
    "set_intent",
    route_order_step,
    {
        "list_orders": "list_orders",
        "get_status": "get_status",
        END: END
    }
)
builder.add_edge("list_orders", END)
builder.add_edge("get_status", END)

order_status_agent_graph = builder.compile()
