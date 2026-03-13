# Smalltalk Agent

Handles casual, non-task-oriented user messages (greetings, jokes, status checks).

## LLM Interaction Sample

**User**: "Tell me a joke"

**Request (via `get_chat_completion`)**:
```json
{
  "messages": [
    {"role": "system", "content": "You are a friendly assistant..."},
    {"role": "user", "content": "Tell me a joke"}
  ],
  "response_format": {
    "type": "json_schema",
    "json_schema": {
      "name": "smalltalk_response",
      "schema": {
        "type": "object",
        "properties": {
          "reply": {"type": "string"},
          "is_joke": {"type": "boolean"}
        }
      }
    }
  }
}
```

**Response**:
```json
{
  "reply": "Why did the robot go on vacation? To recharge its batteries!",
  "is_joke": true
}
```
