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

### 4. Observability
- **@log_execution**: Standardized decorator for method entry/exit logging.
- **LangSmith**: Full trace visualization for every LLM and Tool call.
- **Cost Tracking**: Usage metrics collected at the `llm_service.py` level.
