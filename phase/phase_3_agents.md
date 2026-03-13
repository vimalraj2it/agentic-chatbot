# Phase 3: Agent Implementations

## Objective
Implement the three new agents as LangGraph sub-graphs: OrderStatusAgent, CreateOrderAgent, and InventoryMonitorAgent.

---

## 3.1 OrderStatusAgent

**File**: `src/graphs/order_status.py`

```python
"""
OrderStatusAgent — Agentic AI
Multi-step order lookup:
  Step 1: list_orders → present numbered list → save workflow_state
  Step 2: user selects order → get_order_status → return status
"""

from langgraph.graph import StateGraph, START, END
from src.graphs.state import AgentState
from src.tools.order_tools import list_orders, get_order_status
from src.services.llm_service import get_chat_completion, clean_messages
from src.core.config import settings
from src.core.logging_config import get_logger

logger = get_logger(__name__)


async def set_active_intent(state: AgentState):
    return {"active_intent": "order_status"}


async def list_orders_node(state: AgentState):
    """
    Calls list_orders tool and formats a numbered selection list.
    Saves workflow_state so the orchestrator knows we are mid-flow.
    """
    logger.info("Node: list_orders_node")
    user_id = state["user_id"]
    orders = await list_orders(user_id)

    if not orders:
        return {
            "assistant_response": "You don't have any orders yet.",
            "orders": [],
            "workflow_state": None,  # nothing to resume
        }

    # Format numbered list
    lines = ["Here are your orders:\n"]
    for idx, o in enumerate(orders, 1):
        lines.append(f"{idx}. {o['product']} (ID: {o['order_id']})")
    lines.append("\nPlease select an order number to check its status.")
    message = "\n".join(lines)

    return {
        "assistant_response": message,
        "orders": orders,
        "workflow_state": {
            "agent": "order_status",
            "step": "awaiting_selection",
            "data": {"orders": orders},
        },
    }


async def get_status_node(state: AgentState):
    """
    Called after user selects an order.
    Resolves user input to an order_id and fetches status.
    """
    logger.info("Node: get_status_node")
    user_input = state["user_message"]
    orders = state.get("orders") or []

    # ── Resolve selection ──────────────────────────────────────
    selected_order_id = None

    # Try numeric index first ("1", "2", ...)
    try:
        idx = int(user_input.strip()) - 1
        if 0 <= idx < len(orders):
            selected_order_id = orders[idx]["order_id"]
    except ValueError:
        pass

    # Try matching by order_id or product name
    if not selected_order_id:
        for o in orders:
            if (user_input.strip().upper() in o["order_id"].upper()
                    or user_input.strip().lower() in o["product"].lower()):
                selected_order_id = o["order_id"]
                break

    if not selected_order_id:
        return {
            "assistant_response": "I couldn't identify that order. "
                                  "Please reply with the order number (1, 2, …).",
            # keep workflow_state so we can retry
        }

    # ── Fetch status ───────────────────────────────────────────
    status = await get_order_status(selected_order_id)

    message = (
        f"📦 **Order {status['order_id']}** — {status.get('product', '')}\n"
        f"Status: **{status['status']}**\n"
        f"Estimated delivery: **{status['estimated_delivery']}**"
    )

    return {
        "assistant_response": message,
        "selected_order": selected_order_id,
        "workflow_state": None,   # workflow complete
    }


# ── Graph construction ─────────────────────────────────────────
builder = StateGraph(AgentState)
builder.add_node("set_intent", set_active_intent)
builder.add_node("list_orders", list_orders_node)
builder.add_node("get_status", get_status_node)


def route_order_step(state: AgentState):
    """If we already have orders (mid-flow), jump straight to get_status."""
    ws = state.get("workflow_state")
    if ws and ws.get("step") == "awaiting_selection":
        return "get_status"
    return "list_orders"


builder.add_edge(START, "set_intent")
builder.add_conditional_edges(
    "set_intent",
    route_order_step,
    {"list_orders": "list_orders", "get_status": "get_status"},
)
builder.add_edge("list_orders", END)
builder.add_edge("get_status", END)

order_status_agent_graph = builder.compile()
```

---

## 3.2 CreateOrderAgent

**File**: `src/graphs/create_order.py`

```python
"""
CreateOrderAgent — Deep Agent
Multi-step guided order creation:
  Step 1: collect product, quantity, address via LLM
  Step 2: create_draft_order tool
  Step 3: ask user to confirm
  Step 4: confirm_order tool
"""

from langgraph.graph import StateGraph, START, END
from src.graphs.state import AgentState
from src.tools.mcp_tools import create_draft_order, confirm_order
from src.services.llm_service import get_chat_completion, clean_messages
from src.core.config import settings
from src.core.logging_config import get_logger

logger = get_logger(__name__)


async def set_active_intent(state: AgentState):
    return {"active_intent": "create_order"}


async def collect_info_node(state: AgentState):
    """
    Uses LLM to extract product, quantity, and address from
    the conversation. If info is incomplete, asks follow-up.
    """
    logger.info("Node: collect_info_node")
    ws = state.get("workflow_state") or {}
    collected = ws.get("data", {})

    messages = [
        {"role": "system", "content": (
            "You are an order assistant. Extract the following from the user's "
            "messages: product, quantity, shipping_address.\n"
            "If any field is missing, ask the user for it.\n"
            "Respond in JSON: "
            '{"product": "...", "quantity": N, "address": "...", '
            '"complete": true/false, "follow_up": "question if incomplete"}'
        )},
    ]
    messages += state.get("history", [])
    messages.append({"role": "user", "content": state["user_message"]})

    response = await get_chat_completion(
        messages=clean_messages(messages),
        model=settings.CREATE_ORDER_MODEL,
    )
    import json
    content = response.choices[0].message.content
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        data = {"complete": False,
                "follow_up": "Could you tell me the product, quantity, "
                              "and shipping address?"}

    if data.get("complete"):
        # All info collected — move to draft creation
        draft = await create_draft_order(
            product=data["product"],
            quantity=data["quantity"],
            address=data["address"],
        )
        msg = (
            f"Here is your draft order:\n\n"
            f"🆔 Order ID: **{draft['order_id']}**\n"
            f"📦 Product: {draft['product']}\n"
            f"🔢 Quantity: {draft['quantity']}\n"
            f"📍 Address: {draft['address']}\n\n"
            f"Would you like to **confirm** this order?"
        )
        return {
            "assistant_response": msg,
            "draft_order": draft,
            "workflow_state": {
                "agent": "create_order",
                "step": "awaiting_confirmation",
                "data": draft,
            },
        }
    else:
        return {
            "assistant_response": data.get("follow_up",
                "Please provide the product, quantity, and address."),
            "workflow_state": {
                "agent": "create_order",
                "step": "collecting_info",
                "data": collected,
            },
        }


async def confirm_node(state: AgentState):
    """
    Handles user confirmation of the draft order.
    """
    logger.info("Node: confirm_node")
    user_input = state["user_message"].strip().lower()
    draft = state.get("draft_order") or {}

    if user_input in ("yes", "confirm", "y", "ok", "sure"):
        result = await confirm_order(draft.get("order_id", ""))
        return {
            "assistant_response": (
                f"✅ {result['message']}\n"
                f"Your order **{result['order_id']}** has been placed!"
            ),
            "workflow_state": None,  # workflow complete
        }
    elif user_input in ("no", "cancel", "n"):
        return {
            "assistant_response": "Order cancelled. Let me know if you need anything else!",
            "draft_order": None,
            "workflow_state": None,
        }
    else:
        return {
            "assistant_response": "Please reply **yes** to confirm or **no** to cancel.",
            # keep workflow_state as-is
        }


# ── Graph construction ─────────────────────────────────────────
def route_create_step(state: AgentState):
    ws = state.get("workflow_state")
    if ws and ws.get("step") == "awaiting_confirmation":
        return "confirm"
    return "collect_info"


builder = StateGraph(AgentState)
builder.add_node("set_intent", set_active_intent)
builder.add_node("collect_info", collect_info_node)
builder.add_node("confirm", confirm_node)

builder.add_edge(START, "set_intent")
builder.add_conditional_edges(
    "set_intent",
    route_create_step,
    {"collect_info": "collect_info", "confirm": "confirm"},
)
builder.add_edge("collect_info", END)
builder.add_edge("confirm", END)

create_order_agent_graph = builder.compile()
```

---

## 3.3 InventoryMonitorAgent

**File**: `src/graphs/inventory_monitor.py`

```python
"""
InventoryMonitorAgent — Autonomous Agent
Runs as a Celery Beat periodic task every hour.
Checks stock levels and logs alerts.
"""

from src.tools.inventory_tools import check_inventory
from src.core.logging_config import get_logger
import asyncio

logger = get_logger(__name__)


async def run_inventory_check():
    """
    Core logic — called by the Celery task wrapper.
    """
    alerts = await check_inventory()

    if not alerts:
        logger.info("InventoryMonitor: All stock levels are healthy.")
        return {"status": "ok", "alerts": []}

    for alert in alerts:
        logger.warning(
            f"⚠️  LOW STOCK: {alert['product']} "
            f"(SKU: {alert['sku']}) — {alert['stock']} units remaining. "
            f"Suggestion: {alert['suggestion']}"
        )

    # In production: persist alerts to MongoDB, send notifications, etc.
    return {"status": "alerts", "alerts": alerts}


# ── Celery task (synchronous wrapper) ──────────────────────────
def inventory_monitor_task():
    """
    Sync entry point called by Celery Beat.
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(run_inventory_check())
    finally:
        loop.close()
```

---

## Architecture Notes

- **OrderStatusAgent** and **CreateOrderAgent** are `StateGraph` sub-graphs compiled and mounted into the main orchestrator as nodes.
- **InventoryMonitorAgent** is NOT a LangGraph graph — it's a standalone async function invoked by Celery Beat. It doesn't participate in the conversation flow.
- Multi-step agents use `workflow_state` to track position. Each invocation checks `workflow_state.step` to decide which node to execute — this means the graph is re-entered with different routing on each user turn.
