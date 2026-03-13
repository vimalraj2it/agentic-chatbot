"""
Create Order Agent — Guide user through order creation.
"""

from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, START, END
from src.graphs.state import AgentState
from src.tools.registry import tool_registry
from src.core.logging_config import get_logger, log_execution
from src.services.prompt_service import prompt_service

logger = get_logger(__name__)


# ── Nodes ──────────────────────────────────────────────────────

@log_execution
async def set_active_intent(state: AgentState):
    return {"active_intent": "create_order"}


from src.services.llm_service import get_chat_completion
from src.models.schemas import OrderExtraction
from src.core.config import settings

@log_execution
async def collect_info_node(state: AgentState):
    """
    Extracts order details using LLM with structured output.
    """
    logger.info("Node: collect_info_node")
    
    # 1. Build extraction prompt
    prompt = prompt_service.render_template(
        "order_extraction.jinja2", 
        user_message=state["user_message"]
    )
    
    # 2. Call LLM with response_format
    try:
        response = await get_chat_completion(
            messages=[{"role": "user", "content": prompt}],
            model=settings.CLASSIFIER_MODEL,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "order_extraction",
                    "schema": OrderExtraction.model_json_schema(),
                    "strict": True
                }
            }
        )
        
        content = response.choices[0].message.content
        extraction = OrderExtraction.model_validate_json(content)
        logger.info(f"Extracted Order Info: {extraction}")
        
        # 3. Update state based on extraction
        if extraction.is_cancel:
            msg = prompt_service.render_template("create_order_workflow.jinja2", type="cancelled")
            return {"assistant_response": msg, "workflow_state": None}
            
        if extraction.product:
            # If we have a product, proceed to draft creation
            # We skip 'ask_product' and go straight to 'create_draft' (or simulate it here)
            # For simplicity in this graph structure, we'll store the product and let the router decide
            return {
                "workflow_state": {
                    "agent": "create_order_agent", 
                    "step": "awaiting_confirmation", 
                    "data": {"product": extraction.product, "quantity": extraction.quantity}
                }
            }
            
        # If nothing extracted, ask for product
        msg = prompt_service.render_template("create_order_workflow.jinja2", type="ask_product")
        return {
            "assistant_response": msg,
            "workflow_state": {"agent": "create_order_agent", "step": "awaiting_product", "data": {}}
        }
        
    except Exception as e:
        logger.error(f"Error in collect_info_node extraction: {e}")
        msg = prompt_service.render_template("create_order_workflow.jinja2", type="ask_product")
        return {
            "assistant_response": msg,
            "workflow_state": {"agent": "create_order_agent", "step": "awaiting_product", "data": {}}
        }

@log_execution
async def create_draft_node(state: AgentState):
    """Creates a draft order based on user input and asks for confirmation."""
    logger.info("Node: create_draft_node")
    product = state["user_message"].strip()
    
    # Logic to create draft order...
    draft = await tool_registry.invoke("create_draft_order", {"user_id": state["user_id"], "product": product})
    
    msg = prompt_service.render_template("create_order_workflow.jinja2", type="ask_confirmation", product=product)
    
    return {
        "assistant_response": msg,
        "workflow_state": {"agent": "create_order_agent", "step": "awaiting_confirmation", "data": {"product": product, "draft_id": draft["draft_id"]}}
    }

@log_execution
async def finalize_order_node(state: AgentState):
    """Confirm or cancel the order based on user response."""
    logger.info("Node: finalize_order_node")
    user_input = state["user_message"].lower()
    data = state["workflow_state"]["data"]
    
    if any(word in user_input for word in ["yes", "confirm", "ok", "sure", "proceed"]):
        confirmation = await tool_registry.invoke("confirm_order", {"draft_id": data["draft_id"]})
        msg = prompt_service.render_template("create_order_workflow.jinja2", type="success", confirmation_id=confirmation["confirmation_id"])
        return {"assistant_response": msg, "workflow_state": None}
    
    msg = prompt_service.render_template("create_order_workflow.jinja2", type="cancelled")
    return {"assistant_response": msg, "workflow_state": None}


# ── Routing ────────────────────────────────────────────────────

def route_create_step(state: AgentState):
    ws = state.get("workflow_state")
    if not ws:
        return "collect_info"
    
    if ws["step"] == "collecting_info":
        return "collect_info" # loop to collect if needed
    
    if ws["step"] == "awaiting_confirmation":
        return "confirm"
    
    return END


# ── Construction ───────────────────────────────────────────────

builder = StateGraph(AgentState)

builder.add_node("set_intent", set_active_intent)
builder.add_node("collect_info", collect_info_node)
builder.add_node("create_draft", create_draft_node)
builder.add_node("confirm", finalize_order_node)

builder.add_edge(START, "set_intent")
builder.add_conditional_edges(
    "set_intent",
    route_create_step,
    {
        "collect_info": "collect_info",
        "confirm": "confirm",
        END: END
    }
)
builder.add_edge("collect_info", END)
builder.add_edge("confirm", END)

create_order_agent_graph = builder.compile()
