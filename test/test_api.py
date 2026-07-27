import sys
import os
import unittest
import json
import tempfile
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app
from backend.services.storage import get_settings, save_settings
from backend.services.job_manager import job_manager
from backend.schemas.settings import SettingsSchema

class TestAPIEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_root_endpoint(self):
        response = self.client.get("/api")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "running")

    def test_get_and_put_settings(self):
        # GET Settings
        res_get = self.client.get("/api/settings")
        self.assertEqual(res_get.status_code, 200)
        settings_data = res_get.json()
        self.assertIn("year", settings_data)

        # PUT Settings
        settings_data["time_limit"] = 45
        res_put = self.client.put("/api/settings", json=settings_data)
        self.assertEqual(res_put.status_code, 200)
        updated = res_put.json()
        self.assertEqual(updated["time_limit"], 45)

    def test_list_schedules(self):
        res = self.client.get("/api/schedules")
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json(), list)

    def test_fetch_schedule_rows(self):
        res = self.client.get("/api/schedules/2026?mode=compact")
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json(), list)

    def test_single_job_concurrency_lock(self):
        # Simulate an already running solver job
        job_manager.is_running = True
        job_manager.current_job_id = "test_running_job"
        try:
            res = self.client.post("/api/schedules/generate", json={"year": 2026, "time_limit": 10})
            self.assertEqual(res.status_code, 409)
            self.assertIn("already running", res.json()["detail"])
        finally:
            job_manager.is_running = False
            job_manager.current_job_id = None

    def test_spa_static_files_and_fallback(self):
        # Test root / access returns status 200 (either SPA index.html or root API fallback if dist missing)
        res_root = self.client.get("/")
        self.assertEqual(res_root.status_code, 200)

        # Test deep SPA route like /settings falls back to 200 index.html when dist exists
        res_spa = self.client.get("/settings")
        self.assertEqual(res_spa.status_code, 200)

    def test_api_route_precedence(self):
        # Ensure /api endpoints are NOT intercepted by SPA fallback
        res_api = self.client.get("/api")
        self.assertEqual(res_api.status_code, 200)
        self.assertEqual(res_api.json()["status"], "running")

if __name__ == "__main__":
    unittest.main()
