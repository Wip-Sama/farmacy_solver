import os
import sys
import logging
from pathlib import Path

# Ensure project root is in sys.path when running python backend/main.py directly
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.config import APP_CONFIG
from backend.api.routes import router as api_router
from backend.api.ws import router as ws_router

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("uvicorn.error")

class SPAStaticFiles(StaticFiles):
    """StaticFiles handler that falls back to index.html for SPA client-side routes."""
    async def get_response(self, path: str, scope):
        try:
            response = await super().get_response(path, scope)
            if response.status_code == 404 and "." not in path.split("/")[-1]:
                response = await super().get_response("index.html", scope)
            return response
        except Exception:
            return await super().get_response("index.html", scope)

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

# Register routers
app.include_router(api_router, prefix="/api")
app.include_router(ws_router, prefix="/api")

@app.get("/api")
async def api_info():
    return {
        "app": "UNICAL Demacs Pharmacy Solver API",
        "status": "running",
        "docs": "/docs",
        "ws": "/api/ws"
    }

@app.on_event("startup")
async def log_startup_banner():
    """Logs startup access URLs clearly in the server console (visible in Docker logs)."""
    banner = (
        "\n" + "=" * 64 + "\n"
        "  UNICAL Demacs Pharmacy Solver is running!\n"
        "\n"
        "  Access Points:\n"
        "   - Web UI:   http://localhost:8001/\n"
        "   - API Base: http://localhost:8001/api\n"
        "   - API Docs: http://localhost:8001/docs\n"
        "=" * 64
    )
    print(banner, flush=True)
    logging.info(banner)

# Mount static frontend build (SPA) at root / if frontend/dist exists (e.g. Docker production runtime)
frontend_dist = Path(PROJECT_ROOT) / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", SPAStaticFiles(directory=str(frontend_dist), html=True), name="static_frontend")
else:
    @app.get("/")
    async def root():
        return {
            "app": "UNICAL Demacs Pharmacy Solver API",
            "status": "running",
            "docs": "/docs",
            "ws": "/api/ws"
        }

if __name__ == "__main__":
    import uvicorn
    host = APP_CONFIG.get("server", {}).get("host", "127.0.0.1")
    port = APP_CONFIG.get("server", {}).get("backend_port", 8000)
    reload = APP_CONFIG.get("server", {}).get("reload", True)
    uvicorn.run("backend.main:app", host=host, port=port, reload=reload)

