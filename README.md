# AI Chat Multi-Frontend Application

A production-ready AI chat application featuring a **3-tier architecture**: **Next.js Frontend**, **FastAPI Backend**, and a centralized **LiteLLM Proxy Server**.

## 🚀 Architecture

-   **Production UI (`web/`)**: Premium **Next.js 15** application powered by **Vercel AI SDK** and Tailwind CSS.
-   **Backend Service (`src/`)**: **FastAPI** hub managing stateful **LangGraph** workflows and session memory.
-   **AI Proxy (`litellm`)**: Centralized model management using the official **LiteLLM Proxy**, handling all provider API keys and observability.
-   **Internal UI (`src/ui.py`)**: Secondary **Streamlit** dashboard for rapid internal testing and monitoring.

## 🛠️ Features

-   **Streaming Support**: Real-time response streaming across all interfaces.
-   **Provider Agnostic**: Switch between OpenAI (GPT-4), Anthropic (Claude-3), Google (Gemini), and Groq with one config change.
-   **Toggleable Proxy**: Run with a full managed server stack or a lightweight direct-to-provider mode.
-   **Containerized**: Fully orchestrated with Docker Compose for one-click deployment.

## 🏃 Getting Started

### 1. Prerequisites
- Docker & Docker Compose
- [uv](https://github.com/astral-sh/uv) (for local non-docker development)
- [pnpm](https://pnpm.io/) (for local non-docker development)

### 2. Environment Setup
The project uses two environment files to separate local and containerized settings:

-   **[`.env`](file:///.env)**: For running scripts directly on your machine.
-   **[`.docker.env`](file:///.docker.env)**: Optimized for internal Docker networking.

Copy the templates and add your API keys:
```bash
cp .env.example .env
cp .env.example .docker.env
```

### 3. Launching

For detailed, step-by-step instructions based on your environment, see:

-   🚀 **[Start with Docker (Recommended)](file:///startwithdocker.md)**
-   💻 **[Start without Docker (Manual)](file:///startwithoutdocker.md)**

Quick launch with Docker:
```bash
docker-compose up --build
```

**Access Points:**
- **Next.js UI**: [http://localhost:3000](http://localhost:3000)
- **FastAPI API**: [http://localhost:8000](http://localhost:8000)
- **Streamlit UI**: [http://localhost:8501](http://localhost:8501)
- **LiteLLM Dashboard**: [http://localhost:4000](http://localhost:4000) (if configured)

## ⚙️ Configuration

### LiteLLM Server Switch
Control how the backend connects to LLMs via the `USE_LITELLM_SERVER` flag in your environment file:
-   **`True`**: Routes all calls through the LiteLLM Proxy (Defined in `litellm_config.yaml`).
-   **`False`**: Calls AI providers directly (Uses `OPENAI_API_KEY`, etc., from `.env`).

### Adding Models
To add new models, simply update [**`litellm_config.yaml`**](file:///litellm_config.yaml) and restart the proxy service.

## 🏗️ Development Phases

The project evolves through the following stages:

-   [**Phase 1 — Basic Chat**](file:///phase/phase1.md): Stateless request/response.
-   [**Phase 2 — Chat + History**](file:///phase/phase2.md): Short-term memory & session management.
-   [**Phase 3 — UI / App Context Injection**](file:///phase/phase3.md): File uploads & business context.
-   [**Phase 4 — Prompt Templates**](file:///phase/phase4.md): Engineering reliability with structured templates.

## 📜 Repository Structure
- `src/`: Core Python backend.
- `web/`: Next.js frontend source.
- `litellm_config.yaml`: Model definitions for the proxy server.
- `docker-compose.yml`: Full stack orchestration.
