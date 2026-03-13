# Phase 4B: Tool Router & Registry

## Objective
Replace hardcoded tool imports with a dynamic **ToolRegistry** — a single place to register, discover, validate, and invoke all tools. This makes the system extensible without modifying agent code.

---

## Why This Is Needed

**Current approach (hardcoded):**
```python
# Each agent imports tools directly
from src.tools.order_tools import list_orders, get_order_status
```

**Problems:**
- Adding a new tool requires editing agent files
- No visibility into which tools exist
- No validation before invocation
- No logging / tracing at the tool layer

---

## Tool Registry Implementation

**File**: `src/tools/registry.py`

```python
"""
ToolRegistry — Dynamic tool registration and invocation.
─────────────────────────────────────────────────────────────────
All tools register here at startup. Agents discover and invoke
tools through the registry instead of direct imports.
"""

from typing import Callable, Dict, Any, Optional, List
from dataclasses import dataclass, field
from src.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ToolDefinition:
    """Metadata about a registered tool."""
    name: str                                # unique key: "list_orders"
    description: str                         # what it does
    handler: Callable                        # async function to call
    required_params: List[str]               # ["user_id"]
    optional_params: List[str] = field(default_factory=list)
    category: str = "general"                # "order", "rag", "mcp", "inventory"
    requires_auth: bool = False              # needs user ownership check
    rate_limit: Optional[int] = None         # max calls per minute (None = unlimited)


class ToolRegistry:
    """
    Central registry for all tools in the system.
    Provides discovery, validation, and invocation.
    """

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition):
        """Register a tool definition."""
        if tool.name in self._tools:
            logger.warning(f"Tool '{tool.name}' is being re-registered")
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name} [{tool.category}]")

    def get(self, name: str) -> Optional[ToolDefinition]:
        """Get a tool definition by name."""
        return self._tools.get(name)

    def list_tools(self, category: str = None) -> List[ToolDefinition]:
        """List all tools, optionally filtered by category."""
        tools = list(self._tools.values())
        if category:
            tools = [t for t in tools if t.category == category]
        return tools

    def list_names(self, category: str = None) -> List[str]:
        """List tool names for LLM system prompts."""
        return [t.name for t in self.list_tools(category)]

    def validate_params(self, name: str, params: Dict[str, Any]) -> List[str]:
        """
        Validate that required parameters are present.
        Returns list of missing parameter names (empty if valid).
        """
        tool = self.get(name)
        if not tool:
            return [f"Tool '{name}' not found"]

        missing = [p for p in tool.required_params if p not in params]
        return missing

    async def invoke(self, name: str, **kwargs) -> Any:
        """
        Invoke a tool by name with keyword arguments.
        Validates params before calling.
        """
        tool = self.get(name)
        if not tool:
            raise ValueError(f"Tool '{name}' is not registered")

        # Validate required params
        missing = self.validate_params(name, kwargs)
        if missing:
            raise ValueError(
                f"Tool '{name}' missing required params: {missing}"
            )

        logger.info(f"Invoking tool: {name} with params: {list(kwargs.keys())}")

        try:
            result = await tool.handler(**kwargs)
            logger.info(f"Tool '{name}' completed successfully")
            return result
        except Exception as e:
            logger.error(f"Tool '{name}' failed: {e}")
            raise


# ── Global singleton ───────────────────────────────────────────
tool_registry = ToolRegistry()
```

---

## Tool Registration at Startup

**File**: `src/tools/__init__.py`

```python
"""
Auto-register all tools when the tools package is imported.
Called once during FastAPI/Celery startup.
"""

from src.tools.registry import tool_registry, ToolDefinition
from src.tools.order_tools import list_orders, get_order_status
from src.tools.rag_tools import search_knowledge_base
from src.tools.mcp_tools import create_draft_order, confirm_order
from src.tools.inventory_tools import check_inventory


def register_all_tools():
    """Register every tool in the system."""

    # ── Order Tools ────────────────────────────────────────────
    tool_registry.register(ToolDefinition(
        name="list_orders",
        description="List all orders for a user",
        handler=list_orders,
        required_params=["user_id"],
        category="order",
        requires_auth=True,
    ))

    tool_registry.register(ToolDefinition(
        name="get_order_status",
        description="Get delivery status of a specific order",
        handler=get_order_status,
        required_params=["order_id"],
        category="order",
        requires_auth=True,
    ))

    # ── RAG Tools ──────────────────────────────────────────────
    tool_registry.register(ToolDefinition(
        name="search_knowledge_base",
        description="Search the knowledge base for relevant documents",
        handler=search_knowledge_base,
        required_params=["query"],
        optional_params=["top_k"],
        category="rag",
    ))

    # ── MCP Tools ──────────────────────────────────────────────
    tool_registry.register(ToolDefinition(
        name="create_draft_order",
        description="Create a draft order via MCP server",
        handler=create_draft_order,
        required_params=["product", "quantity", "address"],
        category="mcp",
        requires_auth=True,
    ))

    tool_registry.register(ToolDefinition(
        name="confirm_order",
        description="Confirm a draft order via MCP server",
        handler=confirm_order,
        required_params=["order_id"],
        category="mcp",
        requires_auth=True,
    ))

    # ── Inventory Tools ────────────────────────────────────────
    tool_registry.register(ToolDefinition(
        name="check_inventory",
        description="Check stock levels and generate alerts",
        handler=check_inventory,
        required_params=[],
        category="inventory",
    ))


# Auto-register on import
register_all_tools()
```

---

## Agent Usage (Before vs After)

### Before (hardcoded):
```python
from src.tools.order_tools import list_orders

async def list_orders_node(state):
    orders = await list_orders(state["user_id"])
```

### After (via registry):
```python
from src.tools.registry import tool_registry

async def list_orders_node(state):
    orders = await tool_registry.invoke("list_orders", user_id=state["user_id"])
```

**Benefits:**
- Agents only know tool **names**, not implementations
- Adding a new tool = one `register()` call, zero agent changes
- All invocations logged/traced centrally
- Parameter validation happens automatically

---

## Dynamic Tool Discovery for LLM

The registry can generate tool descriptions for the classifier/agent system prompts:

```python
def get_tool_descriptions_for_llm(category: str = None) -> str:
    """Generate a tool summary for LLM system prompts."""
    tools = tool_registry.list_tools(category)
    lines = ["Available tools:"]
    for t in tools:
        params = ", ".join(t.required_params)
        lines.append(f"  - {t.name}({params}): {t.description}")
    return "\n".join(lines)
```
