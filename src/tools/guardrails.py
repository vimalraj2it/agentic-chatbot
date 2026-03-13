"""
Tool Guardrails — Pre-invocation validation chain.
"""

from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class GuardrailError(Exception):
    """Raised when a guardrail blocks a tool call."""
    def __init__(self, tool_name: str, reason: str):
        self.tool_name = tool_name
        self.reason = reason
        super().__init__(f"Guardrail blocked '{tool_name}': {reason}")


@dataclass
class GuardrailContext:
    """Context passed to every guardrail check."""
    user_id: str
    session_id: str
    tool_name: str
    params: Dict[str, Any]


GuardrailFn = Callable[[GuardrailContext], None]


# ── Validators ──────────────────────────────────────────────────

def validate_order_id_format(ctx: GuardrailContext):
    order_id = ctx.params.get("order_id", "")
    if order_id and not (order_id.startswith("ORD-") or order_id.startswith("DRAFT-")):
        raise GuardrailError(ctx.tool_name, f"Invalid order ID format: {order_id}")

def validate_positive_quantity(ctx: GuardrailContext):
    qty = ctx.params.get("quantity")
    if qty is not None and (not isinstance(qty, int) or qty <= 0):
        raise GuardrailError(ctx.tool_name, "Quantity must be a positive integer.")

def validate_search_query(ctx: GuardrailContext):
    query = ctx.params.get("query", "")
    if not query or len(query.strip()) < 3:
        raise GuardrailError(ctx.tool_name, "Search query must be at least 3 characters.")


# ── Guardrail Registry ──────────────────────────────────────────

TOOL_GUARDRAILS: Dict[str, List[GuardrailFn]] = {
    "get_order_status": [validate_order_id_format],
    "confirm_order": [validate_order_id_format],
    "create_draft_order": [validate_positive_quantity],
    "search_knowledge_base": [validate_search_query],
}


def run_guardrails(tool_name: str, params: Dict[str, Any], user_id: str, session_id: str) -> Optional[str]:
    """
    Executes guardrails for a tool. Returns error message if blocked, else None.
    """
    guardrails = TOOL_GUARDRAILS.get(tool_name, [])
    ctx = GuardrailContext(user_id=user_id, session_id=session_id, tool_name=tool_name, params=params)

    for guard in guardrails:
        try:
            guard(ctx)
        except GuardrailError as e:
            return e.reason
    return None
