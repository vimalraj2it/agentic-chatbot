# Build & Run with Docker (Recommended)

This mode runs the entire 3-tier stack (Next.js, FastAPI, Streamlit, and LiteLLM Proxy) in isolated containers. It includes Phase 3 features like **Context Injection** (PDF reference).

## 1. Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.
- [Docker Compose](https://docs.docker.com/compose/install/) installed.

## 2. Configuration
Copy the environment template to `.docker.env`:
```bash
cp .env.example .docker.env
```
Open [`.docker.env`](file:///.docker.env) and add your API keys:
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GEMINI_API_KEY`
- `GROQ_API_KEY`
- `MISTRAL_API_KEY`
- `PINECONE_API_KEY` (along with `PINECONE_ENV`, `PINECONE_CLOUD`, `PINECONE_REGION`)
- **LangSmith** variables (optional, for tracing): `LANGCHAIN_TRACING_V2`, `LANGCHAIN_API_KEY`, etc.

## 3. Launch
Run the orchestration command:
```bash
docker-compose up --build
```

## 4. Access the Services
Once the containers are healthy, visit:
- **Next.js UI**: [http://localhost:3000](http://localhost:3000)
- **FastAPI API**: [http://localhost:8000](http://localhost:8000)
- **Streamlit UI**: [http://localhost:8501](http://localhost:8501)
- **LiteLLM Proxy**: [http://localhost:4000](http://localhost:4000)

## 🛑 Stop
To shut down the stack:
```bash
docker-compose down
```
