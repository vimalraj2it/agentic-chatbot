import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.services.memory_service import memory_service
from src.core.database import db
from src.models.mongodb import UserDoc, SessionDoc
from src.api.router import ChatRequest, chat_endpoint

async def verify_context_injection():
    print("Starting verification of context injection...")
    
    # Initialize DB
    await db.connect_to_storage()
    
    # 1. Setup Mock User
    user_id = "test-user-context-id"
    users_col = db.db["users"]
    await users_col.delete_one({"id": user_id})
    await users_col.insert_one({
        "id": user_id,
        "mobile_number": "1234567890",
        "name": "Vimalraj",
        "role": "Lead Architect"
    })
    
    # 2. Setup Mock Sessions for Memory
    sessions_col = db.db["sessions"]
    await sessions_col.delete_many({"user_id": user_id})
    for i in range(2):
        session = SessionDoc(
            user_id=user_id,
            title=f"Previous Topic {i+1}",
            messages=[]
        )
        await sessions_col.insert_one(session.model_dump())
        
    # 3. Test context retrieval & Graph preparation (Streaming Mode)
    initial_state = {
        "session_id": "any-session",
        "user_id": user_id,
        "user_message": "Hello",
        "model": "gpt-4o-mini",
        "history": [],
        "streaming": True # New flag
    }
    
    print("Invoking graph in streaming mode (context only)...")
    from src.services.graph_service import graph
    result = await graph.ainvoke(initial_state)
    
    # Verify context injection
    history = result.get("history", [])
    system_msg = next((m for m in history if m["role"] == "system"), None)
    
    assert system_msg is not None
    print(f"System Message Found: {system_msg['content'][:100]}...")
    
    # Check if call_llm was skipped (assistant_response should be empty)
    assert not result.get("assistant_response")
    print("Graph correctly interrupted before LLM call for streaming.")

    # 4. Test Role Request Injection (Anonymous user)
    anon_user_id = "anon-user-id"
    await users_col.insert_one({"id": anon_user_id, "mobile_number": "0000", "name": "Anon", "role": "User"})
    
    anon_state = initial_state.copy()
    anon_state["user_id"] = anon_user_id
    
    result_anon = await graph.ainvoke(anon_state)
            
    system_msg_anon = next((m for m in result_anon["history"] if m["role"] == "system"), None)
    assert "specifically ask them what their role" in system_msg_anon['content']
    print("Role request correctly injected for 'User' role using ainvoke!")
    
    print("Verification complete!")

if __name__ == "__main__":
    asyncio.run(verify_context_injection())
