"""
Order Tools — Mock implementations for listing and getting status.
"""

from typing import List, Dict, Any, Optional

# ── Mock Data ──────────────────────────────────────────────────
MOCK_ORDERS = {
    "user_123": [
        {"order_id": "ORD-1001", "product": "iPhone 15 Pro", "status": "shipped", "eta": "2 days"},
        {"order_id": "ORD-1002", "product": "AirPods Pro", "status": "processing", "eta": "5 days"},
    ]
}


async def list_orders(user_id: str) -> List[Dict[str, Any]]:
    """
    List all orders for a specific user.
    """
    return MOCK_ORDERS.get(user_id, [])


async def get_order_status(order_id: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed status for a specific order.
    """
    # Search through all user orders for simplicity in mock
    for user_orders in MOCK_ORDERS.values():
        for order in user_orders:
            if order["order_id"] == order_id:
                return order
    return None
