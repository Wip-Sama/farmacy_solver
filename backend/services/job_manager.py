import sys
import os
import asyncio
import logging
import time
from datetime import datetime
from typing import Optional, Set
from fastapi import WebSocket

from core.config import ASP_DIR, SCHEDULES_DIR
from core.runner_core import (
    parse_festivities,
    generate_dynamic_constraints,
    run_clingo,
)
from core.terminal_display import parse_schedule, generate_csv_report
from backend.schemas.ws import WSEvent
from backend.schemas.schedule import ScheduleMetaSchema
from backend.services.storage import save_schedule_metadata

class ConnectionManager:
    """Manages active WebSocket client connections and broadcasts events."""
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logging.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logging.info(f"WebSocket client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast(self, event: WSEvent):
        if not self.active_connections:
            return
        message = event.model_dump_json()
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logging.warning(f"Failed to send to client: {e}")
                disconnected.add(connection)
        for conn in disconnected:
            self.active_connections.remove(conn)

ws_manager = ConnectionManager()

class JobManager:
    """Async single-job concurrency lock & background ASP solver execution engine."""
    def __init__(self):
        self.is_running: bool = False
        self.current_job_id: Optional[str] = None
        self.started_at: Optional[datetime] = None

    async def start_job(self, year: int = 2026, time_limit: int = 60, auto_festivities: bool = True, base: str = "choice", opt: str = "penalita_esponenziale") -> str:
        if self.is_running:
            raise RuntimeError("A scheduling job is already in progress.")

        self.is_running = True
        job_id = f"job_{year}_{int(time.time())}"
        self.current_job_id = job_id
        self.started_at = datetime.now()

        # Broadcast JOB_STARTED to all open browser tabs
        await ws_manager.broadcast(WSEvent(
            type="JOB_STARTED",
            payload={
                "job_id": job_id,
                "year": year,
                "time_limit": time_limit,
                "message": f"Generating schedule for {year}..."
            }
        ))

        # Launch background task
        asyncio.create_task(self._run_solver_task(job_id, year, time_limit, auto_festivities, base, opt))
        return job_id

    async def _run_solver_task(self, job_id: str, year: int, time_limit: int, auto_festivities: bool, base: str, opt: str):
        start_time = time.time()
        csv_filename = f"schedule_{year}.csv"
        output_csv_path = str(SCHEDULES_DIR / csv_filename)

        try:
            # 1. Parse festivities
            await ws_manager.broadcast(WSEvent(
                type="JOB_PROGRESS",
                payload={"line": f"Calculating festivities and date bounds for year {year}..."}
            ))
            festivities_dict = parse_festivities(None, auto_festivities, year)

            # 2. Generate dynamic constraints
            dynamic_file = generate_dynamic_constraints(
                reschedule_csv=None,
                reschedule_from=None,
                unavailables=None,
                unavailable_intervals=None,
                start_week=1,
                end_week=52,
                festivities_dict=festivities_dict,
                year=year
            )

            domain_file = str(ASP_DIR / "domain.lp")
            guess_file = str(ASP_DIR / f"guess_{base}.lp")
            constraints_file = str(ASP_DIR / "constraints.lp")
            opt_file = str(ASP_DIR / "optimizations" / f"{opt}.lp")

            await ws_manager.broadcast(WSEvent(
                type="JOB_PROGRESS",
                payload={"line": f"Invoking Clingo ASP solver (Time limit: {time_limit}s)..."}
            ))

            # Progress log callback
            def on_progress(log_line: str):
                asyncio.run_coroutine_threadsafe(
                    ws_manager.broadcast(WSEvent(type="JOB_PROGRESS", payload={"line": log_line})),
                    asyncio.get_event_loop()
                )

            # Run solver in thread to avoid blocking main async loop
            asp_output, num_solutions = await asyncio.to_thread(
                run_clingo,
                domain_file, guess_file, constraints_file, opt_file,
                dynamic_file=dynamic_file,
                live=True,
                time_limit=time_limit,
                year=year,
                on_model_cb=lambda m, sol, t: on_progress(f"Solution #{sol} found in {t:.2f}s!")
            )

            # Clean up dynamic file
            if os.path.exists(dynamic_file):
                os.remove(dynamic_file)

            if not asp_output or not asp_output.strip():
                raise RuntimeError("Solver produced no solution (UNSATISFIABLE or timeout).")

            # 3. Parse schedule & save CSV
            schedule, festivo_schedule = parse_schedule(asp_output)
            generate_csv_report(schedule, output_csv_path, year=year, csv_mode="compact", festivo_schedule=festivo_schedule)

            elapsed_seconds = round(time.time() - start_time, 2)
            meta = ScheduleMetaSchema(
                year=year,
                filename=csv_filename,
                generated_at=datetime.now().isoformat(),
                solver="clingo",
                execution_time_seconds=elapsed_seconds,
                cost_value="Completed",
                is_locked=False
            )
            save_schedule_metadata(year, meta)

            # Broadcast JOB_COMPLETED to all open browser tabs
            await ws_manager.broadcast(WSEvent(
                type="JOB_COMPLETED",
                payload={
                    "job_id": job_id,
                    "year": year,
                    "filename": csv_filename,
                    "execution_time_seconds": elapsed_seconds,
                    "message": f"Schedule for {year} successfully generated!"
                }
            ))

        except Exception as e:
            logging.error(f"Solver job {job_id} failed: {e}")
            await ws_manager.broadcast(WSEvent(
                type="JOB_FAILED",
                payload={"job_id": job_id, "year": year, "error": str(e)}
            ))
        finally:
            self.is_running = False
            self.current_job_id = None

job_manager = JobManager()
