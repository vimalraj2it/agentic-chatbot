from typing import TypedDict, List, Dict, Any, Optional
from src.models.schemas import QueryClassification

class WorkflowContext(TypedDict):
    agent: str      # "order_status", "create_order", etc.
    step: str       # "awaiting_selection", "collecting_info", etc.
    data: Dict[str, Any] # stored parameters for the current step

class AgentState(TypedDict):
    session_id: str
    user_id: str
    user_message: Any # Support multi-modal
    history: List[Dict[str, Any]]
    assistant_response: str
    model: str
    streaming: bool # Added to control flow for stream endpoints
    app_state: Optional[Dict[str, Any]]
    referenced_data: Optional[List[Dict[str, Any]]]
    files: Optional[List[Dict[str, Any]]]
    classification: Optional[QueryClassification]
    
    # ── Workflow State ─────────────────────────────────────────
    intent: Optional[str] # Top level intent
    active_intent: Optional[str] # Current active sub-graph
    orders: Optional[List[Dict[str, Any]]] # List of orders for selection
    selected_order: Optional[str] # Selected order ID
    draft_order: Optional[Dict[str, Any]] # Working order data
    workflow_state: Optional[WorkflowContext] # Current active workflow position
    pending_workflow: Optional[WorkflowContext] # Interrupted workflow to resume

    # ── Modular prompt parts ───────────────────────────────────
    role_rules: Optional[str]
    guardrails: Optional[str]
    user_profile: Optional[str]
    reference_docs: Optional[str]
    expanded_queries: Optional[List[Dict[str, Any]]]
