# Create Order Agent

A stateful, multi-turn agent for collecting product details and drafting orders.

## Workflow Logic
1. **Extraction**: Uses LLM to extract `product` and `quantity` from user messages.
2. **Context Preservation**: If info is missing, it prompts the user and saves state to MongoDB.
3. **Interruption Support**: If a user asks a side-question, state is saved as `pending_workflow`.

## Structured Extraction Sample

**User**: "I need 3 watches"

**LLM Response (Structured)**:
```json
{
  "product": "watches",
  "quantity": 3,
  "confirm": null,
  "is_cancel": false
}
```

**Tool Invocation (Draft Creation)**:
```python
# A2A Communication
await tool_registry.invoke("create_draft_order", product="watches", qty=3)
```
