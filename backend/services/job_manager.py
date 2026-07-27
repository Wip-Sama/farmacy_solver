import sys
import os
import asyncio
import logging
import time
from datetime import datetime, date
from typing import Optional, Set, Any, List
from fastapi import WebSocket

from core.config import ASP_DIR, SCHEDULES_DIR
from core.runner_core import (
    parse_festivities,
    parse_week_param,
    get_week_number_for_date,
    generate_dynamic_constraints,
    run_clingo,
)
from core.terminal_display import parse_schedule, generate_csv_report
from backend.schemas.ws import WSEvent
from backend.schemas.schedule import ScheduleMetaSchema
from backend.services.storage import save_schedule_metadata, get_settings

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
        self.current_task: Optional[asyncio.Task] = None

    async def start_job(
        self,
        year: int = 2026,
        time_limit: int = 60,
        auto_festivities: bool = True,
        base: str = "choice",
        opt: str = "penalita_esponenziale",
        reschedule_from: Optional[Any] = None,
        use_previous_year: bool = True,
        first_day_of_week: str = "sunday",
        custom_pharmacies: Optional[List[Any]] = None,
        custom_festivities: Optional[List[Any]] = None,
        pharmacy_preferences: Optional[List[Any]] = None,
    ) -> str:
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
        self.current_task = asyncio.create_task(self._run_solver_task(
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
        ))
        return job_id

    async def cancel_current_job(self) -> bool:
        if not self.is_running or not self.current_task:
            return False
        
        logging.info(f"Cancelling active job {self.current_job_id}...")
        self.current_task.cancel()
        await ws_manager.broadcast(WSEvent(
            type="JOB_FAILED",
            payload={
                "job_id": self.current_job_id or "job",
                "year": 2026,
                "error": "Job generation cancelled by user."
            }
        ))
        self.is_running = False
        self.current_job_id = None
        self.current_task = None
        return True


    async def _run_solver_task(
        self,
        job_id: str,
        year: int,
        time_limit: int,
        auto_festivities: bool,
        base: str,
        opt: str,
        reschedule_from: Optional[Any] = None,
        use_previous_year: bool = True,
        first_day_of_week: str = "sunday",
        custom_pharmacies: Optional[List[Any]] = None,
        custom_festivities: Optional[List[Any]] = None,
        pharmacy_preferences: Optional[List[Any]] = None,
    ):
        start_time = time.time()
        csv_filename = f"schedule_{year}.csv"
        output_csv_path = str(SCHEDULES_DIR / csv_filename)
        settings = get_settings()

        try:
            # 1. Parse festivities & custom user festivities
            await ws_manager.broadcast(WSEvent(
                type="JOB_PROGRESS",
                payload={"line": f"Calculating festivities and date bounds for year {year}..."}
            ))
            festivities_dict = parse_festivities(None, auto_festivities, year)

            cust_list = custom_festivities if custom_festivities is not None else settings.custom_festivities
            for cust_fest in cust_list:
                name = cust_fest.name if hasattr(cust_fest, 'name') else (cust_fest.get('name') if isinstance(cust_fest, dict) else str(cust_fest))
                raw_d = cust_fest.date if hasattr(cust_fest, 'date') else (cust_fest.get('date', '') if isinstance(cust_fest, dict) else '')
                d_str = raw_d.strip() if raw_d else ""

                if not d_str:
                    if not auto_festivities:
                        raise ValueError(f"Cannot generate schedule: Festivity '{name}' is missing a date while auto festivities is disabled.")
                    continue

                try:
                    if "/" in d_str:
                        parts = d_str.split("/")
                        d_obj = date(year, int(parts[1]), int(parts[0]))
                    elif "-" in d_str:
                        d_obj = datetime.strptime(d_str, "%Y-%m-%d").date()
                    else:
                        if not auto_festivities:
                            raise ValueError(f"Cannot generate schedule: Festivity '{name}' has invalid date format '{d_str}' while auto festivities is disabled.")
                        continue
                    festivities_dict[d_obj] = name
                except ValueError:
                    raise
                except Exception as e:
                    if not auto_festivities:
                        raise ValueError(f"Cannot generate schedule: Festivity '{name}' has invalid date format '{d_str}' while auto festivities is disabled.")
                    logging.warning(f"Skipping invalid custom festivity date '{d_str}': {e}")

            # 2. History file check (previous year)
            prev_year_csv = None
            if use_previous_year:
                prev_file = SCHEDULES_DIR / f"schedule_{year - 1}.csv"
                if prev_file.exists():
                    prev_year_csv = str(prev_file)

            # 3. Rescheduling week/date bounds
            res_csv = None
            res_from_week = None
            if reschedule_from:
                try:
                    res_from_week = parse_week_param(reschedule_from, year=year, first_day_of_week=first_day_of_week)
                except Exception as e:
                    logging.warning(f"Invalid reschedule_from format '{reschedule_from}': {e}")

                if res_from_week and res_from_week > 1:
                    curr_file = SCHEDULES_DIR / f"schedule_{year}.csv"
                    if curr_file.exists():
                        res_csv = str(curr_file)

            # 4. Pharmacy preferences (unavailabilities)
            unavailables = []
            pref_list = pharmacy_preferences if pharmacy_preferences is not None else settings.pharmacy_preferences
            for pref in pref_list:
                state = pref.state if hasattr(pref, 'state') else (pref.get('state', 'Closed') if isinstance(pref, dict) else 'Closed')
                raw_d = pref.date if hasattr(pref, 'date') else (pref.get('date', '') if isinstance(pref, dict) else '')
                pharm_id = pref.pharmacy_id if hasattr(pref, 'pharmacy_id') else (pref.get('pharmacy_id') if isinstance(pref, dict) else None)
                if state in ["Closed", "Preferably Closed"] and raw_d and pharm_id:
                    d_str = raw_d.strip()
                    try:
                        if "/" in d_str:
                            parts = d_str.split("/")
                            d_obj = date(year, int(parts[1]), int(parts[0]))
                        elif "-" in d_str:
                            d_obj = datetime.strptime(d_str, "%Y-%m-%d").date()
                        else:
                            continue
                        w_num = get_week_number_for_date(d_obj, year=year, first_day_of_week=first_day_of_week)
                        unavailables.append(f"{pharm_id},{w_num}")
                    except Exception as e:
                        logging.warning(f"Skipping invalid preference date '{d_str}': {e}")

            # 5. Generate dynamic constraints
            dynamic_file = generate_dynamic_constraints(
                reschedule_csv=res_csv,
                reschedule_from=res_from_week,
                unavailables=unavailables if unavailables else None,
                unavailable_intervals=None,
                start_week=1,
                end_week=52,
                festivities_dict=festivities_dict,
                prev_year_csv=prev_year_csv,
                first_day_of_week=first_day_of_week,
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

            main_loop = asyncio.get_running_loop()
            def on_progress(log_line: str):
                asyncio.run_coroutine_threadsafe(
                    ws_manager.broadcast(WSEvent(type="JOB_PROGRESS", payload={"line": log_line})),
                    main_loop
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

            # 6. Parse schedule & save CSV
            schedule, festivo_schedule = parse_schedule(asp_output)
            generate_csv_report(
                schedule,
                output_csv_path,
                year=year,
                csv_mode="compact",
                festivo_schedule=festivo_schedule,
                festivities_dict=festivities_dict,
                first_day_of_week=first_day_of_week
            )

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

        except asyncio.CancelledError:
            logging.warning(f"Solver job {job_id} was cancelled.")
        except Exception as e:
            logging.error(f"Solver job {job_id} failed: {e}")
            await ws_manager.broadcast(WSEvent(
                type="JOB_FAILED",
                payload={"job_id": job_id, "year": year, "error": str(e)}
            ))
        finally:
            self.is_running = False
            self.current_job_id = None
            self.current_task = None


job_manager = JobManager()

