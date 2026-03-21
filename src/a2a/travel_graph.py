"""
LangGraph Travel Planner Agent for Agent Chat UI.

This graph exposes a ReAct-style travel planning agent with:
- Gemini LLM for reasoning
- Weather tool (mock data)
- Activity search tool (mock data)

Graph ID: travel_planner
Deployment URL: http://localhost:2024 (via `langgraph dev`)
"""

import os
from typing import Literal
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode

# Load .env from project root
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

# ─── Tools ────────────────────────────────────────────────────────────────────

@tool
def get_weather(location: str) -> dict:
    """Get current weather for a city. Returns temperature, description, and unit."""
    mock_data = {
        "paris": {"temperature": 72, "description": "clear sky", "city": "Paris", "unit": "°F"},
        "london": {"temperature": 61, "description": "overcast clouds", "city": "London", "unit": "°F"},
        "new york": {"temperature": 78, "description": "sunny", "city": "New York", "unit": "°F"},
        "tokyo": {"temperature": 68, "description": "partly cloudy", "city": "Tokyo", "unit": "°F"},
        "sydney": {"temperature": 65, "description": "light rain", "city": "Sydney", "unit": "°F"},
        "dubai": {"temperature": 95, "description": "clear sky", "city": "Dubai", "unit": "°F"},
        "rome": {"temperature": 75, "description": "sunny", "city": "Rome", "unit": "°F"},
    }
    loc_key = location.lower().strip()
    return mock_data.get(loc_key, {
        "temperature": 70,
        "description": "partly cloudy",
        "city": location.title(),
        "unit": "°F"
    })


@tool
def search_activities(query: str, activity_type: str = "general") -> dict:
    """Search for tourist activities and attractions in a city.
    activity_type can be 'outdoor', 'indoor', or 'general'."""
    query_lower = query.lower()
    type_lower = activity_type.lower()

    if "outdoor" in query_lower or "outdoor" in type_lower:
        results = [
            {"title": "Luxembourg Gardens", "description": "A scenic walk through beautiful gardens"},
            {"title": "Tuileries Garden", "description": "Historic garden near the Louvre"},
            {"title": "Seine River Banks", "description": "Bike or walk along the riverside"},
            {"title": "Champ de Mars", "description": "Picnic with Eiffel Tower views"},
            {"title": "Bois de Boulogne", "description": "Large park for hiking and nature"},
        ]
    elif "indoor" in query_lower or "indoor" in type_lower:
        results = [
            {"title": "Louvre Museum", "description": "World's largest art museum"},
            {"title": "Musée d'Orsay", "description": "Impressionist masterpieces collection"},
            {"title": "Centre Pompidou", "description": "Modern and contemporary art"},
            {"title": "Catacombs of Paris", "description": "Underground ossuary exploration"},
            {"title": "Galeries Lafayette", "description": "Iconic Parisian department store"},
        ]
    else:
        results = [
            {"title": "Eiffel Tower", "description": "Iconic Parisian landmark"},
            {"title": "Louvre Museum", "description": "World's largest art museum"},
            {"title": "Montmartre & Sacré-Cœur", "description": "Artistic hilltop neighborhood"},
            {"title": "Seine River Cruise", "description": "Scenic boat tour of Paris"},
            {"title": "Champs-Élysées & Arc de Triomphe", "description": "Famous avenue and monument"},
        ]
    return {"query": query, "type": activity_type, "results": results, "count": len(results)}


# ─── LLM + Tool binding ──────────────────────────────────────────────────────

tools = [get_weather, search_activities]

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
)

model = llm.bind_tools(tools)


# ─── Graph Nodes ──────────────────────────────────────────────────────────────

SYSTEM_PROMPT = (
    "You are a helpful travel planning assistant. "
    "Use the get_weather tool to check weather conditions and "
    "the search_activities tool to find things to do. "
    "When a user asks about traveling somewhere, always check the weather first, "
    "then search for relevant activities based on the weather conditions. "
    "Finally, create a detailed day-by-day travel itinerary. "
    "Be enthusiastic and helpful!"
)


def agent_node(state: MessagesState):
    """Call the LLM with tools bound."""
    from langchain_core.messages import SystemMessage
    messages = state["messages"]
    # Prepend system prompt if not already there
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    response = model.invoke(messages)
    return {"messages": [response]}


def should_continue(state: MessagesState) -> Literal["tools", END]:
    """Decide whether to call tools or finish."""
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END


# ─── Build Graph ──────────────────────────────────────────────────────────────

workflow = StateGraph(MessagesState)

# Add nodes
workflow.add_node("agent", agent_node)
workflow.add_node("tools", ToolNode(tools))

# Set entry point
workflow.add_edge(START, "agent")

# Agent decides: call tools or finish
workflow.add_conditional_edges("agent", should_continue)

# After tools run, go back to agent
workflow.add_edge("tools", "agent")

# Compile the graph — this is what langgraph.json references
graph = workflow.compile()
