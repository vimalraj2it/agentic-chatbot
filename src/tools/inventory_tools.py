"""
Inventory Tools — Mock inventory checking.
"""

from typing import List, Dict, Any

MOCK_INVENTORY = {
    "iPhone 15 Pro": 150,
    "AirPods Pro": 12,
    "MacBook M3": 5,
}

LOW_STOCK_THRESHOLD = 10

async def check_inventory() -> List[Dict[str, Any]]:
    """
    Check stock levels and return items below threshold.
    """
    alerts = []
    for item, stock in MOCK_INVENTORY.items():
        if stock < LOW_STOCK_THRESHOLD:
            alerts.append({
                "item": item,
                "current_stock": stock,
                "status": "critical" if stock < 5 else "warning"
            })
    return alerts
