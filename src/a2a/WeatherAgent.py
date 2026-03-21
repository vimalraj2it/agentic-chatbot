from python_a2a import A2AServer, skill, agent, run_server, TaskStatus, TaskState
import os
import requests
import logging
@agent(
    name="Weather Agent",
    description="Provides weather information",
    version="1.0.0",
    url="https://zzz.example.com"
)
class WeatherAgent(A2AServer):
    
    @skill(
        name="Get Weather",
        description="Get current weather for a location",
        tags=["weather", "forecast"],
        examples="I am a weather agent for getting weather forecast from Open weather"
    )
    def get_weather(self, location):
        """Get weather for a location (mock data for demo)."""
        # Hardcoded mock weather data for demo purposes
        mock_data = {
            "paris": {"temp": 72, "description": "clear sky", "name": "Paris"},
            "london": {"temp": 61, "description": "overcast clouds", "name": "London"},
            "new york": {"temp": 78, "description": "sunny", "name": "New York"},
            "tokyo": {"temp": 68, "description": "partly cloudy", "name": "Tokyo"},
            "sydney": {"temp": 65, "description": "light rain", "name": "Sydney"},
            "dubai": {"temp": 95, "description": "clear sky", "name": "Dubai"},
            "rome": {"temp": 75, "description": "sunny", "name": "Rome"},
        }

        loc_key = location.lower().strip()
        data = mock_data.get(loc_key, {"temp": 70, "description": "partly cloudy", "name": location.title()})

        logging.info(f"Mock weather for {location}: {data}")
        return f"The weather in {data['name']} is {data['description']} with a temperature of {data['temp']}°F."
    
    def handle_task(self, task):
        # Extract location from message
        message_data = task.message or {}
        content = message_data.get("content", {})
        text = content.get("text", "") if isinstance(content, dict) else ""
        
        if "weather" in text.lower() and "in" in text.lower():
            location = text.split("in", 1)[1].strip().rstrip("?.")
            
            # Get weather and create response
            weather_text = self.get_weather(location)
            task.artifacts = [{
                "parts": [{"type": "text", "text": weather_text}]
            }]
            task.status = TaskStatus(state=TaskState.COMPLETED)
        else:
            task.status = TaskStatus(
                state=TaskState.INPUT_REQUIRED,
                message={"role": "agent", "content": {"type": "text", 
                         "text": "Please ask about weather in a specific location."}}
            )
        return task
# Run the server
if __name__ == "__main__":
    agent = WeatherAgent(url="http://localhost:8001", google_a2a_compatible=True)
    run_server(agent, port=8001, debug=True)