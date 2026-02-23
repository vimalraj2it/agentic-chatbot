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
        end
    end
    
    External["LLM Provider (OpenAI/LiteLLM)"]

    %% Flow
    User -->|Message| UI
    UI --> Hook
    Hook -->|POST Request| Proxy
    Proxy -->|Forward stream request| Main
    Main --> Router
    
    Router -->|Get history| Memory
    Router -->|Invoke| Graph
    Router -->|Generate stream| LLM
    
    LLM -->|API Call| External
    External -->|Token chunks| LLM
    
    LLM -->|Stream data| Router
    Router -->|SSE Stream| Proxy
    Proxy -->|Text chunks| Hook
    Hook -->|Update State| UI
    UI -->|Display Response| User
    
    Router -->|Persist messages| Memory
```

## Description of Components

1.  **Frontend (UI)**: React components that render the chat interface and manage user input state.
2.  **Next.js Proxy**: Acts as a gateway to handle CORS and hide the internal backend URL. It transforms SSE (Server-Sent Events) from the backend into a format the frontend hook expects.
3.  **FastAPI Backend**: The core logic server that handles session management and orchestration.
4.  **Memory Service**: Manages short-term conversation history for each session.
5.  **LLM Service**: Handles communication with external AI providers using LiteLLM/OpenAI.
6.  **Graph Service**: (Optional) Uses LangGraph to manage complex multi-step reasoning or tool-calling flows.
