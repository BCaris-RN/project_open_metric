import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BASE_DIR.parent
SETTINGS_PATH = BASE_DIR / "config" / "settings.json"
KEYS_DIR = PROJECT_ROOT / "keys"

DEFAULTS = {
    "metricool_cookies_path": str(KEYS_DIR / "metricool_cookies.json"),
    "buffer_cookies_path": str(KEYS_DIR / "buffer_cookies.json"),
    "service_account_path": str(KEYS_DIR / "service_account.json"),
}


def _load_settings() -> Dict[str, Any]:
    if SETTINGS_PATH.exists():
        try:
            return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def _save_settings(data: Dict[str, Any]) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    settings = _load_settings()
    value = settings.get(key)
    if value is None or value == "":
        return default
    return str(value)


def save_config(update: Dict[str, Any]) -> None:
    settings = _load_settings()
    for key, value in update.items():
        if value is None:
            continue
        settings[key] = value
    _save_settings(settings)


def get_metricool_email() -> Optional[str]:
    return os.getenv("METRICOOL_EMAIL") or get_setting("metricool_email")


def get_metricool_password() -> Optional[str]:
    return os.getenv("METRICOOL_PASSWORD") or get_setting("metricool_password")


def get_metricool_cookies_path() -> str:
    return (
        os.getenv("METRICOOL_COOKIES_PATH")
        or get_setting("metricool_cookies_path", DEFAULTS["metricool_cookies_path"])
        or DEFAULTS["metricool_cookies_path"]
    )


def get_metricool_analytics_url() -> Optional[str]:
    return os.getenv("METRICOOL_ANALYTICS_URL") or get_setting("metricool_analytics_url")


def get_buffer_email() -> Optional[str]:
    return os.getenv("BUFFER_EMAIL") or get_setting("buffer_email")


def get_buffer_password() -> Optional[str]:
    return os.getenv("BUFFER_PASSWORD") or get_setting("buffer_password")


def get_buffer_cookies_path() -> str:
    return (
        os.getenv("BUFFER_COOKIES_PATH")
        or get_setting("buffer_cookies_path", DEFAULTS["buffer_cookies_path"])
        or DEFAULTS["buffer_cookies_path"]
    )


def get_drive_folder_id() -> Optional[str]:
    return os.getenv("GOOGLE_DRIVE_FOLDER_ID") or get_setting("drive_id")


def get_service_account_path() -> str:
    return (
        os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        or get_setting("service_account_path", DEFAULTS["service_account_path"])
        or DEFAULTS["service_account_path"]
    )


def config_status() -> Dict[str, bool]:
    metricool_email = get_metricool_email()
    metricool_password = get_metricool_password()
    metricool_cookies = Path(get_metricool_cookies_path())
    drive_id = get_drive_folder_id()
    service_account = Path(get_service_account_path())
    buffer_email = get_buffer_email()
    buffer_password = get_buffer_password()
    buffer_cookies = Path(get_buffer_cookies_path())

    return {
        "metricool_connected": metricool_cookies.exists()
        or (bool(metricool_email) and bool(metricool_password)),
        "drive_connected": bool(drive_id) and service_account.exists(),
        "buffer_connected": buffer_cookies.exists()
        or (bool(buffer_email) and bool(buffer_password)),
    }
