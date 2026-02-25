import json
from typing import Dict, Any, List, Optional
from src.services.llm_service import get_chat_completion
from src.services.prompt_service import prompt_service
from src.models.schemas import QueryClassification
from src.core.logging_config import get_logger

logger = get_logger(__name__)

class ClassifierService:
    """
    Service for classifying user queries using LLM.
    """
    
    async def classify(self, message: str, chat_history: Optional[List[Dict[str, Any]]] = None) -> QueryClassification:
        logger.info(f"Classifying message: {message[:50]}...")
        
        prompt = prompt_service.build_classification_prompt(message, chat_history)
        return await self.classify_with_prompt(prompt)

    async def classify_with_messages(self, messages: List[Dict[str, Any]]) -> QueryClassification:
        """
        Classifies user intent using a structured list of messages.
        Matches the request format used by the specialized agents.
        """
        logger.info("Classifying with structured messages...")
        
        try:
            # Standardize messages (remove 'id' etc)
            from src.services.llm_service import clean_messages
            cleaned_messages = clean_messages(messages)
            
            response = await get_chat_completion(
                messages=cleaned_messages,
                model=None, # Use default model
                stream=False
            )
            
            content = response.choices[0].message.content
            logger.info(f"Raw Classifier Response: {content}")
            
            # Clean JSON if wrapped in markdown
            json_str = content
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                # If no markdown, try to find the first '{' and last '}'
                try:
                    start = content.find("{")
                    end = content.rfind("}") + 1
                    if start != -1 and end != 0:
                        json_str = content[start:end]
                except:
                    pass
            
            data = json.loads(json_str)
            
            # Ensure required_tools is a list
            if "required_tools" not in data or data["required_tools"] is None:
                data["required_tools"] = []
            
            result = QueryClassification(**data)
            logger.info(f"Parsed Classification: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error in query classification with messages: {e}")
            return QueryClassification(
                intent="faq",
                domain="general",
                safety="safe",
                required_tools=[],
                complexity_level="low"
            )

    def build_classification_prompt_from_messages(self, messages: List[Dict[str, Any]]) -> str:
        """Converts structured messages into a classification prompt"""
        # Extract the user message and history for the existing prompt builder
        # Or construct a specialized prompt that respects the structured context
        user_message = ""
        history = []
        for msg in messages:
            if msg["role"] == "user":
                user_message = msg["content"]
            elif msg["role"] == "assistant":
                history.append(msg)
                
        # We still want to use the Jinja template for classification logic
        return prompt_service.build_classification_prompt(user_message, history)

    async def classify_with_prompt(self, prompt: str) -> QueryClassification:
        """Executes classification logic with a pre-built prompt"""
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = await get_chat_completion(
                messages=messages,
                model=None, # Use default model
                stream=False
            )
            
            content = response.choices[0].message.content
            # Clean JSON if wrapped in markdown
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            data = json.loads(content)
            
            # Ensure required_tools is a list
            if "required_tools" not in data or data["required_tools"] is None:
                data["required_tools"] = []
            
            return QueryClassification(**data)
            
        except Exception as e:
            logger.error(f"Error in query classification: {e}")
            # Fallback to a safe default
            return QueryClassification(
                intent="faq", # Default to faq to be safe (include context)
                domain="general",
                safety="safe",
                required_tools=[],
                complexity_level="low"
            )

classifier_service = ClassifierService()
