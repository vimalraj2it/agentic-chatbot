import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.services.prompt_service import prompt_service
from src.services.llm_service import get_chat_completion

async def verify_prompt_service():
    print("--- Verifying PromptService ---")
    context = "User is interested in 811 Dream Different Credit Card."
    guardrails = ["Do not mention interest rates unless asked.", "Keep it under 50 words."]
    
    # 1. Test Regular Markdown Prompt
    system_prompt = prompt_service.build_system_prompt(
        context_string=context,
        guardrails=guardrails,
        output_format="markdown"
    )
    print("\n[Normal Prompt Sample]:")
    print(system_prompt[:200] + "...")
    assert "# ROLE & CORE RULES" in system_prompt
    assert "# CONTEXT & DATA" in system_prompt
    assert "# GUARDRAILS" in system_prompt
    assert "811 Dream Different" in system_prompt
    print("✓ Regular prompt formatting looks correct.")

    # 2. Test JSON Mode Prompt
    json_prompt = prompt_service.build_system_prompt(
        output_format="json"
    )
    print("\n[JSON Prompt Sample]:")
    print(json_prompt[-100:])
    assert "Response MUST be a valid JSON object" in json_prompt
    print("✓ JSON prompt formatting looks correct.")

async def verify_llm_json_mode():
    print("\n--- Verifying LLM JSON Mode ---")
    messages = [
        {"role": "system", "content": "You are a data extractor. Return a JSON object with 'name' and 'age' fields."},
        {"role": "user", "content": "My name is Vimal and I am 30 years old."}
    ]
    
    try:
        response = await get_chat_completion(
            messages=messages,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        print(f"LLM Response: {content}")
        
        import json
        data = json.loads(content)
        assert "name" in data
        assert "age" in data
        print("✓ LLM JSON mode returns valid JSON.")
    except Exception as e:
        print(f"✗ LLM JSON mode failed: {e}")

if __name__ == "__main__":
    asyncio.run(verify_prompt_service())
    # Note: verify_llm_json_mode() requires a running backend/proxy and valid keys
    # asyncio.run(verify_llm_json_mode())
