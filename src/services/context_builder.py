from typing import List, Dict, Any, Optional
from src.core.logging_config import get_logger

logger = get_logger(__name__)

class ContextBuilder:
    @staticmethod
    def format_user_profile(user_info: Dict[str, Any]) -> str:
        if not user_info:
            return ""
        
        name = user_info.get("name", "Anonymous")
        role = user_info.get("role", "User")
        return f"User Profile:\n- Name: {name}\n- Role: {role}\n"

    @staticmethod
    def format_app_state(app_state: Dict[str, Any]) -> str:
        if not app_state:
            return ""
        
        lines = ["Current App State:"]
        for key, value in app_state.items():
            lines.append(f"- {key}: {value}")
        return "\n".join(lines) + "\n"

    @staticmethod
    def format_database_rows(referenced_data: List[Dict[str, Any]]) -> str:
        if not referenced_data:
            return ""
        
        lines = ["Referenced Database Rows:"]
        for idx, row in enumerate(referenced_data):
            lines.append(f"Row {idx + 1}:")
            for key, value in row.items():
                lines.append(f"  - {key}: {value}")
        return "\n".join(lines) + "\n"

    @staticmethod
    def format_file_context(files: List[Dict[str, Any]]) -> str:
        if not files:
            return ""
        
        lines = ["Attached Files Context:"]
        for idx, file_data in enumerate(files):
            filename = file_data.get("filename", f"file_{idx}")
            content = file_data.get("content", "[No content preview available]")
            lines.append(f"File: {filename}\nContent:\n{content}")
        return "\n".join(lines) + "\n"

    _reference_cache: Optional[str] = None

    @classmethod
    def load_reference_pdf(cls, file_path: str = "reference-file/reference_context.txt") -> str:
        if cls._reference_cache is not None:
            return cls._reference_cache
        
        try:
            import os
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    cls._reference_cache = f.read()
                    logger.info("Reference context loaded from file.")
            else:
                logger.warning(f"Reference file not found at {file_path}")
                cls._reference_cache = ""
        except Exception as e:
            logger.error(f"Error loading reference context: {e}")
            cls._reference_cache = ""
            
        return cls._reference_cache

    @classmethod
    def build_context_dict(
        cls,
        user_info: Optional[Dict] = None,
        memory: Optional[List[str]] = None,
        app_state: Optional[Dict] = None,
        referenced_data: Optional[List[Dict]] = None,
        files: Optional[List[Dict]] = None
    ) -> Dict[str, str]:
        """
        Builds a dictionary of different context parts for split system messages.
        """
        logger.info("Building context dictionary")
        
        # 1. Profile 
        profile_parts = []
        if user_info:
            profile_parts.append(cls.format_user_profile(user_info))
        if memory:
            profile_parts.append(f"Past Conversation Topics: {', '.join(memory)}\n")
        
        # 2. Reference Document
        ref_context = cls.load_reference_pdf()

        # 3. Dynamic Context/Files
        dynamic_parts = []
        if app_state:
            dynamic_parts.append(cls.format_app_state(app_state))
        if referenced_data:
            dynamic_parts.append(cls.format_database_rows(referenced_data))
        if files:
            dynamic_parts.append(cls.format_file_context(files))

        return {
            "user_profile": "\n".join(profile_parts) if profile_parts else "",
            "reference_document": ref_context if ref_context else "",
            "dynamic_context": "\n".join(dynamic_parts) if dynamic_parts else ""
        }

    @classmethod
    def build_combined_context(
        cls,
        user_info: Optional[Dict] = None,
        memory: Optional[List[str]] = None,
        app_state: Optional[Dict] = None,
        referenced_data: Optional[List[Dict]] = None,
        files: Optional[List[Dict]] = None
    ) -> str:
        logger.info("Building combined context string")
        parts = []
        
        # Inject Static PDF Reference Context First
        ref_context = cls.load_reference_pdf()
        if ref_context:
            parts.append("### REFERENCE DOCUMENT: 811 Dream Different Credit Card Offer Terms & Conditions ###")
            parts.append(ref_context)
            parts.append("#################################################################################\n")

        if user_info:
            parts.append(cls.format_user_profile(user_info))
            
        if memory:
            parts.append(f"Past Conversation Topics: {', '.join(memory)}\n")
            
        if app_state:
            parts.append(cls.format_app_state(app_state))
            
        if referenced_data:
            parts.append(cls.format_database_rows(referenced_data))
            
        if files:
            parts.append(cls.format_file_context(files))
            
        return "\n".join(parts)

context_builder = ContextBuilder()
