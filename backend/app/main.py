"""
backend/app/main.py
Main entrypoint for the FastAPI application.
Mounts API routers, handles CORS, and serves static frontend assets.
"""

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.config import get_settings
from backend.app.api.health import router as health_router
from backend.app.api.chat import router as chat_router
from backend.app.core.errors import AppException, app_exception_handler

settings = get_settings()

app = FastAPI(
    title="AI Customer Support Agent with Persistent Memory",
    description="Context-aware customer support assistant powered by Hindsight persistent memory and Groq LLMs.",
    version="1.0.0",
)

# Global Exception Handlers
app.add_exception_handler(AppException, app_exception_handler)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(health_router)
app.include_router(chat_router)

# Mount Frontend static directory
frontend_path = Path(__file__).resolve().parent.parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
