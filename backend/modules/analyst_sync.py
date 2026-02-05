import logging
import os
from pathlib import Path
from typing import Optional

import pandas as pd
from dotenv import load_dotenv
from googleapiclient.http import MediaFileUpload

from backend.db_init import DATA_DIR, FILE_NAME, authenticate_drive, normalize_drive_folder_id
from backend.modules.sqlite_store import SQLiteStore

BASE_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = BASE_DIR / "config" / ".env"
load_dotenv(ENV_PATH)

logger = logging.getLogger("open_metric.analyst")


def _get_env(name: str) -> Optional[str]:
    value = os.getenv(name, "").strip()
    return value or None


def _prepare_source_csv() -> Path:
    target_name = _get_env("NOTEBOOKLM_SOURCE_NAME") or "NotebookLM_Source.csv"
    target_path = DATA_DIR / target_name

    store = SQLiteStore()
    df = store.export_df()

    if df.empty:
        fallback = DATA_DIR / FILE_NAME
        if fallback.exists():
            df = pd.read_csv(fallback)

    df.to_csv(target_path, index=False)
    return target_path


def _ensure_drive_file(service, folder_id: str, filename: str) -> str:
    query = f"name = '{filename}' and '{folder_id}' in parents and trashed = false"
    results = service.files().list(q=query, pageSize=1, fields="files(id)").execute()
    items = results.get("files", [])
    if items:
        return items[0]["id"]

    file_metadata = {"name": filename, "parents": [folder_id]}
    created = service.files().create(body=file_metadata, fields="id").execute()
    return created["id"]


def sync_notebook() -> None:
    file_id = _get_env("NOTEBOOKLM_SOURCE_FILE_ID")
    folder_id_raw = _get_env("NOTEBOOKLM_FOLDER_ID") or _get_env("GOOGLE_DRIVE_FOLDER_ID")
    filename = _get_env("NOTEBOOKLM_SOURCE_NAME") or "NotebookLM_Source.csv"

    if not file_id and not folder_id_raw:
        logger.warning(
            "NotebookLM sync skipped: NOTEBOOKLM_SOURCE_FILE_ID or NOTEBOOKLM_FOLDER_ID is required."
        )
        return

    service = authenticate_drive()
    source_path = _prepare_source_csv()

    if not file_id:
        folder_id = normalize_drive_folder_id(folder_id_raw or "")
        file_id = _ensure_drive_file(service, folder_id, filename)

    media = MediaFileUpload(source_path, mimetype="text/csv")
    service.files().update(fileId=file_id, media_body=media).execute()
    logger.info("NotebookLM source updated: %s", filename)
