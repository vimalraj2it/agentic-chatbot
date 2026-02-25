# Data Flow Diagram

This diagram illustrates the flow of data from the user interface through the various backend layers.

```mermaid
graph TD
    User([User])
    
    subgraph "Frontend (Next.js - Port 3000)"
        UI["Chat UI (src/app/page.tsx)"]
        Hook["useChatbot Hook"]
        Proxy["API Route Proxy (api/chat/route.ts)"]
    end
    
    subgraph "Backend (FastAPI - Port 8000)"
        Main["FastAPI App (main.py)"]
        Router["API Router (router.py)"]
        
        subgraph "Service Layer"
            Memory["Memory Service (memory_service.py)"]
            LLM["LLM Service (llm_service.py)"]
            Graph["Graph Service (graph_service.py)"]
            Prompt["Prompt Service (prompt_service.py)"]
            Context["Context Builder (context_builder.py)"]
        end
    end
    
    External["LLM Provider (OpenAI/LiteLLM)"]

    %% Flow
    User -->|Message| UI
    UI --> Hook
    Hook -->|POST Request| Proxy
    Proxy -->|Forward stream request| Main
    Main --> Router
    
    Router -->|Invoke| Graph
    Graph -->|Get history/profile| Memory
    Graph -->|Build context| Context
    Graph -->|Build system prompt| Prompt
    Graph -->|Call LLM| LLM
    
    LLM -->|API Call| External
    External -->|Token chunks| LLM
    
    LLM -->|Stream data| Graph
    Graph -->|Stream output| Router
    Router -->|SSE Stream| Proxy
    Proxy -->|Text chunks| Hook
    Hook -->|Update State| UI
    UI -->|Display Response| User
    
    Graph -->|Persist messages| Memory
```

## Data Sequence Diagram

This sequence diagram detail the step-by-step interaction between components for a single chat message.

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Frontend as UI (page.tsx)
    participant Proxy as Proxy (route.ts)
    participant Router as API Router (router.py)
    participant Graph as Graph Service (graph_service.py)
    participant Memory as Memory Service (memory_service.py)
    participant Context as Context Builder (context_builder.py)
    participant Prompt as Prompt Service (prompt_service.py)
    participant LLM as LLM Service (llm_service.py)
    participant AI as External LLM

    User->>Frontend: Type "Hello"
    Frontend->>Proxy: POST /api/chat
    Proxy->>Router: Forward request to FastAPI
    Router->>Graph: graph.ainvoke(state)
    
    Note over Graph: Node: load_memory_node
    Graph->>Memory: get_history(session_id)
    Memory-->>Graph: Returns recent messages
    
    Note over Graph: Node: inject_context
    Graph->>Memory: get_user_context(user_id)
    Memory-->>Graph: Returns profile & memory
    Graph->>Context: build_combined_context(...)
    Context-->>Graph: Returns enriched context string
    Graph->>Prompt: build_system_prompt(context, cache=True)
    Prompt-->>Graph: Returns structured system prompt
    
    Note over Graph: Node: call_llm
    Graph->>LLM: get_chat_completion(messages)
    LLM->>AI: LiteLLM API Call
    AI-->>LLM: Response content
    LLM-->>Graph: Assistant message
    
    Graph->>Memory: save_message(...)
    Graph-->>Router: Final State
    Router-->>Proxy: SSE stream / JSON response
    Proxy-->>Frontend: Token chunks
    Frontend-->>User: Display response
```

## Description of Components

1.  **Frontend (UI)**: React components that render the chat interface and manage user input state.
    -   **File**: `web/src/app/page.tsx`
    -   **Hook**: `useChatbot` (manages message state and streaming).

2.  **Next.js Proxy**: Acts as a gateway to handle CORS and hide the internal backend URL.
    -   **File**: `web/src/app/api/chat/route.ts` (POST handler).

3.  **FastAPI Backend**: The core logic server that handles session management and orchestration.
    -   **EntryPoint**: `src/main.py`
    -   **Routing**: `src/api/router.py` (orchestrates graph invocation).

4.  **Memory Service**: Manages conversation history and user profiles.
    -   **File**: `src/services/memory_service.py`
    -   **Methods**: `get_history()`, `get_user_context()`, `save_message()`.

5.  **Context Builder**: Logic for assembling various data points into a coherent context string.
    -   **File**: `src/services/context_builder.py`
    -   **Method**: `build_combined_context()`.

6.  **Prompt Service**: Manages Jinja2 templates for system prompts with `cache_control` support.
    -   **File**: `src/services/prompt_service.py`
    -   **Method**: `build_system_prompt()`.

7.  **Graph Service**: The central orchestrator (using LangGraph) identifying nodes and transitions.
    -   **File**: `src/services/graph_service.py`
    -   **Methods**: `load_memory_node()`, `context_injection_node()`, `call_llm_node()`.

8.  **LLM Service**: Handles communication with external AI providers using LiteLLM/OpenAI.
    -   **File**: `src/services/llm_service.py`
    -   **Methods**: `get_chat_completion()`, `get_chat_stream()`.
