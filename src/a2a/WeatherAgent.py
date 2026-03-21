from python_a2a import A2AServer, skill, agent, run_server, TaskStatus, TaskState
import json
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
        examples='{"location": "Paris"}'
    )
    def get_weather(self, location):
        """Get weather for a location (mock data for demo)."""
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
        data = mock_data.get(loc_key, {
            "temperature": 70,
            "description": "partly cloudy",
            "city": location.title(),
            "unit": "°F"
        })

        logging.info(f"Mock weather for {location}: {data}")
        return data
    
    def handle_task(self, task):
        message_data = task.message or {}
        content = message_data.get("content", {})
        text = content.get("text", "") if isinstance(content, dict) else ""
        
        # Try to parse JSON request
        print(f"\n📥 Incoming Request: {text}")
        try:
            request = json.loads(text)
            location = request.get("location", "")
        except (json.JSONDecodeError, TypeError):
            # Fallback: extract location from plain text
            if "in" in text.lower():
                location = text.split("in", 1)[1].strip().rstrip("?.")
            else:
                location = text.strip()
        
        if location:
            weather_data = self.get_weather(location)
            response = {
                "status": "success",
                "data": weather_data
            }
            print(f"📤 Outgoing Response: {json.dumps(response, indent=2)}")
            task.artifacts = [{
                "parts": [{"type": "text", "text": json.dumps(response)}]
            }]
            task.status = TaskStatus(state=TaskState.COMPLETED)
        else:
            error_response = {
                "status": "error",
                "message": "Please provide a location. Example: {\"location\": \"Paris\"}"
            }
            task.status = TaskStatus(
                state=TaskState.INPUT_REQUIRED,
                message={"role": "agent", "content": {"type": "text", 
                         "text": json.dumps(error_response)}}
            )
        return task

# Run the server
if __name__ == "__main__":
    agent = WeatherAgent(url="http://localhost:8001", google_a2a_compatible=True)
    run_server(agent, port=8001, debug=True)