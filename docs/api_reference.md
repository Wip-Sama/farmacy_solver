# API Reference & WebSocket Protocol Specification

This document details all REST API endpoints and real-time WebSocket event protocols exposed by the FastAPI backend server (`backend/`).

---

## 1. REST Endpoints

### 1.1 Settings Management

#### `GET /api/settings`
Returns current user preferences and solver configuration from `data/settings.json`.

* **Response (200 OK):**
  ```json
  {
    "year": 2026,
    "use_previous_year": true,
    "first_day_of_week": "sunday",
    "auto_festivities": true,
    "time_limit": 60,
    "reschedule_from": null,
    "custom_festivities": [
      { "name": "Pasqua", "date": "2026-04-05" }
    ],
    "pharmacy_preferences": [
      { "pharmacy_id": 1, "date": "2026-12-25", "state": "Closed" }
    ]
  }
  ```

#### `PUT /api/settings`
Updates user preferences, writes atomically to `data/settings.json`, and broadcasts `SETTINGS_UPDATED` WebSocket event to all connected clients.

* **Request Body:** `SettingsSchema` JSON object.
* **Response (200 OK):** `{"status": "success", "settings": {...}}`

---

### 1.2 Schedule Operations

#### `GET /api/schedules`
Lists all available generated schedule files in `data/schedules/` alongside metadata.

* **Response (200 OK):**
  ```json
  [
    {
      "year": 2026,
      "filename": "schedule_2026.csv",
      "generated_at": "2026-07-27T15:30:00Z",
      "solver": "clingo",
      "execution_time_seconds": 14.2,
      "cost_value": "13450"
    }
  ]
  ```

#### `GET /api/schedules/{year}`
Returns parsed weekly schedule rows for table rendering in the Vue GUI.

* **Query Parameters:** `mode` (`compact` | `extended`, default: `compact`)
* **Response (200 OK):** Parsed schedule grid rows with holiday names and assigned pharmacies.

#### `POST /api/schedules/generate`
Triggers an ASP solver job for the specified year. Enforces the **Single-Job Concurrency Lock**.

* **Request Body:**
  ```json
  {
    "year": 2026,
    "time_limit": 60,
    "auto_festivities": true,
    "reschedule_from": "15",
    "regenerate_from": null,
    "use_previous_year": true,
    "first_day_of_week": "sunday"
  }
  ```
* **Response (202 Accepted):** `{"status": "job_started", "job_id": "job_2026_1722095400"}`
* **Error Response (400 Bad Request):** `{"detail": "Cannot generate schedule: Festivity '...' is missing a date while auto festivities is disabled."}`
* **Error Response (409 Conflict):** `{"detail": "A scheduling job is already running (Job ID: job_2026_...)"}`

#### `GET /api/schedules/{year}/export`
Generates and downloads a CSV or PNG schedule report file.

* **Query Parameters:**
  - `format` (`csv` | `png`, default: `csv`)
  - `orientation` (`horizontal` | `vertical`, default: `horizontal`)
  - `type` (`normal` | `compact` | `extended`, default: `normal`)
* **Response (200 OK):** Binary file stream (`text/csv` or `image/png`).

---

## 2. Real-Time WebSocket Engine (`ws://127.0.0.1:8001/api/ws`)

All Vue browser tabs connect to `/api/ws`. The server broadcasts JSON event envelopes matching this structure:

```json
{
  "type": "EVENT_TYPE",
  "timestamp": "2026-07-27T15:30:00Z",
  "payload": {}
}
```

### Event Types

| Event Type | Direction | Payload Description |
| :--- | :--- | :--- |
| `SETTINGS_UPDATED` | Server → All Clients | Broadcast when any tab saves settings. Contains new settings object. |
| `JOB_STARTED` | Server → All Clients | Broadcast when a solver run begins. Locks UI buttons globally. |
| `JOB_PROGRESS` | Server → All Clients | Streams solver stdout lines in real time (`{"line": "Grounding..."}`). |
| `JOB_COMPLETED` | Server → All Clients | Broadcast when solver finishes. Unlocks UI buttons and triggers schedule reload. |
| `JOB_FAILED` | Server → All Clients | Broadcast if solver crashes or fails. Contains error message. |

