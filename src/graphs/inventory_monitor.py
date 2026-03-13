"""
Inventory Monitor — Background task for scheduled checks.
"""

from src.tools.registry import tool_registry
from src.core.logging_config import get_logger

logger = get_logger(__name__)

async def run_inventory_check():
    """
    Logic for the monitor agent.
    """
    logger.info("Running scheduled inventory check...")
    
    alerts = await tool_registry.invoke("check_inventory")
    
    if not alerts:
        logger.info("Inventory check passed: No low-stock items.")
        return
    
    for alert in alerts:
        status = alert["status"].upper()
        logger.warning(
            f"[{status}] Low stock alert: {alert['item']} — "
            f"Stock level: {alert['current_stock']}"
        )
    
    return alerts


def inventory_monitor_task():
    """
    Synchronous wrapper for Celery beat.
    """
    import asyncio
    return asyncio.run(run_inventory_check())
