# Build & Run without Docker

This mode runs the services directly on your machine. This is faster for development but requires manual setup of each component.

## 1. Prerequisites
- [uv](https://github.com/astral-sh/uv) installed (Python manager).
- [Node.js](https://nodejs.org/) (v18+) installed.
- [pnpm](https://pnpm.io/) installed.
- **[Redis](https://redis.io/docs/getting-started/)** installed and running (Required for Celery).
- **[MongoDB](https://www.mongodb.com/docs/manual/installation/)** installed and running.

## 2. Configuration
Copy the environment template to `.env`:
```bash
cp .env.example .env
```
Ensure `USE_LITELLM_SERVER=False` in [`.env`](file:///.env) to call providers directly, and add your required API keys:
- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `GROQ_API_KEY`, `MISTRAL_API_KEY`
- `PINECONE_API_KEY` (along with `PINECONE_ENV`, `PINECONE_CLOUD`, `PINECONE_REGION`)
- **LangSmith** variables (optional, for tracing): `LANGCHAIN_TRACING_V2`, `LANGCHAIN_API_KEY`, etc.

## 3. Run the Services (Separate Terminals)

> **Minimal Mode**: If you want to run the application entirely synchronously without Celery or Redis, simply set `USE_CELERY=False` in your `.env`. If you do this, you can skip **Terminal B** entirely. 
> Additionally, if you don't need the admin dashboard, you can skip **Terminal C** (Streamlit).

### Terminal A: FastAPI Backend
```bash
uv sync
uv run uvicorn src.main:app --reload --port 8000
```

### Terminal B: Celery Worker
```bash
# Ensure Redis is running first!
# Note: On Windows, use --pool=solo or --pool=threads
uv run celery -A src.core.celery_app worker --loglevel=info --pool=solo
```

### Terminal C: Streamlit Dashboard
```bash
uv run streamlit run src/ui.py --server.port 8501
```

### Terminal D: Next.js Frontend
```bash
cd web
pnpm install
pnpm run dev
```

## 4. Access the Services
- **Next.js UI**: [http://localhost:3000](http://localhost:3000)
- **FastAPI API**: [http://localhost:8000](http://localhost:8000)
- **Streamlit UI**: [http://localhost:8501](http://localhost:8501)

## 💡 Pro Tip
If you want to use the **LiteLLM Server** without Docker, you must run it manually:
```bash
uv pip install 'litellm[proxy]'
litellm --config litellm_config.yaml --port 4000
```
Then set `USE_LITELLM_SERVER=True` in your `.env`.

## 5. Troubleshooting (Windows / Git Bash)

### Find and Kill Services by Port
If a port is already in use (e.g., 8000 or 3000), use these commands:

1. **Find PID by port (e.g., 8000):**
   ```bash
   netstat -ano | grep :8000
   ```
   *The PID is the number in the very last column.*

2. **Kill process by PID:**
   *(Wait for the previous command to give you the PID. If the output showed PID 31036, you would run: `taskkill -F -PID 31036`)*
   ```bash
   taskkill -F -PID <PID_NUMBER>
   ```

### Stop Running Celery Workers
If Celery workers are stuck in the background:

1. **Find Celery/Python processes:**
   ```bash
   tasklist | grep python
   ```

2. **Kill all Python processes (Warning: stops FastAPI too):**
   ```bash
   taskkill -F -IM python.exe -T
   ```
