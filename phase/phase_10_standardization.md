# Phase 10: Structured Input & Output Standardization

## Goal
Eliminate manual JSON parsing and ensure all LLM interactions use strict structured I/O for better reliability and validation.

## Changes
- **Classifier Service**: Refactored `ClassifierService.get_intent` to use `response_format` with Pydantic models.
- **Create Order Agent**: Upgraded data extraction to use real structured LLM calls instead of manual regex/parsing.
- **Agent Responses**: Standardized `SmallTalkResponse` and `FAQResponse` usage across all nodes.
- **Validation**: Added strict Pydantic validation for all incoming and outgoing LLM payloads.

## Files Modified
- `src/services/classifier_service.py`
- `src/graphs/create_order.py`
- `src/models/schemas.py`
- `src/services/llm_service.py`
