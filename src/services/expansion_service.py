from typing import List, Dict, Any
from src.services.llm_service import get_chat_completion
from src.services.prompt_service import prompt_service
from src.core.config import settings
from src.core.logging_config import get_logger
from src.models.schemas import QueryExpansion
import json

logger = get_logger(__name__)

class ExpansionService:
    async def expand_query(
        self, 
        user_message: str, 
        history: List[Dict[str, Any]] = None,
        user_profile: str = None,
        guardrails: str = None
    ) -> List[Dict[str, Any]]:
        """Expands user query into multiple variations for better retrieval, considering context"""
        logger.info(f"Expanding query: {user_message} with history length: {len(history) if history else 0}")
        
        try:
            # Render system prompt
            system_content = prompt_service.render_template(
                "expansion.jinja2", 
                user_message=user_message,
                history=history
            )
            
            # Formulate structured messages similar to classifier
            messages = [{"role": "system", "content": system_content}]
            
            if user_profile:
                messages.append({"role": "system", "content": user_profile})
            if guardrails:
                messages.append({"role": "system", "content": guardrails})
                
            if history:
                messages += history
                
            messages.append({"role": "user", "content": user_message})
            
            response = await get_chat_completion(
                messages=messages,
                model=settings.CLASSIFIER_MODEL, # Use classifier model for expansion too
                temperature=0.0,
                top_p=0.1,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "query_expansion",
                        "schema": QueryExpansion.model_json_schema(),
                        "strict": True
                    }
                }
            )
            
            content = response.choices[0].message.content
            logger.info(f"Raw Expansion Response: {content}")
            
            expansion = QueryExpansion.model_validate_json(content)
            # Convert ScoredQuery objects to dictionaries
            variations = [{"query": q.query, "score": q.score} for q in expansion.expanded_queries]
            
            # Include original query at the end as a fallback
            all_queries = variations + [{"query": user_message, "score": 1.0}]
            
            # Deduplicate by query string
            seen = set()
            unique_queries = []
            for item in all_queries:
                if item["query"] not in seen:
                    unique_queries.append(item)
                    seen.add(item["query"])
                    
            return unique_queries
            
        except Exception as e:
            logger.error(f"Error in query expansion: {e}")
            return [{"query": user_message, "score": 1.0}] # Fallback to original query

expansion_service = ExpansionService()
