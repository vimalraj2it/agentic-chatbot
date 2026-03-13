"""
Auto-register all tools when the tools package is imported.
"""

from src.tools.registry import tool_registry, ToolDefinition
from src.tools.order_tools import list_orders, get_order_status
from src.tools.rag_tools import search_knowledge_base
from src.tools.mcp_tools import create_draft_order, confirm_order
from src.tools.inventory_tools import check_inventory

def register_all_tools():
    """Register every tool in the system."""

    tool_registry.register(ToolDefinition(
        name="list_orders",
        description="List all orders for a user",
        handler=list_orders,
        required_params=["user_id"],
        category="order",
        requires_auth=True
    ))

    tool_registry.register(ToolDefinition(
        name="get_order_status",
        description="Get status of a specific order",
        handler=get_order_status,
        required_params=["order_id"],
        category="order",
        requires_auth=True
    ))

    tool_registry.register(ToolDefinition(
        name="search_knowledge_base",
        description="Search documentation for information",
        handler=search_knowledge_base,
        required_params=["query"],
        category="rag"
    ))

    tool_registry.register(ToolDefinition(
        name="create_draft_order",
        description="Create a draft order",
        handler=create_draft_order,
        required_params=["product", "quantity", "address"],
        category="mcp",
        requires_auth=True
    ))

    tool_registry.register(ToolDefinition(
        name="confirm_order",
        description="Confirm a draft order",
        handler=confirm_order,
        required_params=["order_id"],
        category="mcp",
        requires_auth=True
    ))

    tool_registry.register(ToolDefinition(
        name="check_inventory",
        description="Check stock levels",
        handler=check_inventory,
        required_params=[],
        category="inventory"
    ))

# Register on import
register_all_tools()
