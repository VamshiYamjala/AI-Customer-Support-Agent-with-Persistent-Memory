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
from backend.app.api.auth import router as auth_router
from backend.app.api.sessions import router as sessions_router
from backend.app.core.errors import AppException, app_exception_handler

# Global application settings loaded from environment or defaults
settings = get_settings()

# Initialize FastAPI application instance
# Configured for AI Customer Support with persistent customer memory
app = FastAPI(
    title="AI Customer Support Agent with Persistent Memory",
    description="Context-aware customer support assistant powered by Hindsight persistent memory and Groq LLMs.",
    version="1.0.0",
)

# Register global custom exception handler for unified error responses
app.add_exception_handler(AppException, app_exception_handler)

# Configure Cross-Origin Resource Sharing (CORS) permissions
cors_origins = settings.allowed_origins_list
allow_credentials = False if "*" in cors_origins else True

# Attach CORS middleware to enable secure browser-based access from frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register modular API routers
# Health checks, authentication, customer session management, and conversational chat endpoints
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(sessions_router)
app.include_router(chat_router)

# Mount frontend static directory to serve web assets directly
frontend_path = Path(__file__).resolve().parent.parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")


if __name__ == "__main__":
    import os
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=port)

