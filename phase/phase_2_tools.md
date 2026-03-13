# Phase 2: Tool Implementations

## Objective
Create all tool functions consumed by agents. Tools are standalone async functions — they are NOT LangChain `Tool` wrappers yet. The agent nodes call them directly.

---

## 2.1 Order Tools

**File**: `src/tools/order_tools.py`

```python
"""
Order management tools — mock implementations.
Replace the in-memory store with real API calls in production.
"""

from typing import List, Dict, Any

# ── Mock order database ────────────────────────────────────────
MOCK_ORDERS: Dict[str, List[Dict[str, Any]]] = {
    "user_001": [
        {"order_id": "ORD-1001", "product": "iPhone 15 Pro", "status": "shipped",
         "estimated_delivery": "2 days", "quantity": 1},
        {"order_id": "ORD-1002", "product": "AirPods Pro", "status": "processing",
         "estimated_delivery": "5 days", "quantity": 2},
    ],
    "user_002": [
        {"order_id": "ORD-2001", "product": "MacBook Air M3", "status": "delivered",
         "estimated_delivery": "delivered", "quantity": 1},
    ],
}


async def list_orders(user_id: str) -> List[Dict[str, Any]]:
    """
    Returns all orders for a user.
    Production: call Order Management REST API.
    """
    return MOCK_ORDERS.get(user_id, [])


async def get_order_status(order_id: str) -> Dict[str, Any]:
    """
    Returns delivery status for a single order.
    Production: call Logistics API.
    """
    for orders in MOCK_ORDERS.values():
        for order in orders:
            if order["order_id"] == order_id:
                return {
                    "order_id": order_id,
                    "product": order["product"],
                    "status": order["status"],
                    "estimated_delivery": order["estimated_delivery"],
                }
    return {"order_id": order_id, "status": "not_found",
            "message": "Order not found"}
```

---

## 2.2 RAG / Knowledge-Base Tools

**File**: `src/tools/rag_tools.py`

```python
"""
Knowledge-base search tool — wraps the existing FAISS / Pinecone retrieval.
"""

from src.services.document_service import document_service


async def search_knowledge_base(query: str, top_k: int = 5) -> str:
    """
    Retrieves the top-K document chunks matching the query.
    Returns formatted context string.
    """
    results = await document_service.search_documents(query, top_k=top_k)
    if not results:
        return "No relevant information found in the knowledge base."

    context = "\n\n".join([
        f"--- {r['filename']} (score: {r['score']:.4f}) ---\n{r['content']}"
        for r in results
    ])
    return context
```

---

## 2.3 MCP Tools (Order Creation)

**File**: `src/tools/mcp_tools.py`

```python
"""
MCP Server tools for order creation workflow.
Mock implementation — replace with MCP REST calls in production.
"""

import uuid
from typing import Dict, Any

# ── In-memory draft store ──────────────────────────────────────
_drafts: Dict[str, Dict[str, Any]] = {}


async def create_draft_order(
    product: str, quantity: int, address: str
) -> Dict[str, Any]:
    """
    Creates a draft order via MCP server.
    Returns the draft with a generated order_id.
    """
    order_id = f"ORD-{uuid.uuid4().hex[:6].upper()}"
    draft = {
        "order_id": order_id,
        "product": product,
        "quantity": quantity,
        "address": address,
        "status": "draft",
    }
    _drafts[order_id] = draft
    return draft


async def confirm_order(order_id: str) -> Dict[str, Any]:
    """
    Confirms a draft order via MCP server.
    Changes status from 'draft' to 'confirmed'.
    """
    draft = _drafts.get(order_id)
    if not draft:
        return {"order_id": order_id, "status": "error",
                "message": "Draft order not found"}

    draft["status"] = "confirmed"
    return {"order_id": order_id, "status": "confirmed",
            "message": "Order confirmed successfully!"}
```

---

## 2.4 Inventory Tools

**File**: `src/tools/inventory_tools.py`

```python
"""
Inventory monitoring tools — background autonomous agent.
"""

from typing import List, Dict, Any

THRESHOLD = 10

MOCK_INVENTORY: List[Dict[str, Any]] = [
    {"sku": "SKU-001", "product": "iPhone 15 Pro", "stock": 5},
    {"sku": "SKU-002", "product": "AirPods Pro", "stock": 50},
    {"sku": "SKU-003", "product": "MacBook Air M3", "stock": 3},
    {"sku": "SKU-004", "product": "iPad Mini", "stock": 25},
]


async def check_inventory() -> List[Dict[str, Any]]:
    """
    Returns items whose stock is below the alert threshold.
    """
    alerts = []
    for item in MOCK_INVENTORY:
        if item["stock"] < THRESHOLD:
            alerts.append({
                **item,
                "alert": True,
                "suggestion": f"Reorder {THRESHOLD - item['stock']} units of {item['product']}",
            })
    return alerts
```

---

## Architecture Notes

- All functions are **plain async** — no LangChain `@tool` decorator. They can be unit-tested independently.
- Agent nodes call them directly: `orders = await list_orders(state["user_id"])`.
- For LangSmith tracing, the decorator is added at the node level, not the tool level.
