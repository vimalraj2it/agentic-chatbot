from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, START, END
from src.services.llm_service import get_chat_completion
from src.services.memory_service import memory_service
from src.core.logging_config import get_logger

logger = get_logger(__name__)

class AgentState(TypedDict):
    session_id: str
    user_message: str
    history: List[Dict[str, str]]
    assistant_response: str
    model: str

async def load_memory_node(state: AgentState) -> Dict[str, Any]:
    logger.info(f"Node: load_memory_node - Session: {state['session_id']}")
    history = await memory_service.get_history(state["session_id"])
    return {"history": history}

async def call_llm_node(state: AgentState) -> Dict[str, Any]:
    logger.info("Node: call_llm_node")
    messages = state["history"] + [{"role": "user", "content": state["user_message"]}]
    response = await get_chat_completion(messages=messages, model=state.get("model"))
    return {"assistant_response": response.choices[0].message.content}

builder = StateGraph(AgentState)
builder.add_node("load_memory", load_memory_node)
builder.add_node("call_llm", call_llm_node)

builder.add_edge(START, "load_memory")
builder.add_edge("load_memory", "call_llm")
builder.add_edge("call_llm", END)

graph = builder.compile()
