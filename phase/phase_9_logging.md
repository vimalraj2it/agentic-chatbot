# Phase 9: Standardized Logging & Observability

## Overview
Phase 9 introduces a project-wide standard for execution tracing. This ensures that every significant operation (AI nodes, tool calls, service methods) is logged with its inputs, outputs, and duration, significantly simplifying debugging and performance monitoring.

## The `@log_execution` Decorator (`src/core/logging_config.py`)

### Features
- **Automatic Tracing**: Logs `START`, `RETURN` (input/output), and `ERROR` events.
- **Timing**: Measures and logs execution duration in seconds.
- **Universal Support**: Works with both synchronous and `async def` functions using intelligent introspection.
- **Module Awareness**: Dynamically uses the logger of the module where the function is defined.

## Mandatory Standards
As documented in `.agent/instructions.md`, all developers (and AI agents) must apply this decorator to:
1. **Graph Nodes**: Every step in a LangGraph workflow.
2. **Tool Handlers**: Any function registered in the `ToolRegistry`.
3. **Core Services**: Key business logic in services like `ConversationStateManager` or `MemoryService`.

## Example Usage
```python
from src.core.logging_config import log_execution

@log_execution
async def my_important_node(state: AgentState):
    # ... logic ...
    return {"result": "success"}
```

## Benefits
- **Traceability**: Follow the exact path of a user request through multiple agents.
- **Bottleneck Detection**: Quickly identify slow-running nodes or tools.
- **Error Context**: See the exact arguments that caused a failure.
