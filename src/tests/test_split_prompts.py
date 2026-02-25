import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.services.prompt_service import prompt_service

async def test_prompts():
    print("--- Testing Single String System Prompt ---")
    context = "User is looking for a home loan."
    sys_prompt = prompt_service.build_system_prompt(
        context_string=context,
        output_format="markdown"
    )
    print("✓ Single string prompt generated.")
    assert "ROLE & CORE RULES" in sys_prompt
    assert "User is looking for a home loan." in sys_prompt
    assert "GUARDRAILS & RESPONSE FORMAT" in sys_prompt
    
    print("\n--- Testing Split System Prompt ---")
    context_parts = {
        "user_profile": "Name: John Doe, Role: Professional",
        "reference_document": "Home Loan Terms & Conditions",
        "dynamic_context": "Current interest rate is 7.5%"
    }
    split_prompts = prompt_service.build_split_system_prompt(
        context_parts=context_parts,
        output_format="json"
    )
    
    print(f"✓ Generated {len(split_prompts)} split messages.")
    assert len(split_prompts) == 4
    
    for i, msg in enumerate(split_prompts):
        role = msg["role"]
        content = msg["content"]
        print(f"Message {i+1} ({role}):\n{content[:100]}...")
        
        if i == 0: assert "ROLE & CORE RULES" in content
        if i == 1: assert "John Doe" in content
        if i == 2: 
            assert "GUARDRAILS & RESPONSE FORMAT" in content
            assert "Response MUST be a valid JSON object" in content
        if i == 3: 
            assert "Home Loan Terms" in content
            assert "7.5%" in content

    print("\n✓ Split prompts verification successful!")

if __name__ == "__main__":
    asyncio.run(test_prompts())
