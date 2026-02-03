import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# --- 1. CONFIGURATION ---
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / "config" / ".env"
load_dotenv(ENV_PATH)

DATA_DIR = BASE_DIR / "data_cache"
DATA_DIR.mkdir(parents=True, exist_ok=True)

FILE_NAME = "Social_Metrics_Master.csv"
LOCAL_PATH = DATA_DIR / FILE_NAME

# The "Golden Schema" for NotebookLM
MASTER_SCHEMA = [
    "post_id",          # Composite Key: e.g., "ig_123456789"
    "timestamp_utc",    # ISO 8601: "2026-02-02T10:00:00"
    "platform",         # "Instagram", "LinkedIn", "TikTok"
    "media_type",       # "Reel", "Carousel", "Static"
    "engagement_score", # Pre-calc: (Likes + Comments + Shares) / Reach
    "reach",            # Raw Reach
    "likes",
    "comments",
    "shares",
    "caption_text",     # For Topic/Sentiment analysis
    "conversion_status" # "Clicked", "None"
]


def _require_env(var_name: str) -> str:
    value = os.getenv(var_name)
    if not value:
        print(f"Error: Missing required env var {var_name}.")
        print(f"-> Set it in {ENV_PATH}")
        sys.exit(1)
    return value


def _resolve_path(path_value: str) -> Path:
    path = Path(path_value)
    if not path.is_absolute():
        path = (BASE_DIR / path).resolve()
    return path


def authenticate_drive():
    """Authenticates using the Service Account."""
    service_account_path = _resolve_path(_require_env("GOOGLE_APPLICATION_CREDENTIALS"))

    if not service_account_path.exists():
        print(f"Error: Service account key not found at {service_account_path}")
        print("-> Place your .json key in backend/keys/ or update GOOGLE_APPLICATION_CREDENTIALS.")
        sys.exit(1)

    scopes = ["https://www.googleapis.com/auth/drive"]
    creds = service_account.Credentials.from_service_account_file(
        service_account_path, scopes=scopes
    )
    return build("drive", "v3", credentials=creds)


def init_data_lake():
    folder_id = _require_env("GOOGLE_DRIVE_FOLDER_ID")
    print(f"Connecting to Google Drive (Folder ID: {folder_id})...")
    service = authenticate_drive()

    query = f"name = '{FILE_NAME}' and '{folder_id}' in parents and trashed = false"
    results = service.files().list(
        q=query,
        pageSize=1,
        fields="files(id, name)"
    ).execute()
    items = results.get("files", [])

    if items:
        print(f"Database exists. File ID: {items[0]['id']}")
        return items[0]["id"]

    print("Database not found. Initializing schema...")

    df = pd.DataFrame(columns=MASTER_SCHEMA)
    df.to_csv(LOCAL_PATH, index=False)

    file_metadata = {
        "name": FILE_NAME,
        "parents": [folder_id]
    }
    media = MediaFileUpload(LOCAL_PATH, mimetype="text/csv")

    created = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id"
    ).execute()

    print(f"Success. Created '{FILE_NAME}' (ID: {created.get('id')})")
    print("-> You can now connect this file to NotebookLM.")
    return created.get("id")


if __name__ == "__main__":
    init_data_lake()
