# Technical Architecture & System Overview

This document provides a technical specification of the Pharmacy Scheduling System (`farmacy_solver`), explaining its hybrid ASP solver pipeline, real-time FastAPI WebSocket synchronization engine, file-based persistence model, and Vue 3 frontend architecture.

---

## 1. System Overview

The system uses a 3-tier hybrid architecture:

```
+-------------------------------------------------------------------+
|               Vue 3 + Tailwind CSS v4 Frontend                    |
|  - TopControls, FestivitiesTable, PreferencesTable, ScheduleView |
|  - Toast Notification Indicator (vue-sonner) during scheduling    |
|  - Pinia Stores with Zero-Polling WebSocket Synchronization       |
+---------------------------------+---------------------------------+
                                  |
               WebSocket / REST   |   (Port 8000 / Port 5173)
                                  v
+-------------------------------------------------------------------+
|                     FastAPI Backend Layer                         |
|  - REST Routes (/api/settings, /api/schedules)                    |
|  - Real-Time Connection Manager & WS Broadcast Server (/api/ws)   |
|  - Async Single-Job Concurrency Lock (JobManager)                |
+---------------------------------+---------------------------------+
                                  |
                   Python Import  |   (core.runner_core)
                                  v
+-------------------------------------------------------------------+
|                    Core ASP Engine & Solvers                      |
|  - Dynamic ASP Code Generator (runner_core.py)                    |
|  - Clingo / DLV Solvers (core/asp/*.lp)                           |
|  - Schedule CSV & Metadata Serialization (csv_utils.py)           |
+-------------------------------------------------------------------+
```

---

## 2. Component Layers

### 2.1 Core ASP & Logic Engine (`core/`)
* **`core/config.py`**: Centralized configuration resolver that reads `app_config.yaml` and dynamically calculates workspace paths (`PROJECT_ROOT`, `ASP_DIR`, `DATA_DIR`, `SCHEDULES_DIR`).
* **`core/runner_core.py`**: Python engine that calculates date bounds, Easter and Italian national holidays, generates temporary ASP facts/rules (`.lp`), invokes the `clingo` Python API, and parses ASP answer set atoms (`turno/2`, `turno_festivo/2`).
* **`core/asp/*.lp`**: Declarative Answer Set Programming rule files:
  * `domain.lp`: Search space predicates (`farmacia`, `settimana`).
  * `constraints.lp`: Hard constraints (fairness, consecutive shift rules, summer marina rules).
  * `guess_choice.lp` & `guess_or.lp`: Choice rules for assignment search.
  * `optimizations/*.lp`: Soft optimization criteria (exponential gap penalty minimization).
* **`core/csv_utils.py` & `core/terminal_display.py`**: Data serialization layer for reading, writing, and formatting schedules into compact, normal, or extended CSV formats.

### 2.2 Backend Web Server (`backend/`)
* **`backend/main.py`**: FastAPI entry point configured via `app_config.yaml`. Sets up CORS middleware, static file routes, and WebSocket endpoints.
* **`backend/services/job_manager.py`**: Thread-safe async job state machine that enforces **Single-Job Concurrency Locking**. Rejects concurrent solver triggers (returning HTTP 409 Conflict) and streams solver output lines over WebSockets.
* **`backend/services/storage.py`**: Atomic JSON read/write service for `data/settings.json` and `data/schedules/*.meta.json` preventing file corruption during concurrent operations.

### 2.3 Frontend Application (`frontend/`)
* **Vite + Vue 3 (Composition API) + TypeScript**: Reactive Single Page Application styled with **Tailwind CSS v4** and custom neon/glowing card glassmorphism.
* **Zero-Polling Real-Time Sync**: Uses `@vueuse/core` `useWebSocket` to maintain a single persistent connection (`/api/ws`). Whenever any browser tab updates a setting or triggers a schedule, all connected tabs update instantly without polling.

---

## 3. Data Flow & Persistence

1. **User Settings**: Stored in `data/settings.json`. Contains year defaults, auto-festivities preference, solver time limits, and custom festivities/pharmacy preferences.
2. **Schedules**: Stored as `data/schedules/schedule_{year}.csv` alongside `data/schedules/schedule_{year}.meta.json` (storing execution time, solver used, cost value, generation timestamp).
