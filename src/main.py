from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

from contextlib import asynccontextmanager
from src.core.logging_config import setup_logging
# Initialize logging FIRST before other local imports
setup_logging()

from src.api.router import router as api_router
from src.core.config import settings
from src.core.database import db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await db.connect_to_storage()
    
    # Initialize LangSmith Tracing
    if settings.LANGCHAIN_TRACING_V2.lower() == "true":
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT
        os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
        print(f"LangSmith Tracing Enabled: {settings.LANGCHAIN_PROJECT}")

    # Generate Graph Visualizations
    try:
        from src.services.graph_service import generate_all_visualizations
        generate_all_visualizations()
    except Exception as e:
        print(f"Error generating graphs: {e}")
    yield
    # Shutdown
    await db.close_storage()

app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router, prefix="/api")

# Serve static files (Frontend)
if os.path.exists("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
