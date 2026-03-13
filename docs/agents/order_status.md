# Order Status Agent

A deterministic agent for real-time tracking of order fulfillment.

## Component: Tool Access
Unlike the Create Order agent, this agent primarily relies on the `get_order_status` tool with strict guardrails.

## Sample Interaction

**User**: "Where is ORD-9988?"

**Tool Call**:
```json
{
  "tool_name": "get_order_status",
  "parameters": {"order_id": "ORD-9988"}
}
```

**Guardrail Check**:
- Verified order ID format (`ORD-XXXX`).
- Verified user ownership of the order.

**Response**:
```json
{
  "status": "delivered",
  "history": [
    {"timestamp": "2024-03-01", "event": "shipped"},
    {"timestamp": "2024-03-03", "event": "delivered"}
  ]
}
```
