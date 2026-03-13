# Phase 1 — Basic Chat: The Foundation

In this phase, we establish a direct, stateless communication channel between the user interface and the Large Language Model (LLM).

## 🧩 Key Components

### 1. API Bridge (FastAPI)
The backend acts as a proxy, receiving user input and forwarding it to the AI provider.
- **Tools**: FastAPI, Uvicorn.
- **Protocol**: Single HTTP POST request/response cycle.

### 2. AI Connectivity (LiteLLM)
We use a unified interface to talk to different models (GPT, Claude, Gemini).
- **Configuration**: `litellm_config.yaml` manages API keys and model routing.
- **Switching**: Providers can be swapped without changing backend code.

### 3. Basic UI
A simple entry point to test the connection.
- **Features**: Text input, "Send" button, display area for the response.
- **Experience**: No "typing" indicators or history. Each message is a "new" conversation.

## 🛠️ Implementation Steps
1. Configure model credentials in `.env`.
2. Set up a FastAPI endpoint `/chat`.
3. Call the LLM completion API directly.
4. Return the raw text response to the UI.

## ⚠️ Limitations
- **No Persistence**: Refreshing the page loses all data.
- **Limited Context**: The AI can't remember what you said in the previous message.
- **Static Thinking**: Responses are purely based on the LLMs internal knowledge base.
