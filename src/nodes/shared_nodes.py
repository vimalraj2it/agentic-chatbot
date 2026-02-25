from typing import Dict, Any, Optional
from src.graphs.state import AgentState
from src.services.prompt_service import prompt_service
from src.services.memory_service import memory_service
from src.services.context_builder import context_builder
from src.core.logging_config import get_logger

logger = get_logger(__name__)

async def role_injection_node(state: AgentState) -> Dict[str, Any]:
    """Injects role based on intent"""
    intent = state.get("active_intent")
    logger.info(f"Node: role_injection_node - Intent: {intent}")
    
    # Map intents to templates (None/No intent defaults to classifier)
    template_map = {
        "smalltalk": "role_smalltalk.jinja2",
        "faq": "role_faq.jinja2",
        "classifier": "role_classifier.jinja2"
    }
    template = template_map.get(intent) if intent else "role_classifier.jinja2"
    logger.info(f"Node: role_injection_node - Selected Template: {template}")
    
    role_rules = prompt_service.render_template(template)
    logger.info(f"Node: role_injection_node - Role Rules Preview: {role_rules[:50]}...")
    return {"role_rules": role_rules}

async def gruadrail_node(state: AgentState) -> Dict[str, Any]:
    """Injects guardrails based on intent"""
    intent = state.get("active_intent")
    logger.info(f"Node: gruadrail_node - Intent: {intent}")
    
    # For now, using shared guardrails, but can be intent-specific
    guardrails = prompt_service.render_template("guardrails_default.jinja2")
    return {"guardrails": guardrails}

async def user_profile_node(state: AgentState) -> Dict[str, Any]:
    """Retrieves and renders user profile"""
    logger.info(f"Node: user_profile_node - User: {state['user_id']}")
    context = await memory_service.get_user_context(state["user_id"])
    
    context_parts = context_builder.build_context_dict(
        user_info=context["user_info"],
        memory=context["memory"]
    )
    
    user_profile = prompt_service.render_template("user_profile.jinja2", **context_parts)
    return {"user_profile": user_profile}

async def reference_docs_node(state: AgentState) -> Dict[str, Any]:
    """Retrieves and renders reference documents"""
    logger.info(f"Node: reference_docs_node - User: {state['user_id']}")
    context = await memory_service.get_user_context(state["user_id"])
    
    context_parts = context_builder.build_context_dict(
        user_info=context["user_info"],
        memory=context["memory"],
        app_state=state.get("app_state"),
        referenced_data=state.get("referenced_data"),
        files=state.get("files")
    )
    
    reference_docs = prompt_service.render_template("reference_document.jinja2", **context_parts)
    return {"reference_docs": reference_docs}

async def load_memory_node(state: AgentState) -> Dict[str, Any]:
    """Retrieves last 5 messages for context"""
    logger.info(f"Node: load_memory_node - Session: {state['session_id']}")
    history = await memory_service.get_history(state["session_id"], limit=5)
    return {"history": history}
