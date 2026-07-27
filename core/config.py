import os
from pathlib import Path

# Project root directory (parent of core directory)
PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT", Path(__file__).resolve().parent.parent))
CONFIG_FILE = PROJECT_ROOT / "app_config.yaml"

def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            import yaml
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except ImportError:
            # Fallback if PyYAML is not installed yet
            pass
    return {
        "server": {
            "host": "127.0.0.1",
            "backend_port": 8000,
            "frontend_port": 5173,
            "reload": True
        },
        "paths": {
            "data_dir": "data",
            "schedules_dir": "data/schedules",
            "settings_file": "data/settings.json"
        }
    }

APP_CONFIG = load_config()

ASP_DIR = PROJECT_ROOT / "core" / "asp"
DATA_DIR = PROJECT_ROOT / APP_CONFIG.get("paths", {}).get("data_dir", "data")
SCHEDULES_DIR = PROJECT_ROOT / APP_CONFIG.get("paths", {}).get("schedules_dir", "data/schedules")
SETTINGS_FILE = PROJECT_ROOT / APP_CONFIG.get("paths", {}).get("settings_file", "data/settings.json")
