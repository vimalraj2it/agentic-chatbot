"""
Conversation State Manager — Handles persistent workflow state and lifecycle.
"""

import time
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from src.core.database import db
from src.core.logging_config import get_logger

logger = get_logger(__name__)

# TTL for stale workflows (15 minutes)
WORKFLOW_TTL_SECONDS = 900

class ConversationState(BaseModel):
    """Data model for a conversation's active/pending workflow."""
    session_id: str
    current_agent: Optional[str] = None    # "order_status", "create_order"
    workflow_step: Optional[str] = None    # "awaiting_selection", "confirm"
    agent_data: Dict[str, Any] = Field(default_factory=dict)
    
    # Interruption tracking
    interrupted_from: Optional[Dict[str, Any]] = None # stores previous state when pausing
    
    last_updated: float = Field(default_factory=time.time)

    @property
    def has_active_workflow(self) -> bool:
        return self.current_agent is not None

    @property
    def is_interrupted(self) -> bool:
        return self.interrupted_from is not None

    @property
    def is_expired(self) -> bool:
        return (time.time() - self.last_updated) > WORKFLOW_TTL_SECONDS


class ConversationStateManager:
    """
    Manages loading, saving, and transitioning conversation states in MongoDB.
    """

    def __init__(self):
        self.collection = db.get_collection("conversation_states")

    async def get(self, session_id: str) -> ConversationState:
        """Fetch state for a session. Returns empty state if none exists or expired."""
        doc = await self.collection.find_one({"session_id": session_id})
        
        if not doc:
            return ConversationState(session_id=session_id)
        
        state = ConversationState(**doc)
        
        if state.is_expired and state.has_active_workflow:
            logger.info(f"Workflow for {session_id} expired. Clearing.")
            await self.clear(session_id)
            return ConversationState(session_id=session_id)
            
        return state

    async def save(self, state: ConversationState):
        """Persist state to database."""
        state.last_updated = time.time()
        await self.collection.update_one(
            {"session_id": state.session_id},
            {"$set": state.model_dump()},
            upsert=True
        )

    async def clear(self, session_id: str):
        """Wipe state completely."""
        await self.collection.delete_one({"session_id": session_id})

    async def interrupt(self, session_id: str):
        """
        Pause current workflow and move it to 'interrupted_from'.
        Used when user asks an out-of-flow question (like FAQ).
        """
        state = await self.get(session_id)
        if not state.has_active_workflow:
            return
            
        logger.info(f"Interrupting workflow {state.current_agent} for {session_id}")
        state.interrupted_from = {
            "current_agent": state.current_agent,
            "workflow_step": state.workflow_step,
            "agent_data": state.agent_data
        }
        state.current_agent = None
        state.workflow_step = None
        state.agent_data = {}
        await self.save(state)

    async def resume(self, session_id: str) -> Optional[str]:
        """
        Restore a previously interrupted workflow.
        Returns the name of the agent resumed.
        """
        state = await self.get(session_id)
        if not state.is_interrupted:
            return None
            
        logger.info(f"Resuming workflow for {session_id}")
        prev = state.interrupted_from
        state.current_agent = prev["current_agent"]
        state.workflow_step = prev["workflow_step"]
        state.agent_data = prev["agent_data"]
        state.interrupted_from = None
        
        await self.save(state)
        return state.current_agent

    # ── Workflow Control ──────────────────────────────────────────

    async def update_workflow(self, session_id: str, agent: str, step: str, data: Dict[str, Any]):
        """Advance a workflow to a new step."""
        state = await self.get(session_id)
        state.current_agent = agent
        state.workflow_step = step
        state.agent_data = data
        await self.save(state)

# Singleton
conversation_state_manager = ConversationStateManager()
