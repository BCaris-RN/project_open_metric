import io
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

from backend.db_init import (
    authenticate_drive,
    DATA_DIR,
    FILE_NAME,
    MASTER_SCHEMA,
    normalize_drive_folder_id,
)

BASE_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = BASE_DIR / "config" / ".env"
load_dotenv(ENV_PATH)


def _require_env(var_name: str) -> str:
    value = os.getenv(var_name)
    if not value:
        print(f"Error: Missing required env var {var_name}.")
        print(f"-> Set it in {ENV_PATH}")
        raise SystemExit(1)
    return value


class DriveSync:
    def __init__(self):
        self.service = authenticate_drive()
        self.folder_id = normalize_drive_folder_id(_require_env("GOOGLE_DRIVE_FOLDER_ID"))
        self.local_path = DATA_DIR / FILE_NAME
        self.local_path.parent.mkdir(parents=True, exist_ok=True)
        self.file_id = self._get_file_id()

    def _get_file_id(self) -> str:
        """Finds the ID of the existing Master CSV."""
        query = f"name = '{FILE_NAME}' and '{self.folder_id}' in parents and trashed = false"
        results = self.service.files().list(q=query, pageSize=1, fields="files(id)").execute()
        items = results.get("files", [])
        if not items:
            raise FileNotFoundError(
                f"Master CSV '{FILE_NAME}' not found. Run backend/db_init.py first."
            )
        return items[0]["id"]

    def pull_master(self) -> pd.DataFrame:
        """Downloads the current Master CSV from Drive."""
        request = self.service.files().get_media(fileId=self.file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            _, done = downloader.next_chunk()

        fh.seek(0)
        try:
            return pd.read_csv(fh)
        except pd.errors.EmptyDataError:
            return pd.DataFrame(columns=MASTER_SCHEMA)

    def _coerce_schema(self, df: pd.DataFrame) -> pd.DataFrame:
        if df is None or df.empty:
            return pd.DataFrame(columns=MASTER_SCHEMA)

        for col in MASTER_SCHEMA:
            if col not in df.columns:
                df[col] = pd.NA

        return df[MASTER_SCHEMA]

    def push_update(self, new_data_df: pd.DataFrame) -> int:
        """
        Delta Check:
        1. Downloads current Master.
        2. Filters out posts that already exist (by post_id).
        3. Appends only NEW posts.
        4. Uploads the updated Master.
        """
        if new_data_df is None or new_data_df.empty:
            print("No data provided. Nothing to sync.")
            return 0

        incoming = self._coerce_schema(new_data_df.copy())
        if "post_id" not in incoming.columns:
            raise ValueError("Incoming data is missing required column: post_id")

        incoming["post_id"] = incoming["post_id"].astype(str)
        incoming = incoming[incoming["post_id"].str.len() > 0]
        incoming = incoming.drop_duplicates(subset=["post_id"], keep="first")

        print("Downloading current Master DB for delta check...")
        current_df = self._coerce_schema(self.pull_master())
        current_ids = set(current_df["post_id"].astype(str))

        delta_df = incoming[~incoming["post_id"].isin(current_ids)]

        if delta_df.empty:
            print("No new data found. Database is up to date.")
            return 0

        print(f"Found {len(delta_df)} new entries. Merging...")
        updated_df = pd.concat([current_df, delta_df], ignore_index=True)
        updated_df.to_csv(self.local_path, index=False)

        media = MediaFileUpload(self.local_path, mimetype="text/csv")
        self.service.files().update(fileId=self.file_id, media_body=media).execute()

        print(f"Success! Uploaded updated Master DB with {len(updated_df)} total rows.")
        return len(delta_df)
