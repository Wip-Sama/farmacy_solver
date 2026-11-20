import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Ensure project root is in sys.path when running python backend/main.py directly
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.api.routes import router as api_router
from backend.api.ws import router as ws_router
from core.config import APP_CONFIG

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("uvicorn.error")


class SPAStaticFiles(StaticFiles):
    """StaticFiles handler that falls back to index.html for SPA client-side routes."""

    async def get_response(self, path: str, scope):
        clean_path = path.lstrip("/")
        if clean_path == "api" or clean_path.startswith("api/"):
            raise StarletteHTTPException(status_code=404, detail="Not Found")

        try:
            response = await super().get_response(path, scope)
            if response.status_code == 404 and "." not in path.split("/")[-1]:
                response = await super().get_response("index.html", scope)
            return response
        except Exception:
            return await super().get_response("index.html", scope)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Logs startup access URLs clearly in the server console."""
    port = os.getenv("PORT") or APP_CONFIG.get("server", {}).get("backend_port", 8001)
    divider = "=" * 64
    banner = (
        f"\n{divider}\n"
        "  UNICAL Demacs Pharmacy Solver is running!\n"
        "\n"
        "  Access Points:\n"
        f"   - Web UI:   http://localhost:{port}/\n"
        f"   - API Base: http://localhost:{port}/api\n"
        f"   - API Docs: http://localhost:{port}/docs\n"
        f"{divider}"
    )
    logger.info(banner)
    yield


app = FastAPI(
    title="Pharmacy Solver API",
    description="REST & Real-Time WebSocket API for ASP Pharmacy Scheduling",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(ws_router, prefix="/api")


@app.get("/api")
async def api_info():
    return {
        "app": "UNICAL Demacs Pharmacy Solver API",
        "status": "running",
        "docs": "/docs",
        "ws": "/api/ws",
    }


@app.get("/api/health")
async def health_check():
    """Lightweight liveness check without disk I/O or audit log noise."""
    return {"status": "ok"}


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
            "ws": "/api/ws",
        }


if __name__ == "__main__":
    host = APP_CONFIG.get("server", {}).get("host", "127.0.0.1")
    port = int(os.getenv("PORT") or APP_CONFIG.get("server", {}).get("backend_port", 8000))
    reload = APP_CONFIG.get("server", {}).get("reload", True)
    uvicorn.run("backend.main:app", host=host, port=port, reload=reload)
