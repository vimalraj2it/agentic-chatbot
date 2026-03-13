"""
ToolRegistry — Dynamic tool registration and invocation.
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

    async def invoke(self, name: str, user_id: str = "", session_id: str = "", **kwargs) -> Any:
        """
        Invoke a tool by name with keyword arguments.
        Includes guardrail checks and parameter validation.
        """
        from src.tools.guardrails import run_guardrails

        tool = self.get(name)
        if not tool:
            raise ValueError(f"Tool '{name}' is not registered")

        # ── Guardrail check ──────────────────────────────────────────
        # In a real implementation, we'd import TOOL_GUARDRAILS here
        error_msg = run_guardrails(name, kwargs, user_id, session_id)
        if error_msg:
            return {"error": True, "message": error_msg}

        # ── Parameter validation ─────────────────────────────────────
        missing = self.validate_params(name, kwargs)
        if missing:
            raise ValueError(f"Tool '{name}' missing required params: {missing}")

        logger.info(f"Invoking tool: {name} with params: {list(kwargs.keys())}")

        try:
            result = await tool.handler(**kwargs)
            logger.info(f"Tool '{name}' completed successfully")
            return result
        except Exception as e:
            logger.error(f"Tool '{name}' failed: {e}")
            raise


# Singleton instance
tool_registry = ToolRegistry()
