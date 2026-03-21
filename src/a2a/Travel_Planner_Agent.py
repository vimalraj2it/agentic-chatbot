from langchain_google_genai import ChatGoogleGenerativeAI
import asyncio
import json
import os
from python_a2a import AgentNetwork
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

async def main():
    # Create an agent network
    network = AgentNetwork(name="Travel Assistant Network")
    # Add agents to the network
    network.add("weather", "http://localhost:8001")
    network.add("search", "http://localhost:8002")
    # List all available agents
    print("\nAvailable Agents:")
    for agent_info in network.list_agents():
        print(f"- {agent_info['name']}: {agent_info['description']}")

    # Create Gemini LLM client directly
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GEMINI_API_KEY"),
    )

    params = {
        "destination": "Paris",
        "travel_dates": "June 21-25"
    }
    
    # --- Step 1: Get weather via JSON request ---
    weather_request = json.dumps({"location": params["destination"]})
    weather_agent = network.get_agent("weather")
    weather_raw = weather_agent.ask(weather_request)

    try:
        weather_response = json.loads(weather_raw)
        weather_data = weather_response.get("data", {})
        print(f"\n🌤 Weather Response (JSON):")
        print(json.dumps(weather_response, indent=2))
    except json.JSONDecodeError:
        weather_data = {"city": params["destination"], "description": weather_raw}
        print(f"\nWeather (text): {weather_raw}")

    # --- Step 2: Get search results via JSON request ---
    activity_type = "outdoor" if any(
        kw in weather_data.get("description", "").lower() 
        for kw in ["sunny", "clear"]
    ) else "indoor"

    search_request = json.dumps({
        "query": f"Recommend {activity_type} activities in {params['destination']}",
        "type": activity_type
    })
    search_agent = network.get_agent("search")
    search_raw = search_agent.ask(search_request)

    try:
        search_response = json.loads(search_raw)
        search_data = search_response.get("data", {})
        print(f"\n🔍 Search Response (JSON):")
        print(json.dumps(search_response, indent=2))
    except json.JSONDecodeError:
        search_data = {"results": [{"title": search_raw}]}
        print(f"\nSearch (text): {search_raw}")

    # --- Step 3: Summarize with Gemini ---
    activities_list = "\n".join(
        [f"- {r['title']}: {r.get('description', '')}" for r in search_data.get("results", [])]
    )
    
    prompt = (
        f"You are a travel assistant. Plan a trip to {params['destination']} "
        f"for {params['travel_dates']}.\n\n"
        f"Weather: {weather_data.get('description', 'unknown')} at "
        f"{weather_data.get('temperature', 'N/A')}{weather_data.get('unit', '°F')}\n\n"
        f"Recommended activities:\n{activities_list}\n\n"
        f"Suggest a day-by-day itinerary with must-see attractions."
    )
    print(f"\n📝 Prompt to Gemini:\n{prompt}\n")

    llm_result = llm.invoke(prompt)
    print(f"\n✈️ Travel Plan:\n{llm_result.content}")

if __name__ == "__main__":
    asyncio.run(main())