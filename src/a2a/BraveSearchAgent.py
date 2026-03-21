from python_a2a import A2AServer, skill, agent, run_server, TaskStatus, TaskState
import os
import requests
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
        examples="Search 'must visit places in utah in may'"
    )
    def search(self, query: str):
        """Perform search (mock data for demo)."""
        # Hardcoded mock search results for demo purposes
        query_lower = query.lower()

        if "outdoor" in query_lower or "park" in query_lower:
            results = [
                "Visit the Luxembourg Gardens for a scenic walk",
                "Explore Tuileries Garden near the Louvre",
                "Bike along the Seine River banks",
                "Picnic at Champ de Mars with Eiffel Tower views",
                "Hike in Bois de Boulogne park",
            ]
        elif "indoor" in query_lower or "museum" in query_lower:
            results = [
                "Tour the Louvre Museum — world's largest art museum",
                "Visit Musée d'Orsay for Impressionist masterpieces",
                "Explore Centre Pompidou for modern art",
                "Discover the Catacombs of Paris underground",
                "Enjoy shopping at Galeries Lafayette",
            ]
        else:
            results = [
                "Visit the Eiffel Tower — iconic landmark",
                "Explore the Louvre Museum",
                "Walk through Montmartre and visit Sacré-Cœur",
                "Take a Seine River cruise",
                "Stroll the Champs-Élysées to the Arc de Triomphe",
            ]

        logging.info(f"Mock search for: {query}")
        summary = "\n".join([f"- {r}" for r in results])
        return f"Top recommendations for '{query}':\n{summary}"
    def handle_task(self, task):
        message_data = task.message or {}
        content = message_data.get("content", {})
        text = content.get("text", "") if isinstance(content, dict) else ""
        if text.strip():
            query = text.strip()
            result = self.search(query)
            task.artifacts = [{
                "parts": [{"type": "text", "text": result}]
            }]
            task.status = TaskStatus(state=TaskState.COMPLETED)
        else:
            task.status = TaskStatus(
                state=TaskState.INPUT_REQUIRED,
                message={"role": "agent", "content": {"type": "text", 
                         "text": "Please provide a search query."}}
            )
        return task
if __name__ == "__main__":
    agent = BraveSearchAgent(url="http://localhost:8002",google_a2a_compatible=True)
    run_server(agent, port=8002, debug=True)