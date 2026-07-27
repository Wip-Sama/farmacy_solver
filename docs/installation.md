# Installation & Setup Guide

This guide describes how to install dependencies, configure environment settings, and launch the development servers for the Pharmacy Scheduling System.

---

## Prerequisites

Ensure your system has the following tools installed:

1. **Python 3.10+** (verify via `python --version`)
2. **Node.js 18+ & npm 9+** (verify via `node --version` and `npm --version`)
3. **PowerShell 7+ or standard Windows PowerShell** (for Windows automated scripts)

---

## 1. Quick One-Click Setup (Recommended)

Run the automated installation script from the project root:

```powershell
.\scripts\install.ps1
```

This script will automatically:
- Create a Python virtual environment (`.venv312`) if it does not already exist.
- Install all backend Python dependencies from `requirements.txt` (`clingo`, `fastapi`, `uvicorn`, `websockets`, `pydantic`, `pyyaml`).
- Install all frontend Node.js dependencies in `frontend/` (`vue`, `tailwindcss@4`, `@tanstack/vue-table`, `radix-vue`, `@lucide/vue`, `pinia`).

---

## 2. Manual Installation Steps

If you prefer to set up the environment manually:

### Backend Setup
```powershell
# Create virtual environment
python -m venv .venv312

# Activate virtual environment
.\.venv312\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt
```

### Frontend Setup
```powershell
# Navigate to frontend directory
cd frontend

# Install npm packages
npm install
```

---

## 3. Configuration (`app_config.yaml`)

Edit `app_config.yaml` in the root folder to customize ports, host addresses, or storage locations:

```yaml
server:
  host: "127.0.0.1"
  backend_port: 8000
  frontend_port: 5173
  reload: true

paths:
  data_dir: "data"
  schedules_dir: "data/schedules"
  settings_file: "data/settings.json"
```

---

## 4. Running Development Servers

Launch both the FastAPI backend server and Vite frontend dev server concurrently:

```powershell
.\scripts\dev.ps1
```

Access the application in your web browser:
- **Frontend GUI:** `http://127.0.0.1:5173`
- **FastAPI REST API Docs:** `http://127.0.0.1:8000/docs`
- **WebSocket Endpoint:** `ws://127.0.0.1:8000/api/ws`

---

## 5. Running Tests & CLI Tools

### Unit Tests
```powershell
.\.venv312\Scripts\python -m unittest discover -s test
```

### Preserved CLI Runner
```powershell
.\.venv312\Scripts\python cli/runner.py --time-limit 10 --year 2026 --auto-festivities --csv data/schedules/schedule_2026.csv
```

---

## 6. Docker Container Deployment

You can build and run the entire application (Backend FastAPI + Frontend SPA) inside a Docker container.

### Build Docker Image
```powershell
.\scripts\docker-build.ps1
```

### Launch Container
```powershell
.\scripts\docker-run.ps1
```

### Volume Isolation Options
- **Internal Managed Volume (Isolated)**: By default, `docker-compose.yml` mounts a dedicated internal Docker volume `pharmacy_data:/app/data` (declared with `VOLUME ["/app/data"]` in `Dockerfile`). This keeps application settings and generated schedules completely isolated within Docker container storage.
- **Host Bind-Mount**: If you prefer direct access to local `./data` files on your host filesystem, uncomment `- ./data:/app/data` in `docker-compose.yml`.

### Automated GitHub Actions CI/CD
A GitHub Actions workflow is included at `.github/workflows/docker-publish.yml`. On every `push` to the `main` branch:
1. Docker image is automatically compiled (multi-stage frontend + ASP solver runner).
2. Image is published to **GitHub Container Registry (GHCR)** at `ghcr.io/<owner>/<repo>:latest` and tagged with the commit SHA.

When running in Docker, access points are logged to standard output:
- **Application Web UI:** `http://localhost:8001/`
- **FastAPI REST API Docs:** `http://localhost:8001/docs`
- **REST API Base:** `http://localhost:8001/api`

