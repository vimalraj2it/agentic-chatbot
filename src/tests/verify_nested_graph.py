import asyncio
from src.services.graph_service import graph
from src.models.schemas import QueryClassification

async def test_small_routing():
    print("\n--- Testing Smalltalk Routing (Small Agent) ---")
    state = {
        "session_id": "test_session",
        "user_id": "test_user",
        "user_message": "Hello, how are you?",
        "history": [],
        "model": None,
        "streaming": False,
        "app_state": None,
        "referenced_data": None,
        "files": None
    }
    
    result = await graph.ainvoke(state)
    print(f"User Message: {state['user_message']}")
    print(f"Classification: {result.get('classification')}")
    print(f"Active Intent: {result.get('active_intent')}")
    print(f"Response: {result.get('assistant_response')}")
    
    classification = result.get("classification")
    assert classification is not None
    assert classification.intent == "smalltalk"
    assert result.get("active_intent") == "smalltalk"
    assert result.get("role_rules") is not None
    assert result.get("guardrails") is not None
    assert "assistant_response" in result

async def test_faq_routing():
    print("\n--- Testing FAQ Routing (FAQ Agent) ---")
    state = {
        "session_id": "test_session_faq",
        "user_id": "test_user",
        "user_message": "What is Phase 4?",
        "history": [],
        "model": None,
        "streaming": False,
        "app_state": None,
        "referenced_data": None,
        "files": None
    }
    
    result = await graph.ainvoke(state)
    print(f"User Message: {state['user_message']}")
    print(f"Classification: {result.get('classification')}")
    print(f"Active Intent: {result.get('active_intent')}")
    print(f"Response: {result.get('assistant_response')}")
    
    classification = result.get("classification")
    assert classification.intent == "faq"
    assert result.get("active_intent") == "faq"
    assert result.get("role_rules") is not None
    assert result.get("guardrails") is not None
    assert "assistant_response" in result

async def test_out_of_domain_routing():
    print("\n--- Testing Out-of-Domain Routing ---")
    state = {
        "session_id": "test_session_ood",
        "user_id": "test_user",
        "user_message": "How do I bake a lasagna?",
        "history": [],
        "model": None,
        "streaming": False,
        "app_state": None,
        "referenced_data": None,
        "files": None
    }
    
    result = await graph.ainvoke(state)
    print(f"User Message: {state['user_message']}")
    print(f"Classification: {result.get('classification')}")
    print(f"Active Intent: {result.get('active_intent')}")
    print(f"Response: {result.get('assistant_response')}")
    
    # Out-of-domain agent might not update active_intent or role_rules as it's a direct response node
    assert result.get("classification") is not None
    assert "outside my current scope" in result.get("assistant_response")

from src.core.database import db

async def run_tests():
    print("--- Initializing Database ---")
    await db.connect_to_storage()
    try:
        await test_small_routing()
        await test_faq_routing()
        await test_out_of_domain_routing()
    finally:
        await db.close_storage()

if __name__ == "__main__":
    asyncio.run(run_tests())
