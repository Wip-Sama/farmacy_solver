import sys
import os
import unittest
import json
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app
from backend.services.job_manager import job_manager
from backend.services.storage import get_settings, save_settings
from backend.services.export_service import generate_schedule_png
from core.config import SCHEDULES_DIR


class TestBackendFrontendIntegration(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_root_endpoint(self):
        res = self.client.get("/api")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("Pharmacy", data["app"])
        self.assertEqual(data["status"], "running")

    def test_settings_persistence(self):
        # Read current settings
        res = self.client.get("/api/settings")
        self.assertEqual(res.status_code, 200)
        initial = res.json()

        # Update settings with custom festivities & preferences
        initial["time_limit"] = 55
        initial["first_day_of_week"] = "monday"
        initial["custom_festivities"] = [{"name": "Festa di Prova", "date": "15/08"}]
        initial["pharmacy_preferences"] = [{"pharmacy_id": 2, "date": "15/08", "state": "Closed"}]

        put_res = self.client.put("/api/settings", json=initial)
        self.assertEqual(put_res.status_code, 200)
        updated = put_res.json()
        self.assertEqual(updated["time_limit"], 55)
        self.assertEqual(updated["first_day_of_week"], "monday")
        self.assertEqual(len(updated["custom_festivities"]), 1)

    def test_schedule_rows_contain_festivities_and_pharmacies(self):
        res = self.client.get("/api/schedules/2026?mode=compact")
        self.assertEqual(res.status_code, 200)
        rows = res.json()
        self.assertIsInstance(rows, list)
        if len(rows) > 0:
            first_row = rows[0]
            self.assertIn("week", first_row)
            self.assertIn("date", first_row)
            self.assertIn("festivity", first_row)
            self.assertIn("pharmacies", first_row)
            self.assertIn("status", first_row)
            self.assertIsInstance(first_row["pharmacies"], list)

    def test_trigger_schedule_generation_payload(self):
        payload = {
            "year": 2026,
            "time_limit": 10,
            "auto_festivities": True,
            "reschedule_from": "15",
            "use_previous_year": True,
            "first_day_of_week": "sunday"
        }
        res = self.client.post("/api/schedules/generate", json=payload)
        # Should start job or conflict if job already running
        self.assertIn(res.status_code, [202, 409])
        if res.status_code == 202:
            data = res.json()
            self.assertEqual(data["status"], "job_started")
            self.assertTrue(data["job_id"].startswith("job_2026_"))

    def test_export_csv_and_png(self):
        for mode_type in ["tiny", "compact", "normal", "extended"]:
            for orient in ["horizontal", "vertical"]:
                # Test CSV Export
                res_csv = self.client.get(f"/api/schedules/2026/export?format=csv&type={mode_type}&orientation={orient}")
                self.assertIn(res_csv.status_code, [200, 404])
                if res_csv.status_code == 200:
                    self.assertEqual(res_csv.headers["content-type"], "text/csv; charset=utf-8")
                    self.assertGreater(len(res_csv.content), 20)

                # Test PNG Export
                res_png = self.client.get(f"/api/schedules/2026/export?format=png&type={mode_type}&orientation={orient}")
                self.assertIn(res_png.status_code, [200, 404])
                if res_png.status_code == 200:
                    self.assertEqual(res_png.headers["content-type"], "image/png")
                    self.assertGreater(len(res_png.content), 100)

    def test_png_generator_direct(self):
        sample_rows = [
            {
                "week": 1,
                "date": "2026-01-04",
                "festivity": "Capodanno",
                "pharmacies": [{"id": 1, "name": "MONTORO", "location": "centro"}],
                "status": "future"
            }
        ]
        for mode in ["tiny", "compact", "normal", "extended"]:
            for orient in ["vertical", "horizontal"]:
                for label in ["names", "ids"]:
                    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                        tmp_path = tmp.name

                    try:
                        generate_schedule_png(
                            2026, sample_rows, tmp_path,
                            mode=mode, orientation=orient, pharmacy_label=label,
                            pharmacy_name_map={1: "MONTORO", 2: "BUCCARELLI"}
                        )
                        self.assertTrue(os.path.exists(tmp_path))
                        self.assertGreater(os.path.getsize(tmp_path), 200)
                    finally:
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)

    def test_validation_blocks_when_auto_festivities_disabled_and_missing_date(self):
        payload = {
            "year": 2026,
            "auto_festivities": False,
            "custom_festivities": [{"name": "Missing Date Festivity", "date": ""}]
        }
        res = self.client.post("/api/schedules/generate", json=payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn("missing a date", res.json()["detail"])

    def test_use_previous_year_and_auto_festivities_persistence(self):
        res = self.client.get("/api/settings")
        self.assertEqual(res.status_code, 200)
        current = res.json()

        # Toggle values
        current["use_previous_year"] = False
        current["auto_festivities"] = False
        put_res = self.client.put("/api/settings", json=current)
        self.assertEqual(put_res.status_code, 200)

        # Re-fetch settings
        refetch = self.client.get("/api/settings").json()
        self.assertEqual(refetch["use_previous_year"], False)
        self.assertEqual(refetch["auto_festivities"], False)

        # Restore defaults
        current["use_previous_year"] = True
        current["auto_festivities"] = True
        self.client.put("/api/settings", json=current)

    def test_cancel_schedule_generation(self):
        # Cancel when no job running returns 400
        res_no_job = self.client.post("/api/schedules/cancel")
        self.assertEqual(res_no_job.status_code, 400)


if __name__ == "__main__":
    unittest.main()

