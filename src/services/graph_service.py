from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, START, END
from src.graphs.state import AgentState
from src.graphs.smalltalk import smalltalk_agent_graph
from src.graphs.faq import faq_agent_graph
from src.graphs.out_of_domain import out_of_domain_agent_graph
from src.nodes.shared_nodes import role_injection_node, gruadrail_node, user_profile_node, load_memory_node
from src.services.classifier_service import classifier_service
from src.services.llm_service import get_chat_completion
from src.core.logging_config import get_logger

logger = get_logger(__name__)

async def set_classifier_intent(state: AgentState):
    return {"active_intent": None}

async def classifier_agent(state: AgentState) -> Dict[str, Any]:
    """Classifies user intent using structured messages"""
    logger.info(f"Node: classifier_agent")
    
    # Structure messages matching the sample
    messages = [
        {"role": "system", "content": state.get("role_rules", "")},
        {"role": "system", "content": state.get("user_profile", "")},
        {"role": "system", "content": state.get("guardrails", "")}
    ]
    
    # Add history and current message
    messages += state.get("history", [])
    messages.append({"role": "user", "content": state["user_message"]})
    
    # Use classifier service with structured messages directly
    classification = await classifier_service.classify_with_messages(messages)
    return {"classification": classification}

def router_condition(state: AgentState):
    """Routes based on classification intent"""
    classification = state.get("classification")
    if not classification:
        return "out_of_domain_agent"
    
    intent = classification.intent
    if intent == "smalltalk":
        return "small_agent"
    elif intent == "faq":
        return "faq_agent"
    elif intent == "out-of-domain":
        return "out_of_domain_agent"
    else:
        return "out_of_domain_agent"

# --- Main Orchestrator Graph Construction ---
builder = StateGraph(AgentState)

# Nodes
builder.add_node("set_intent", set_classifier_intent)
builder.add_node("role_injection_node", role_injection_node)
builder.add_node("gruadrail_node", gruadrail_node)
builder.add_node("user_profile_node", user_profile_node)
builder.add_node("load_memory_node", load_memory_node)
builder.add_node("classifier_agent", classifier_agent)

# Specialized Intent Subgraphs
builder.add_node("small_agent", smalltalk_agent_graph)
builder.add_node("faq_agent", faq_agent_graph)
builder.add_node("out_of_domain_agent", out_of_domain_agent_graph)

# Sequence: Start -> Intent -> Role -> Gruadrail -> Profile -> Memory -> Classifier
builder.add_edge(START, "set_intent")
builder.add_edge("set_intent", "role_injection_node")
builder.add_edge("role_injection_node", "gruadrail_node")
builder.add_edge("gruadrail_node", "user_profile_node")
builder.add_edge("user_profile_node", "load_memory_node")
builder.add_edge("load_memory_node", "classifier_agent")

# Conditional Branching
builder.add_conditional_edges(
    "classifier_agent",
    router_condition,
    {
        "small_agent": "small_agent",
        "faq_agent": "faq_agent",
        "out_of_domain_agent": "out_of_domain_agent"
    }
)

# Completion
builder.add_edge("small_agent", END)
builder.add_edge("faq_agent", END)
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
    save_graph_visualization(out_of_domain_agent_graph, "out_of_domain")

# Visualizations are now triggered in main.py lifespan
