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
        base_dir = os.path.dirname(__file__)
        self.config_dir = os.path.join(base_dir, "..", "templates", "config")
        self.template_dir = os.path.join(base_dir, "..", "templates", "prompts")
        
        config_path = os.path.join(self.config_dir, "prompt_config.json")
        
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
        output_format: Optional[str] = None,
        use_cache: bool = False
    ) -> Any:
        """
        Builds a structured system prompt using Jinja2 templates and JSON config.
        If use_cache is True, returns a list content block for Anthropic caching.
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
                prompt_str = template.render(**template_data)
            except Exception as e:
                logger.error(f"Error rendering Jinja template: {e}")
                prompt_str = self._build_fallback_prompt(template_data)
        else:
            prompt_str = self._build_fallback_prompt(template_data)

        if use_cache:
            return [{
                "type": "text", 
                "text": prompt_str,
                "cache_control": {"type": "ephemeral"}
            }]
            
        return prompt_str

    def _build_fallback_prompt(self, template_data: Dict[str, Any]) -> str:
        """Fallback Logic when Jinja is unavailable."""
        logger.warning("Using fallback system prompt (Jinja2 unavailable or failed)")
        sections = [
            "# ROLE & CORE RULES",
            template_data["system_rules"]
        ]

        if template_data["context_string"]:
            sections.append("# CONTEXT & DATA")
            sections.append(template_data["context_string"])

        sections.append("# GUARDRAILS & RESPONSE FORMAT")
        guardrails_str = "\n".join([f"- {g}" for g in template_data["guardrails"]])
        sections.append(guardrails_str)

        if template_data["output_format"] == "json":
            sections.append("Response MUST be a valid JSON object. Do not include any text outside the JSON block.")
            sections.append("Format: {\"response\": \"your message here\"}")
        else:
            sections.append("Response should be in clean Markdown format.")

        return "\n\n".join(sections)

    def build_split_system_prompt(
        self, 
        context_parts: Dict[str, str],
        guardrails: Optional[List[str]] = None,
        output_format: Optional[str] = None,
        use_cache: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Builds a list of 4 system messages using modular Jinja2 templates:
        1 -> ROLE & CORE RULES (role_rules.jinja2)
        2 -> USER PROFILE (user_profile.jinja2)
        3 -> GUARDRAILS & RESPONSE FORMAT (guardrails_format.jinja2)
        4 -> REFERENCE DOCUMENT (reference_document.jinja2)
        """
        fmt = (output_format or self.config.get("output_format", "markdown")).lower()
        
        # Base data for all templates
        base_data = {
            "system_rules": self.config.get("system_rules"),
            "guardrails": self.config.get("guardrails", []) + (guardrails or []),
            "output_format": fmt,
            **context_parts
        }

        # Template mapping
        template_map = [
            ("role_rules.jinja2", "role_rules"),
            ("user_profile.jinja2", "user_profile"),
            ("guardrails_format.jinja2", "guardrails_format"),
            ("reference_document.jinja2", "reference_document")
        ]

        messages = []
        
        if self.env:
            for t_name, _ in template_map:
                try:
                    template = self.env.get_template(t_name)
                    content = template.render(**base_data).strip()
                    messages.append({"role": "system", "content": content})
                except Exception as e:
                    logger.error(f"Error rendering {t_name}: {e}")
                    # Fallback to a placeholder if template fails
                    messages.append({"role": "system", "content": f"Error loading {t_name}"})
        else:
            # Basic fallback if Jinja is not available
            logger.warning("Jinja not available, using basic split prompt fallback")
            return self._build_basic_split_fallback(base_data)

        if use_cache:
            for m in messages:
                m["content"] = [{
                    "type": "text",
                    "text": m["content"],
                    "cache_control": {"type": "ephemeral"}
                }]
        
        return messages

    def _build_basic_split_fallback(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Basic fallback logic when Jinja is unavailable."""
        m1 = {"role": "system", "content": f"# ROLE & CORE RULES\n{data.get('system_rules')}"}
        m2 = {"role": "system", "content": f"# USER PROFILE\n{data.get('user_profile', 'User identity is anonymous.')}"}
        
        guardrails_str = "\n".join([f"- {g}" for g in data.get('guardrails', [])])
        fmt = data.get('output_format', 'markdown')
        format_instr = "Response should be in clean Markdown format."
        if fmt == "json":
            format_instr = "Response MUST be a valid JSON object.\nFormat: {\"response\": \"your message here\"}"
            
        m3 = {"role": "system", "content": f"# GUARDRAILS & RESPONSE FORMAT\n{guardrails_str}\n\n{format_instr}"}
        
        ref = data.get('reference_document', 'No specific reference documents provided.')
        if data.get('dynamic_context'):
            ref += f"\n\n# ADDITIONAL DATA\n{data.get('dynamic_context')}"
        m4 = {"role": "system", "content": f"# REFERENCE DOCUMENT\n{ref}"}
        
        return [m1, m2, m3, m4]

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
