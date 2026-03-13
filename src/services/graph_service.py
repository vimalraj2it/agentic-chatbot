from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, START, END
from src.graphs.state import AgentState
from src.graphs.smalltalk import smalltalk_agent_graph
from src.graphs.faq import faq_agent_graph
from src.graphs.out_of_domain import out_of_domain_agent_graph
from src.graphs.order_status import order_status_agent_graph
from src.graphs.create_order import create_order_agent_graph
from src.nodes.shared_nodes import role_injection_node, gruadrail_node, user_profile_node, load_memory_node
from src.services.prompt_service import prompt_service
from src.services.classifier_service import classifier_service
from src.services.expansion_service import expansion_service
from src.services.conversation_state_manager import conversation_state_manager
from src.services.llm_service import get_chat_completion
from src.core.logging_config import get_logger, log_execution

logger = get_logger(__name__)

@log_execution
async def set_classifier_intent(state: AgentState):
    return {"active_intent": None}

@log_execution
async def check_pending_workflow_node(state: AgentState):
    """Load workflow state from MongoDB to see if we are in the middle of a process."""
    logger.info("Node: check_pending_workflow_node")
    cs = await conversation_state_manager.get(state["session_id"])
    
    if cs.has_active_workflow:
        return {
            "active_intent": cs.current_agent,
            "workflow_state": {
                "agent": cs.current_agent,
                "step": cs.workflow_step,
                "data": cs.agent_data
            }
        }
    
    if cs.is_interrupted:
        return {
            "pending_workflow": {
                "agent": cs.interrupted_from["current_agent"],
                "step": cs.interrupted_from["workflow_step"],
                "data": cs.interrupted_from["agent_data"]
            }
        }
    
    return {}

@log_execution
async def save_interruption_node(state: AgentState):
    """Save active workflow to 'pending' if user interrupted it."""
    logger.info("Node: save_interruption_node")
    await conversation_state_manager.interrupt(state["session_id"])
    return {"pending_workflow": state["workflow_state"], "workflow_state": None}

from src.services.prompt_service import prompt_service

@log_execution
async def resume_node(state: AgentState):
    """Restore the previous workflow after handling an interruption."""
    logger.info("Node: resume_node")
    resumed_agent = await conversation_state_manager.resume(state["session_id"])
    
    # Prepend a resume message to the assistant response
    response = state.get("assistant_response", "")
    pending = state.get("pending_workflow")
    
    resume_msg = prompt_service.render_template(
        "orchestrator_messages.jinja2", 
        type="interruption_resume",
        agent_name=resumed_agent,
        step=pending["step"] if pending else None
    )
    
    return {
        "assistant_response": response + resume_msg,
        "workflow_state": state["pending_workflow"],
        "pending_workflow": None
    }

@log_execution
async def sync_state_node(state: AgentState):
    """Sync graph state back to MongoDB via Manager."""
    logger.info("Node: sync_state_node")
    ws = state.get("workflow_state")
    if ws:
        await conversation_state_manager.update_workflow(
            state["session_id"], ws["agent"], ws["step"], ws["data"]
        )
    else:
        # If no workflow state, clear active but keep interrupted
        cs = await conversation_state_manager.get(state["session_id"])
        if not cs.is_interrupted:
            await conversation_state_manager.clear(state["session_id"])
    return state

@log_execution
async def expansion_agent(state: AgentState):
    """Expands user query for better classification and retrieval"""
    logger.info(f"Node: expansion_agent")
    expanded = await expansion_service.expand_query(
        state["user_message"], 
        history=state.get("history", []),
        user_profile=state.get("user_profile"),
        guardrails=state.get("guardrails")
    )
    return {"expanded_queries": expanded}

@log_execution
async def classifier_agent(state: AgentState) -> Dict[str, Any]:
    """Classifies user intent using structured messages"""
    logger.info(f"Node: classifier_agent")
    
    # Use the highest scored expanded query if available for classification
    classification_message = state["user_message"]
    if state.get("expanded_queries"):
        # The expansion service returns original at index 0, but variations might be better
        # We'll take the first one (which is usually the most refined by the LLM)
        classification_message = state["expanded_queries"][0]["query"]
        logger.info(f"Using expanded query for classification: {classification_message}")

    # Structure messages matching the sample
    messages = [
        {"role": "system", "content": state.get("role_rules", "")},
        {"role": "system", "content": state.get("user_profile", "")},
        {"role": "system", "content": state.get("guardrails", "")}
    ]
    
    # Add history and current message
    messages += state.get("history", [])
    messages.append({"role": "user", "content": classification_message})
    
    # Use classifier service with structured messages directly
    classification = await classifier_service.classify_with_messages(messages)
    return {"classification": classification}

def router_condition(state: AgentState):
    """Routes based on classification intent and workflow state"""
    # 1. If we are in an active workflow, keep going there
    ws = state.get("workflow_state")
    if ws:
        return ws["agent"]

    classification = state.get("classification")
    if not classification:
        return "out_of_domain_agent"
    
    intent = classification.intent
    
    # 2. Check for interruptions: active workflow exists but user asked FAQ/Smalltalk
    # This logic will be handled by the graph edge branching
    
    if intent == "smalltalk":
        return "small_agent"
    elif intent == "faq":
        return "faq_agent"
    elif intent == "order_status":
        return "order_status_agent"
    elif intent == "create_order":
        return "create_order_agent"
    elif intent == "out-of-domain":
        return "out_of_domain_agent"
    else:
        return "out_of_domain_agent"

def post_intent_router(state: AgentState):
    """Determine if we need to resume a workflow after handling an interruption."""
    if state.get("pending_workflow") and not state.get("workflow_state"):
        return "resume"
    return END

# --- Main Orchestrator Graph Construction ---
builder = StateGraph(AgentState)

# Nodes
builder.add_node("set_intent", set_classifier_intent)
builder.add_node("role_injection_node", role_injection_node)
builder.add_node("gruadrail_node", gruadrail_node)
builder.add_node("user_profile_node", user_profile_node)
builder.add_node("load_memory_node", load_memory_node)
builder.add_node("check_workflow", check_pending_workflow_node) # ⭐ Journey Management
builder.add_node("expansion_agent", expansion_agent)
builder.add_node("classifier_agent", classifier_agent)
builder.add_node("save_interruption", save_interruption_node) # ⭐ Journey Management
builder.add_node("resume", resume_node) # ⭐ Journey Management
builder.add_node("sync_state", sync_state_node) # ⭐ Journey Management

# Specialized Intent Subgraphs
builder.add_node("small_agent", smalltalk_agent_graph)
builder.add_node("faq_agent", faq_agent_graph)
builder.add_node("order_status_agent", order_status_agent_graph) # ⭐ NEW
builder.add_node("create_order_agent", create_order_agent_graph) # ⭐ NEW
builder.add_node("out_of_domain_agent", out_of_domain_agent_graph)

# Sequence
builder.add_edge(START, "set_intent")
builder.add_edge("set_intent", "role_injection_node")
builder.add_edge("role_injection_node", "gruadrail_node")
builder.add_edge("gruadrail_node", "user_profile_node")
builder.add_edge("user_profile_node", "load_memory_node")
builder.add_edge("load_memory_node", "check_workflow") # Check workflow before expansion
builder.add_edge("check_workflow", "expansion_agent")
builder.add_edge("expansion_agent", "classifier_agent")

def determine_workflow_interruption(state: AgentState):
    ws = state.get("workflow_state")
    intent = state.get("classification").intent if state.get("classification") else None
    
    # If in a workflow, but user asked FAQ/Smalltalk, it's an interruption
    if ws and intent and intent != ws["agent"] and intent in ["faq", "smalltalk"]:
        return "interrupt"
    return "normal"

# Sub-routing with Interruption Support
builder.add_conditional_edges(
    "classifier_agent",
    determine_workflow_interruption,
    {
        "interrupt": "save_interruption",
        "normal": "router_node" # dummy mapping for router_condition
    }
)

# Dummy node to allow conditional routing after possible interruption save
builder.add_node("router_node", lambda x: x)
builder.add_edge("save_interruption", "router_node")

builder.add_conditional_edges(
    "router_node",
    router_condition,
    {
        "small_agent": "small_agent",
        "faq_agent": "faq_agent",
        "order_status_agent": "order_status_agent",
        "create_order_agent": "create_order_agent",
        "out_of_domain_agent": "out_of_domain_agent"
    }
)

# Completion & Resumption
builder.add_conditional_edges("small_agent", post_intent_router, {"resume": "resume", END: END})
builder.add_conditional_edges("faq_agent", post_intent_router, {"resume": "resume", END: END})

# Agents should save their state when finished or advancing
builder.add_edge("order_status_agent", "sync_state")
builder.add_edge("create_order_agent", "sync_state")
builder.add_edge("sync_state", END)
builder.add_edge("resume", "sync_state")

builder.add_edge("out_of_domain_agent", END)

graph = builder.compile()

from src.utils.graph_viz import save_graph_visualization

# --- Generate All Graph Visualizations (One Place) ---
def generate_all_visualizations():
    """Generates visualizations for the main graph and all sub-agents"""
    logger.info("Generating graph visualizations for all agents...")
    save_graph_visualization(graph, "main")
    save_graph_visualization(smalltalk_agent_graph, "smalltalk")
    save_graph_visualization(faq_agent_graph, "faq")
    save_graph_visualization(order_status_agent_graph, "order_status")
    save_graph_visualization(create_order_agent_graph, "create_order")
    save_graph_visualization(out_of_domain_agent_graph, "out_of_domain")

# Visualizations are now triggered in main.py lifespan
