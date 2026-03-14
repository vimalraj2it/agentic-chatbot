# Setup and Testing Guide

## 1. Environment Requirements
- **Python**: 3.10+
- **Database**: MongoDB (Persistence) & Redis (Pub/Sub)
- **Vector DB**: Pinecone (FAQ/RAG)

## 2. Configuration
Create a `.env` with:
- `MONGODB_URL`
- `REDIS_URL`
- `OPENAI_API_KEY`
- `PINECONE_API_KEY`
- `PINECONE_INDEX_NAME`
- `EMBEDDING_MODEL` (default: `sentence-transformers/all-MiniLM-L6-v2`)

## 3. Installation
```bash
# Create virtual environment
uv venv
source .venv/bin/activate  # Or .venv\Scripts\activate on Windows

# Install dependencies (from requirements.txt if present)
uv pip install -r requirements.txt
uv pip install pinecone-client trafilatura beautifulsoup4
```

## 3. Running the App
```bash
# Start API
python src/main.py

# Start Workers
celery -A src.core.celery_app worker

# Start Frontend
cd web && npm run dev
```

## 4. Local Development (No Celery)
Set `USE_CELERY=False` in `.env` to process all tasks synchronously via FastAPI `BackgroundTasks`.

## 5. Deployment
- **Frontend**: S3 Static Export.
- **Backend**: Containerized (Docker).
