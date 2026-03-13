"""
MCP Tools — Mock implementations for draft creation and confirmation.
"""

import uuid
from typing import Dict, Any, Optional

# In-memory store for draft orders during session
_drafts = {}

async def create_draft_order(product: str, quantity: int, address: str) -> Dict[str, Any]:
    """
    Create a draft order. Returns the draft details with a generated ID.
    """
    order_id = f"DRAFT-{uuid.uuid4().hex[:6].upper()}"
    draft = {
        "order_id": order_id,
        "product": product,
        "quantity": quantity,
        "address": address,
        "status": "draft",
        "total_price": quantity * 999.0  # Mock pricing
    }
    _drafts[order_id] = draft
    return draft

async def confirm_order(order_id: str) -> Dict[str, Any]:
    """
    Confirm a previously created draft order.
    """
    if order_id not in _drafts:
        return {"error": True, "message": f"Draft order {order_id} not found."}
    
    draft = _drafts[order_id]
    draft["status"] = "confirmed"
    draft["confirmation_id"] = f"CONF-{uuid.uuid4().hex[:8].upper()}"
    return draft
