# Build & Run without Docker

This mode runs the services directly on your machine. This is faster for development but requires manual setup of each component.

## 1. Prerequisites
- [uv](https://github.com/astral-sh/uv) installed (Python manager).
- [Node.js](https://nodejs.org/) (v18+) installed.
- [pnpm](https://pnpm.io/) installed.

## 2. Configuration
Copy the environment template to `.env`:
```bash
cp .env.example .env
```
Ensure `USE_LITELLM_SERVER=False` in [`.env`](file:///.env) to call providers directly, and add your API keys.

## 3. Run the Services (Separate Terminals)

### Terminal A: FastAPI Backend
```bash
uv sync
uv run uvicorn src.main:app --reload --port 8000
```

### Terminal B: Streamlit Dashboard
```bash
uv run streamlit run src/ui.py --server.port 8501
```

### Terminal C: Next.js Frontend
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
pip install 'litellm[proxy]'
litellm --config litellm_config.yaml --port 4000
```
Then set `USE_LITELLM_SERVER=True` in your `.env`.
