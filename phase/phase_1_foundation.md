# Phase 1: Foundation — State Machine & Configuration

## Objective
Define the LangGraph `AgentState` with all fields needed for multi-agent routing, multi-step workflows, interruptions, and journey resume.

---

## 1.1 AgentState Definition

**File**: `src/graphs/state.py`

```python
from typing import TypedDict, List, Dict, Any, Optional, Annotated
from langgraph.graph import add_messages
from src.models.schemas import QueryClassification


class WorkflowContext(TypedDict, total=False):
    """Tracks position inside a multi-step workflow."""
    agent: str               # e.g. "order_status", "create_order"
    step: str                # current step name inside that agent
    data: Dict[str, Any]     # agent-specific context carried between steps


class AgentState(TypedDict, total=False):
    # ── identity ──
    session_id: str
    user_id: str

    # ── conversation ──
    user_message: Any
    messages: Annotated[list, add_messages]   # full conversation (LangGraph reducer)
    history: List[Dict[str, Any]]             # last N messages loaded from Mongo
    assistant_response: str

    # ── classification ──
    classification: Optional[QueryClassification]
    intent: Optional[str]                     # resolved top intent
    active_intent: Optional[str]              # intent inside a sub-agent

    # ── model / streaming ──
    model: str
    streaming: bool

    # ── prompt injection (existing) ──
    role_rules: Optional[str]
    guardrails: Optional[str]
    user_profile: Optional[str]
    reference_docs: Optional[str]
    expanded_queries: Optional[List[Dict[str, Any]]]
    app_state: Optional[Dict[str, Any]]
    referenced_data: Optional[List[Dict[str, Any]]]
    files: Optional[List[Dict[str, Any]]]

    # ── order workflow ──
    orders: Optional[List[Dict[str, Any]]]       # fetched order list
    selected_order: Optional[str]                 # user-selected order id
    draft_order: Optional[Dict[str, Any]]         # draft being constructed

    # ── journey management ──
    workflow_state: Optional[WorkflowContext]      # current active workflow
    pending_workflow: Optional[WorkflowContext]    # saved workflow on interruption
```

---

## 1.2 New Schemas

**File**: `src/models/schemas.py` — additions only

```python
# ── New intent score names ──
# Add "order_status" and "create_order" to the valid intent names
# used in QueryClassification.intent

class OrderStatusResponse(BaseModel):
    message: str
    orders: Optional[List[Dict[str, Any]]] = None
    status: Optional[str] = None

class CreateOrderResponse(BaseModel):
    message: str
    draft_order: Optional[Dict[str, Any]] = None
    confirmed: bool = False

class DraftOrder(BaseModel):
    order_id: str
    product: str
    quantity: int
    address: str
    status: str = "draft"
```

---

## 1.3 Config Additions

**File**: `src/core/config.py` — additions only

```python
# In class Settings:
ORDER_STATUS_MODEL: str = "gpt-4o-mini"
CREATE_ORDER_MODEL: str = "gpt-4o-mini"
INVENTORY_CHECK_INTERVAL: int = 3600   # seconds

# LangSmith
LANGCHAIN_TRACING_V2: str = "true"
LANGCHAIN_PROJECT: str = "wechat-assistant"
LANGCHAIN_API_KEY: str = ""
```

---

## Architecture Notes

| Field | Purpose |
|---|---|
| `workflow_state` | Tracks the **active** multi-step agent and its current step |
| `pending_workflow` | Saves the active workflow when the user interrupts with an FAQ |
| `orders` / `selected_order` / `draft_order` | Domain data passed between tool calls within agents |

The `WorkflowContext` is persisted to MongoDB by `memory_service.save_workflow_state()` so journeys survive across HTTP requests.
