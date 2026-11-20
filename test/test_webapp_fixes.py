import asyncio
import os
import sys
import tempfile
import threading
import time
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient

import backend.services.storage as storage_service
from backend.main import app
from backend.schemas.schedule import ScheduleGenerateRequest, ScheduleMetaSchema
from backend.schemas.ws import WSEvent
from backend.services.export_service import generate_schedule_png
from backend.services.job_manager import JobManager
from core.config import ASP_DIR
from core.csv_utils import generate_csv_report
from core.date_utils import parse_custom_date, resolve_festivities_dict
from core.file_utils import atomic_write_path
from core.runner_core import generate_dynamic_constraints, run_clingo


class TestWebappFixes(unittest.TestCase):
    def test_ws_event_timestamp_uses_default_factory(self):
        e1 = WSEvent(type="JOB_STARTED")
        time.sleep(0.01)
        e2 = WSEvent(type="JOB_COMPLETED")
        self.assertNotEqual(e1.timestamp, e2.timestamp)

    def test_health_and_unknown_api_route_behavior(self):
        client = TestClient(app)
        res_health = client.get("/api/health")
        self.assertEqual(res_health.status_code, 200)
        self.assertEqual(res_health.json(), {"status": "ok"})

        res_missing_api = client.get("/api/nonexistent-endpoint")
        self.assertEqual(res_missing_api.status_code, 404)

    def test_schedule_generate_request_preserves_none_overrides(self):
        req = ScheduleGenerateRequest(year=2026)
        self.assertIsNone(req.time_limit)
        self.assertIsNone(req.auto_festivities)
        self.assertIsNone(req.use_previous_year)
        self.assertIsNone(req.first_day_of_week)

    def test_parse_custom_date_and_resolve_festivities(self):
        self.assertEqual(parse_custom_date("15/08", 2026), date(2026, 8, 15))
        self.assertEqual(parse_custom_date("29/02", 2028), date(2028, 2, 29))
        self.assertEqual(parse_custom_date("2026-12-25", 2026), date(2026, 12, 25))

        fest_dict = resolve_festivities_dict(
            year=2026,
            auto_festivities=False,
            custom_festivities=[{"name": "Patrono", "date": "25/05"}],
            strict=True,
        )
        self.assertEqual(fest_dict, {date(2026, 5, 25): "Patrono"})

        with self.assertRaises(ValueError):
            resolve_festivities_dict(
                year=2026,
                auto_festivities=False,
                custom_festivities=[{"name": "NoDate", "date": ""}],
                strict=True,
            )

    def test_generate_png_compact_supports_more_than_ten_pharmacies(self):
        rows = [
            {
                "week": 1,
                "date": "2026-01-05",
                "festivity": None,
                "pharmacies": [
                    {"id": 1, "name": "MONTORO", "location": "centro"},
                    {"id": 11, "name": "NUOVA11", "location": "marina"},
                ],
                "status": "future",
            }
        ]
        name_map = {i: f"PH{i}" for i in range(1, 12)}
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            generate_schedule_png(
                year=2026,
                rows=rows,
                output_path=tmp_path,
                mode="compact",
                orientation="vertical",
                pharmacy_label="names",
                pharmacy_name_map=name_map,
            )
            self.assertTrue(os.path.exists(tmp_path))
            self.assertGreater(os.path.getsize(tmp_path), 200)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_preference_states_generate_expected_asp_constraints(self):
        dyn_file = generate_dynamic_constraints(
            start_week=1,
            end_week=2,
            year=2026,
            force_open=["1,1"],
            force_closed=["2,1"],
            pref_open=["3,2"],
            pref_closed=["4,2"],
        )
        try:
            with open(dyn_file, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn(":- not turno(1, 1).", content)
            self.assertIn(":- turno(1, 2).", content)
            self.assertIn(":~ not turno(2, 3). [10@2, 3, 2]", content)
            self.assertIn(":~ turno(2, 4). [10@2, 4, 2]", content)
        finally:
            if os.path.exists(dyn_file):
                os.remove(dyn_file)

    def test_job_manager_maps_frontend_preference_states_and_cancels(self):
        captured_kwargs = {}

        def fake_generate_dynamic_constraints(**kwargs):
            captured_kwargs.update(kwargs)
            fd, p = tempfile.mkstemp(suffix=".lp", text=True)
            os.close(fd)
            return p

        def fake_run_clingo(*args, cancel_event=None, **kwargs):
            # Block briefly until cancelled or return empty
            while cancel_event is not None and not cancel_event.is_set():
                time.sleep(0.05)
            return "", 0

        async def run_test():
            jm = JobManager()
            with (
                patch("backend.services.job_manager.generate_dynamic_constraints", side_effect=fake_generate_dynamic_constraints),
                patch("backend.services.job_manager.run_clingo", side_effect=fake_run_clingo),
            ):
                await jm.start_job(
                    year=2026,
                    time_limit=10,
                    pharmacy_preferences=[
                        {"pharmacy_id": 1, "date": "05/01", "state": "Open"},
                        {"pharmacy_id": 2, "date": "05/01", "state": "Closed"},
                        {"pharmacy_id": 3, "date": "12/01", "state": "Preferably Open"},
                        {"pharmacy_id": 4, "date": "12/01", "state": "Preferably Closed"},
                    ],
                )
                await asyncio.sleep(0.1)
                cancelled = await jm.cancel_current_job()
                self.assertTrue(cancelled)
                self.assertFalse(jm.is_running)

            self.assertEqual(captured_kwargs["force_open"], ["1,1"])
            self.assertEqual(captured_kwargs["force_closed"], ["2,1"])
            self.assertEqual(captured_kwargs["pref_open"], ["3,2"])
            self.assertEqual(captured_kwargs["pref_closed"], ["4,2"])

        asyncio.run(run_test())

    def test_run_clingo_respects_cancel_event(self):
        dyn_file = generate_dynamic_constraints(start_week=1, end_week=52, year=2026)
        cancel_event = threading.Event()
        cancel_event.set()
        try:
            output, count = run_clingo(
                str(ASP_DIR / "domain.lp"),
                str(ASP_DIR / "guess_choice.lp"),
                str(ASP_DIR / "constraints.lp"),
                str(ASP_DIR / "optimizations" / "penalita_esponenziale.lp"),
                dynamic_file=dyn_file,
                time_limit=10,
                year=2026,
                cancel_event=cancel_event,
            )
            self.assertEqual(output, "")
            self.assertEqual(count, 0)
        finally:
            if os.path.exists(dyn_file):
                os.remove(dyn_file)

    def test_atomic_write_preserves_existing_file_on_error_and_leaves_no_tmp(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "data.json"
            target.write_text('{"ok": true}', encoding="utf-8")

            with self.assertRaises(RuntimeError):
                with atomic_write_path(target) as tmp_path:
                    tmp_path.write_text('{"corrupt":', encoding="utf-8")
                    raise RuntimeError("simulated crash")

            self.assertEqual(target.read_text(encoding="utf-8"), '{"ok": true}')
            self.assertEqual(list(Path(tmp_dir).glob("*.tmp")), [])

    def test_save_metadata_and_csv_atomic_writes_and_missing_fallbacks(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            sched_dir = Path(tmp_dir) / "schedules"
            sched_dir.mkdir(parents=True, exist_ok=True)
            csv_path = sched_dir / "schedule_2098.csv"
            generate_csv_report({1: [1, 7]}, str(csv_path), year=2098, csv_mode="compact")
            self.assertTrue(csv_path.exists())
            self.assertEqual(list(sched_dir.glob("*.tmp")), [])

            with (
                patch.object(storage_service, "SCHEDULES_DIR", sched_dir),
                patch.object(storage_service, "PROJECT_ROOT", Path(tmp_dir)),
            ):
                # Missing .meta.json falls back cleanly using CSV mtime
                listed = storage_service.list_schedules()
                self.assertEqual(len(listed), 1)
                self.assertEqual(listed[0]["year"], 2098)
                self.assertIsNone(listed[0]["execution_time_seconds"])

                # Save metadata atomically and confirm no .tmp left behind
                meta = ScheduleMetaSchema(
                    year=2098,
                    filename="schedule_2098.csv",
                    generated_at="2026-11-20T12:00:00",
                    execution_time_seconds=1.5,
                )
                storage_service.save_schedule_metadata(2098, meta)
                self.assertTrue((sched_dir / "schedule_2098.meta.json").exists())
                self.assertEqual(list(sched_dir.glob("*.tmp")), [])

                # Missing CSV returns empty list in get_schedule_rows
                self.assertEqual(storage_service.get_schedule_rows(2099), [])

        client = TestClient(app)
        res_export = client.get("/api/schedules/2099/export")
        self.assertEqual(res_export.status_code, 404)


if __name__ == "__main__":
    unittest.main()
