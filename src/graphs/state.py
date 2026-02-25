from typing import TypedDict, List, Dict, Any, Optional
from src.models.schemas import QueryClassification

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
    active_intent: Optional[str]
    # Modular prompt parts
    role_rules: Optional[str]
    guardrails: Optional[str]
    user_profile: Optional[str]
    reference_docs: Optional[str]
