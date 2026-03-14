# Admin Portal & Management Tools

Centralized management for administrators to control knowledge ingestion, prompt engineering, and system health.

## RAG Control Center

Allows administrators to manage the knowledge base lifecycle.
- **Trigger Indexing**: Manually trigger `index_website` for a target base URL.
- **Discovery Logs**: View sitemap discovery results and URL counts.
- **Vector Stats**: monitor the number of indexed chunks in Pinecone.

## Prompt Lab

A sandbox for managing LLM prompts without code deployments.
- **Jinja2 Editor**: Live-edit system templates (e.g., `faq_system.jinja2`).
- **A/B Testing**: Compare different prompt versions against sample user inputs.
- **One-Click Deploy**: Push verified prompts to the production Jinja2 registry.

## System Monitoring

Integration with observability platforms.
- **LangSmith Traces**: Direct links to specific conversation traces for debugging.
- **Inventory/Order Overrides**: Manual control over business logic data for testing and support scenarios.

## Configuration Management

Manage application environment variables and feature flags.
- **Environment Overrides**: Secure editing of non-sensitive settings.
- **Service Status**: Dashboard showing health of Redis, MongoDB, and Celery workers.
