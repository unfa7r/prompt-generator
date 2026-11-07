import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SETTINGS_FILE = ROOT / "config" / "settings.json"

def load_settings():
    with SETTINGS_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)

def validate_settings(settings):
    required = [
        "style",
        "aesthetic",
        "lighting",
        "camera",
        "aspect_ratio",
        "detail",
        "text"
    ]

    missing = [key for key in required if key not in settings]

    if missing:
        raise ValueError(f"Missing settings: {', '.join(missing)}")

    return settings
