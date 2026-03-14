# System Architecture

The Multi-Agent AI Assistant is built on a modular, orchestrator-led architecture using **LangGraph** for state management and **LiteLLM** for vendor-agnostic LLM integration.

## Core Pillars

### 1. The Orchestrator (`graph_service.py`)
The central brain that:
- Injects roles and guardrails into the state.
- Classifies user intent using `ClassifierService`.
- Manages "Journey Persistence" (Interrrupt/Resume logic).
- Routes to specialized agent sub-graphs.

### 2. Specialized Agents
Each agent is a self-contained LangGraph sub-graph:
- **SmallTalk**: Casual conversation.
- **FAQ**: RAG-based knowledge retrieval.
- **Create Order**: Multi-turn data extraction workflow.
- **Order Status**: Tool-based deterministic lookups.

### 3. State & Persistence
- **AgentState**: A TypedDict tracking chat history, active intent, and workflow-specific metadata.
- **MongoDB**: Used for long-term checkpointing and session management via `ConversationStateManager`.

### 4. Knowledge Management (Advanced RAG)
- **ScrapingService**: Orchestrates sitemap discovery and URL crawling.
- **High-Fidelity Cleaning**: Transformer-like logic to strip boilerplate while preserving semantic structure.
- **Pinecone**: Low-latency vector database for semantic search.

### 5. Management & Observability
- **Admin Portal**: Dedicated endpoints for RAG control and Prompt Engineering.
- **Jinja2 Registry**: Dynamic prompt templates managed through the `PromptLab`.
- **LangSmith**: Full trace visualization for every LLM and Tool call.
- **Logging Decorator**: Standardized `@log_execution` for method tracing.
