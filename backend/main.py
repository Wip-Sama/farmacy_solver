import os
import sys
import logging

# Ensure project root is in sys.path when running python backend/main.py directly
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import APP_CONFIG

from backend.api.routes import router as api_router
from backend.api.ws import router as ws_router

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = FastAPI(
    title="Pharmacy Solver API",
    description="REST & Real-Time WebSocket API for ASP Pharmacy Scheduling",
    version="1.0.0"
)

# Configure CORS
frontend_port = APP_CONFIG.get("server", {}).get("frontend_port", 5173)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    f"http://localhost:{frontend_port}",
    f"http://127.0.0.1:{frontend_port}",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles

# Register routers
app.include_router(api_router, prefix="/api")
app.include_router(ws_router, prefix="/api")

@app.get("/")
async def root():
    return {
        "app": "UNICAL Demacs Pharmacy Solver API",
        "status": "running",
        "docs": "/docs",
        "ws": "/api/ws"
    }

# Mount static frontend build (SPA) if frontend/dist exists (e.g. Docker container)
frontend_dist = os.path.join(PROJECT_ROOT, "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/static", StaticFiles(directory=frontend_dist, html=True), name="static_frontend")

if __name__ == "__main__":
    import uvicorn
    host = APP_CONFIG.get("server", {}).get("host", "127.0.0.1")
    port = APP_CONFIG.get("server", {}).get("backend_port", 8000)
    reload = APP_CONFIG.get("server", {}).get("reload", True)
    uvicorn.run("backend.main:app", host=host, port=port, reload=reload)
