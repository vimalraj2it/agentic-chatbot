import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.services.graph_service import graph
from src.core.logging_config import setup_logging
from src.core.database import db

async def test_complete_flow():
    print("--- Testing Complete Flow (Split Prompts + Metadata Logging) ---")
    initial_state = {
        "session_id": "test_session_123",
        "user_id": "test_user_456",
        "user_message": "What is the interest rate for 811 Dream Different card?",
        "model": "gpt-4o-mini",
        "streaming": False,
        "app_state": {"platform": "web"},
        "referenced_data": [{"product": "811 card", "status": "active"}],
        "files": None,
        "response_format": None
    }
    
    try:
        print("Connecting to DB...")
        await db.connect_to_storage()
        print("Invoking graph...")
        result = await graph.ainvoke(initial_state)
        print("\n[Assistant Response]:")
        print(result["assistant_response"])
        
        print("\n[Message Structure Check]:")
        # Check if history has at least 4 system messages
        history = result.get("history", [])
        system_msgs = [m for m in history if m["role"] == "system"]
        print(f"Number of system messages: {len(system_msgs)}")
        for idx, m in enumerate(system_msgs):
            print(f"Message {idx+1} Content Start: {m['content'][:50]}...")
            
        assert len(system_msgs) >= 4, f"Expected at least 4 system messages, got {len(system_msgs)}"
        print("✓ Message structure verification successful.")
        
    except Exception as e:
        print(f"✗ Flow test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db.close_storage()

if __name__ == "__main__":
    setup_logging()
    asyncio.run(test_complete_flow())
