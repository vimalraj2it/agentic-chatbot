from langgraph.graph import StateGraph, START, END
from src.graphs.state import AgentState
from src.core.logging_config import get_logger

logger = get_logger(__name__)

async def out_of_domain_node(state: AgentState):
    """Out-of-domain Agent: Direct response for unsupported queries"""
    logger.info("Node: out_of_domain_node")
    
    msg = "I'm sorry, but that's outside my current scope or domain. I'm here to assist with project-related questions and general conversation!"
    
    return {"assistant_response": msg}

# Build Out-of-Domain Graph
builder = StateGraph(AgentState)
builder.add_node("out_of_domain_agent", out_of_domain_node)
builder.add_edge(START, "out_of_domain_agent")
builder.add_edge("out_of_domain_agent", END)
out_of_domain_agent_graph = builder.compile()


