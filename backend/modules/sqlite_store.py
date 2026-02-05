import os
import sqlite3
from pathlib import Path
from typing import Optional

import pandas as pd
from dotenv import load_dotenv

from backend.db_init import DATA_DIR, MASTER_SCHEMA

BASE_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = BASE_DIR / "config" / ".env"
load_dotenv(ENV_PATH)


def _resolve_db_path() -> Path:
    raw = os.getenv("SQLITE_DB_PATH", str(DATA_DIR / "open_metric.db"))
    path = Path(raw)
    if not path.is_absolute():
        path = (BASE_DIR / path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


class SQLiteStore:
    def __init__(self):
        self.db_path = _resolve_db_path()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        columns = ", ".join([f"{col} TEXT" for col in MASTER_SCHEMA])
        sql = f"""
        CREATE TABLE IF NOT EXISTS metrics (
            {columns},
            PRIMARY KEY (post_id)
        );
        """
        with self._connect() as conn:
            conn.execute(sql)
            conn.commit()

    def upsert_df(self, df: pd.DataFrame) -> int:
        if df is None or df.empty:
            return 0

        working = df.copy()
        for col in MASTER_SCHEMA:
            if col not in working.columns:
                working[col] = pd.NA
        working = working[MASTER_SCHEMA]
        working["post_id"] = working["post_id"].astype(str)
        working = working[working["post_id"].str.len() > 0]
        working = working.drop_duplicates(subset=["post_id"], keep="first")

        rows = working.fillna("").values.tolist()
        if not rows:
            return 0

        placeholders = ", ".join(["?"] * len(MASTER_SCHEMA))
        sql = f"INSERT OR IGNORE INTO metrics ({', '.join(MASTER_SCHEMA)}) VALUES ({placeholders})"

        with self._connect() as conn:
            cur = conn.cursor()
            cur.executemany(sql, rows)
            conn.commit()
            return cur.rowcount

    def latest_row(self) -> Optional[dict]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT * FROM metrics
                ORDER BY
                    CASE WHEN timestamp_utc IS NULL OR timestamp_utc = '' THEN 1 ELSE 0 END,
                    timestamp_utc DESC,
                    rowid DESC
                LIMIT 1
                """
            )
            row = cur.fetchone()
            if not row:
                return None
            return dict(zip(MASTER_SCHEMA, row))

    def export_df(self) -> pd.DataFrame:
        with self._connect() as conn:
            return pd.read_sql_query("SELECT * FROM metrics", conn)

    def export_csv(self, path: Path) -> Path:
        df = self.export_df()
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False)
        return path
