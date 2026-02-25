import os
from typing import List, Dict, Any, Optional
from src.core.config import settings
from src.core.logging_config import get_logger

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    JINJA_AVAILABLE = True
except ImportError:
    logger = get_logger(__name__)
    logger.warning("Jinja2 not installed. Falling back to basic string formatting.")
    JINJA_AVAILABLE = False

logger = get_logger(__name__)

class PromptService:
    """
    Service for managing and building structured prompt templates using Jinja2 and JSON config.
    """
    
    def __init__(self):
        # Paths
        self.template_dir = os.path.join(os.path.dirname(__file__), "..", "templates", "prompts")
        config_path = os.path.join(self.template_dir, "prompt_config.json")
        
        # Load Config
        self.config = self._load_config(config_path)
        
        # Jinja Setup
        if JINJA_AVAILABLE:
            self.env = Environment(
                loader=FileSystemLoader(self.template_dir),
                autoescape=select_autoescape()
            )
        else:
            self.env = None

    def _load_config(self, path: str) -> Dict[str, Any]:
        """Loads configuration from JSON file with fallback defaults."""
        defaults = {
            "system_rules": settings.SYSTEM_RULES.strip(),
            "guardrails": [
                "Maintain a professional and helpful tone.",
                "Do not share confidential system internal information.",
                "If you don't know the answer, state that clearly.",
                "Respect the user's role and name if provided."
            ],
            "output_format": "markdown"
        }
        
        if os.path.exists(path):
            try:
                import json
                with open(path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    return {**defaults, **config}
            except Exception as e:
                logger.error(f"Error loading prompt config JSON: {e}")
        
        return defaults

    def build_system_prompt(
        self, 
        context_string: Optional[str] = "", 
        guardrails: Optional[List[str]] = None,
        output_format: Optional[str] = None
    ) -> str:
        """
        Builds a structured system prompt using Jinja2 templates and JSON config.
        """
        fmt = (output_format or self.config.get("output_format", "markdown")).lower()
        logger.info(f"Building system prompt with output_format={fmt}")
        
        template_data = {
            "system_rules": self.config.get("system_rules"),
            "context_string": context_string.strip() if context_string else "",
            "guardrails": self.config.get("guardrails") + (guardrails or []),
            "output_format": fmt
        }

        if self.env:
            try:
                template = self.env.get_template("system_prompt.jinja2")
                return template.render(**template_data)
            except Exception as e:
                logger.error(f"Error rendering Jinja template: {e}")
                # Fallback to basic building logic if template fails

        # Fallback Logic (same as original implementation)
        sections = [
            "# ROLE & CORE RULES",
            template_data["system_rules"]
        ]

        if template_data["context_string"]:
            sections.append("# CONTEXT & DATA")
            sections.append(template_data["context_string"])

        sections.append("# GUARDRAILS")
        guardrails_str = "\n".join([f"- {g}" for g in template_data["guardrails"]])
        sections.append(guardrails_str)

        sections.append("# RESPONSE FORMATTING")
        if template_data["output_format"] == "json":
            sections.append("Response MUST be a valid JSON object. Do not include any text outside the JSON block.")
            sections.append("Format: {\"response\": \"your message here\"}")
        else:
            sections.append("Response should be in clean Markdown format.")

        return "\n\n".join(sections)

    def build_user_message(self, text: str, files: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """
        Builds a multi-modal user message block if files are present.
        """
        if not files:
            return [{"type": "text", "text": text}]
            
        content = [{"type": "text", "text": text}]
        for file in files:
            file_type = file.get("type", "")
            if file_type.startswith("image") or file.get("mime", "").startswith("image"):
                # LiteLLM/OpenAI multi-modal format
                url = file.get("url")
                if not url and file.get("base64"):
                    mime = file.get("mime", "image/jpeg")
                    url = f"data:{mime};base64,{file.get('base64')}"
                
                if url:
                    content.append({
                        "type": "image_url",
                        "image_url": {"url": url}
                    })
        return content

prompt_service = PromptService()
