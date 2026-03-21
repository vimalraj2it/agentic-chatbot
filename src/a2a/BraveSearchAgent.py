from python_a2a import A2AServer, skill, agent, run_server, TaskStatus, TaskState
import json
import logging

@agent(
    name="Brave Search Agent",
    description="Performs internet search using Brave Search API",
    version="1.0.0",
    url="https://yourdomain.com"
)
class BraveSearchAgent(A2AServer):
    @skill(
        name="Search Internet",
        description="Perform a web search using Brave Search API",
        tags=["search", "internet", "brave"],
        examples='{"query": "must visit places in Paris", "type": "outdoor"}'
    )
    def search(self, query: str, search_type: str = "general"):
        """Perform search (mock data for demo)."""
        query_lower = query.lower()
        search_type_lower = search_type.lower()

        if "outdoor" in query_lower or "outdoor" in search_type_lower:
            results = [
                {"title": "Luxembourg Gardens", "description": "A scenic walk through beautiful gardens"},
                {"title": "Tuileries Garden", "description": "Historic garden near the Louvre"},
                {"title": "Seine River Banks", "description": "Bike or walk along the riverside"},
                {"title": "Champ de Mars", "description": "Picnic with Eiffel Tower views"},
                {"title": "Bois de Boulogne", "description": "Large park for hiking and nature"},
            ]
        elif "indoor" in query_lower or "indoor" in search_type_lower:
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

        logging.info(f"Mock search for: {query} (type: {search_type})")
        return {"query": query, "type": search_type, "results": results, "count": len(results)}

    def handle_task(self, task):
        message_data = task.message or {}
        content = message_data.get("content", {})
        text = content.get("text", "") if isinstance(content, dict) else ""

        # Try to parse JSON request
        print(f"\n📥 Incoming Request: {text}")
        try:
            request = json.loads(text)
            query = request.get("query", "")
            search_type = request.get("type", "general")
        except (json.JSONDecodeError, TypeError):
            # Fallback: use plain text as query
            query = text.strip()
            search_type = "general"

        if query:
            search_data = self.search(query, search_type)
            response = {
                "status": "success",
                "data": search_data
            }
            print(f"📤 Outgoing Response: {json.dumps(response, indent=2)}")
            task.artifacts = [{
                "parts": [{"type": "text", "text": json.dumps(response)}]
            }]
            task.status = TaskStatus(state=TaskState.COMPLETED)
        else:
            error_response = {
                "status": "error",
                "message": 'Please provide a search query. Example: {"query": "places in Paris", "type": "outdoor"}'
            }
            task.status = TaskStatus(
                state=TaskState.INPUT_REQUIRED,
                message={"role": "agent", "content": {"type": "text", 
                         "text": json.dumps(error_response)}}
            )
        return task

if __name__ == "__main__":
    agent = BraveSearchAgent(url="http://localhost:8002", google_a2a_compatible=True)
    run_server(agent, port=8002, debug=True)