import asyncio
import logging
import os
import threading
import time
from datetime import datetime
from typing import Any

from fastapi import WebSocket

from backend.schemas.schedule import ScheduleMetaSchema
from backend.schemas.ws import WSEvent
from backend.services.storage import get_settings, save_schedule_metadata
from core.config import ASP_DIR, SCHEDULES_DIR
from core.csv_utils import generate_csv_report
from core.date_utils import parse_custom_date, resolve_festivities_dict
from core.runner_core import (
    generate_dynamic_constraints,
    get_week_number_for_date,
    parse_week_param,
    run_clingo,
)
from core.terminal_display import parse_schedule


class ConnectionManager:
    """Manages active WebSocket client connections and broadcasts events."""

    def __init__(self):
        self.active_connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logging.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logging.info(f"WebSocket client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast(self, event: WSEvent):
        if not self.active_connections:
            return
        message = event.model_dump_json()
        disconnected = set()
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception as e:
                logging.warning(f"Failed to send to client: {e}")
                disconnected.add(connection)
        for conn in disconnected:
            self.active_connections.discard(conn)


ws_manager = ConnectionManager()


class JobManager:
    """Async single-job concurrency lock & background ASP solver execution engine."""

    def __init__(self):
        self.is_running: bool = False
        self.current_job_id: str | None = None
        self.current_year: int = 2026
        self.started_at: datetime | None = None
        self.current_task: asyncio.Task | None = None
        self.cancel_event: threading.Event | None = None

    async def start_job(
        self,
        year: int = 2026,
        time_limit: int = 55,
        auto_festivities: bool = True,
        base: str = "choice",
        opt: str = "penalita_esponenziale",
        reschedule_from: Any | None = None,
        use_previous_year: bool = True,
        first_day_of_week: str = "monday",
        custom_pharmacies: list[Any] | None = None,
        custom_festivities: list[Any] | None = None,
        pharmacy_preferences: list[Any] | None = None,
    ) -> str:
        if self.is_running:
            raise RuntimeError("A scheduling job is already in progress.")

        self.is_running = True
        job_id = f"job_{year}_{int(time.time())}"
        self.current_job_id = job_id
        self.current_year = year
        self.started_at = datetime.now()
        self.cancel_event = threading.Event()

        await ws_manager.broadcast(
            WSEvent(
                type="JOB_STARTED",
                payload={
                    "job_id": job_id,
                    "year": year,
                    "time_limit": time_limit,
                    "message": f"Generating schedule for {year}...",
                },
            )
        )

        self.current_task = asyncio.create_task(
            self._run_solver_task(
                job_id=job_id,
                year=year,
                time_limit=time_limit,
                auto_festivities=auto_festivities,
                base=base,
                opt=opt,
                reschedule_from=reschedule_from,
                use_previous_year=use_previous_year,
                first_day_of_week=first_day_of_week,
                custom_pharmacies=custom_pharmacies,
                custom_festivities=custom_festivities,
                pharmacy_preferences=pharmacy_preferences,
                cancel_event=self.cancel_event,
            )
        )
        return job_id

    async def cancel_current_job(self) -> bool:
        if not self.is_running or not self.current_task:
            return False

        job_id = self.current_job_id or "job"
        year = self.current_year
        logging.info(f"Cancelling active job {job_id}...")

        if self.cancel_event is not None:
            self.cancel_event.set()

        task = self.current_task
        try:
            await asyncio.wait_for(asyncio.shield(task), timeout=2.0)
        except asyncio.TimeoutError:
            task.cancel()
        except asyncio.CancelledError:
            pass
        except Exception:
            pass

        await ws_manager.broadcast(
            WSEvent(
                type="JOB_FAILED",
                payload={
                    "job_id": job_id,
                    "year": year,
                    "error": "Job generation cancelled by user.",
                },
            )
        )
        self.is_running = False
        self.current_job_id = None
        self.current_task = None
        self.cancel_event = None
        return True

    async def _run_solver_task(
        self,
        job_id: str,
        year: int,
        time_limit: int,
        auto_festivities: bool,
        base: str,
        opt: str,
        reschedule_from: Any | None = None,
        use_previous_year: bool = True,
        first_day_of_week: str = "monday",
        custom_pharmacies: list[Any] | None = None,
        custom_festivities: list[Any] | None = None,
        pharmacy_preferences: list[Any] | None = None,
        cancel_event: threading.Event | None = None,
    ):
        start_time = time.time()
        csv_filename = f"schedule_{year}.csv"
        output_csv_path = str(SCHEDULES_DIR / csv_filename)
        settings = get_settings()
        dynamic_file: str | None = None

        try:
            await ws_manager.broadcast(
                WSEvent(
                    type="JOB_PROGRESS",
                    payload={"line": f"Calculating festivities and date bounds for year {year}..."},
                )
            )
            cust_list = custom_festivities if custom_festivities is not None else settings.custom_festivities
            festivities_dict = resolve_festivities_dict(
                year=year,
                auto_festivities=auto_festivities,
                custom_festivities=cust_list,
                strict=not auto_festivities,
            )

            prev_year_csv = None
            if use_previous_year:
                prev_file = SCHEDULES_DIR / f"schedule_{year - 1}.csv"
                if prev_file.exists():
                    prev_year_csv = str(prev_file)

            res_csv = None
            res_from_week = None
            if reschedule_from:
                try:
                    res_from_week = parse_week_param(
                        reschedule_from, year=year, first_day_of_week=first_day_of_week
                    )
                except Exception as e:
                    logging.warning(f"Invalid reschedule_from format '{reschedule_from}': {e}")

                if res_from_week and res_from_week > 1:
                    curr_file = SCHEDULES_DIR / f"schedule_{year}.csv"
                    if curr_file.exists():
                        res_csv = str(curr_file)

            force_open: list[str] = []
            force_closed: list[str] = []
            pref_open: list[str] = []
            pref_closed: list[str] = []

            pref_list = pharmacy_preferences if pharmacy_preferences is not None else settings.pharmacy_preferences
            for pref in pref_list:
                state = (
                    pref.state
                    if hasattr(pref, "state")
                    else (pref.get("state", "Closed") if isinstance(pref, dict) else "Closed")
                )
                raw_d = (
                    pref.date
                    if hasattr(pref, "date")
                    else (pref.get("date", "") if isinstance(pref, dict) else "")
                )
                pharm_id = (
                    pref.pharmacy_id
                    if hasattr(pref, "pharmacy_id")
                    else (pref.get("pharmacy_id") if isinstance(pref, dict) else None)
                )

                if raw_d and pharm_id is not None:
                    try:
                        d_obj = parse_custom_date(raw_d, year)
                        if d_obj is None:
                            continue
                        w_num = get_week_number_for_date(d_obj, year=year, first_day_of_week=first_day_of_week)
                        constraint_val = f"{pharm_id},{w_num}"

                        normalized_state = state.strip().lower()
                        if normalized_state in {"closed", "force closed"}:
                            force_closed.append(constraint_val)
                        elif normalized_state in {"open", "force open"}:
                            force_open.append(constraint_val)
                        elif normalized_state == "preferably open":
                            pref_open.append(constraint_val)
                        elif normalized_state == "preferably closed":
                            pref_closed.append(constraint_val)
                    except Exception as e:
                        logging.warning(f"Skipping invalid preference date '{raw_d}': {e}")

            pharmacies_str = None
            if custom_pharmacies:
                pharma_parts = []
                for p in custom_pharmacies:
                    p_id = (
                        p.id
                        if hasattr(p, "id")
                        else (p.get("id") if isinstance(p, dict) else getattr(p, "pharmacy_id", None))
                    )
                    p_location = (
                        p.location
                        if hasattr(p, "location")
                        else (p.get("location", "centro") if isinstance(p, dict) else "centro")
                    )
                    if p_id is not None:
                        pharma_parts.append(f"{p_id},{p_location}")
                if pharma_parts:
                    pharmacies_str = ";".join(pharma_parts)

            dynamic_file = generate_dynamic_constraints(
                reschedule_csv=res_csv,
                reschedule_from=res_from_week,
                start_week=1,
                end_week=52,
                festivities_dict=festivities_dict,
                prev_year_csv=prev_year_csv,
                first_day_of_week=first_day_of_week,
                year=year,
                pharmacies=pharmacies_str,
                force_open=force_open or None,
                force_closed=force_closed or None,
                pref_open=pref_open or None,
                pref_closed=pref_closed or None,
            )

            domain_file = str(ASP_DIR / "domain.lp")
            guess_file = str(ASP_DIR / f"guess_{base}.lp")
            constraints_file = str(ASP_DIR / "constraints.lp")
            opt_file = str(ASP_DIR / "optimizations" / f"{opt}.lp")

            await ws_manager.broadcast(
                WSEvent(
                    type="JOB_PROGRESS",
                    payload={"line": f"Solving schedule (time limit: {time_limit}s)..."},
                )
            )

            main_loop = asyncio.get_running_loop()

            def on_progress(log_line: str):
                asyncio.run_coroutine_threadsafe(
                    ws_manager.broadcast(WSEvent(type="JOB_PROGRESS", payload={"line": log_line})),
                    main_loop,
                )

            asp_output, _num_solutions = await asyncio.to_thread(
                run_clingo,
                domain_file,
                guess_file,
                constraints_file,
                opt_file,
                dynamic_file=dynamic_file,
                live=True,
                time_limit=time_limit,
                year=year,
                on_model_cb=lambda _m, _model_str, sol_num: on_progress(
                    f"Solution #{sol_num} found in {time.time() - start_time:.2f}s"
                ),
                cancel_event=cancel_event,
            )

            if cancel_event is not None and cancel_event.is_set():
                logging.info(f"Solver job {job_id} aborted due to user cancellation.")
                return

            if not asp_output or not asp_output.strip():
                raise RuntimeError("Solver produced no solution (UNSATISFIABLE or timeout).")

            schedule, festivo_schedule = parse_schedule(asp_output)
            SCHEDULES_DIR.mkdir(parents=True, exist_ok=True)
            generate_csv_report(
                schedule,
                output_csv_path,
                year=year,
                csv_mode="compact",
                festivo_schedule=festivo_schedule,
                festivities_dict=festivities_dict,
                first_day_of_week=first_day_of_week,
            )

            elapsed_seconds = round(time.time() - start_time, 2)
            meta = ScheduleMetaSchema(
                year=year,
                filename=csv_filename,
                generated_at=datetime.now().isoformat(),
                solver="clingo",
                execution_time_seconds=elapsed_seconds,
                cost_value="Completed",
                is_locked=False,
            )
            save_schedule_metadata(year, meta)

            await ws_manager.broadcast(
                WSEvent(
                    type="JOB_COMPLETED",
                    payload={
                        "job_id": job_id,
                        "year": year,
                        "filename": csv_filename,
                        "execution_time_seconds": elapsed_seconds,
                        "message": f"Schedule for {year} successfully generated!",
                    },
                )
            )

        except asyncio.CancelledError:
            logging.warning(f"Solver job {job_id} was cancelled.")
        except Exception as e:
            logging.error(f"Solver job {job_id} failed: {e}")
            await ws_manager.broadcast(
                WSEvent(
                    type="JOB_FAILED",
                    payload={"job_id": job_id, "year": year, "error": str(e)},
                )
            )
        finally:
            if dynamic_file and os.path.exists(dynamic_file):
                try:
                    os.remove(dynamic_file)
                except OSError:
                    pass
            if self.current_job_id == job_id:
                self.is_running = False
                self.current_job_id = None
                self.current_task = None
                self.cancel_event = None


job_manager = JobManager()
