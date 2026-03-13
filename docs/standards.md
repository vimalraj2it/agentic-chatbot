# Development Standards

To ensure consistency and reliability, all contributions must adhere to these technical standards.

## 1. Structured Input/Output
Every LLM call requiring data extraction or logic MUST use Pydantic schemas.
- **Input**: Use `PromptService` and Jinja2 templates.
- **Output**: Use `response_format` with `json_schema` in `get_chat_completion`.

## 2. Prompt Management
- **Location**: `src/templates/prompts/*.jinja2`.
- **Logic**: No hardcoded strings in Python nodes. Use `prompt_service.render_template()`.

## 3. Tool Implementation
- Register all tools in `src/tools/registry.py`.
- Apply `@log_execution` to every tool handler.
- Define strict `required_params` for validation.
- Implement guardrails in `src/tools/guardrails.py`.

## 4. Logging & Tracing
Use the `@log_execution` decorator for:
- Start of method (Input parameters).
- End of method (Return value).
- Error handling (Exception details).
