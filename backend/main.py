from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from app.database import init_db
from app.api import auth, agents, chains
from app.core.logging import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger.info("Starting GPTGram API...")
    init_db()
    yield
    # Shutdown
    logger.info("Shutting down GPTGram API...")

# Create FastAPI app
app = FastAPI(
    title="GPTGram - A2A DAG Orchestration Platform",
    description="Agent-to-Agent marketplace with DAG orchestration, A2A compliance, and n8n compatibility",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(agents.router)
app.include_router(chains.router)

@app.get("/")
async def root():
    return {
        "name": "GPTGram API",
        "version": "1.0.0",
        "status": "operational",
        "a2a_compliant": True
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
