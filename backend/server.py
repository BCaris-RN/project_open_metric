import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import List, Optional

import pandas as pd
import requests
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.modules.queue_manager import QueueManager
from backend.modules.harvester_metricool import MetricoolHarvester
from backend.modules.analyst_sync import sync_notebook
from backend.modules.creative_engine import CreativeEngine
from backend.modules.drive_sync import DriveSync
from backend.modules.sqlite_store import SQLiteStore

DATA_DIR = BASE_DIR / "data_cache"
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH = DATA_DIR / "system.log"

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
    ],
)
logger = logging.getLogger("open_metric")

API_KEY = os.getenv("OPEN_METRIC_API_KEY", "").strip()
OLLAMA_STATUS_URL = os.getenv("OLLAMA_STATUS_URL", "http://localhost:11434/api/tags")

STORE = SQLiteStore()

app = FastAPI(title="Open-Metric Command Center", version="1.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Post(BaseModel):
    id: Optional[str] = None
    text: str
    platforms: List[str] = Field(default_factory=lambda: ["linkedin"])
    status: str = "pending"
    image_path: Optional[str] = ""


class GenerateRequest(BaseModel):
    topic: str
    tone: str = "professional"


def _log(message: str) -> None:
    logger.info(message)


def get_queue_manager() -> QueueManager:
    return QueueManager()


def get_store() -> SQLiteStore:
    return STORE


async def run_in_thread(func, *args):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: func(*args))


async def run_harvester_task() -> None:
    _log("[Background] Starting harvester")
    try:
        harvester = MetricoolHarvester()
        await harvester.scrape()
        _log("[Background] Harvester finished")
    except Exception as exc:
        _log(f"[Background] Harvester failed: {exc}")


async def run_sync_task() -> None:
    _log("[Background] Starting NotebookLM sync")
    try:
        await run_in_thread(sync_notebook)
        _log("[Background] NotebookLM sync finished")
    except Exception as exc:
        _log(f"[Background] NotebookLM sync failed: {exc}")


async def run_drive_sync_task() -> None:
    _log("[Background] Starting Drive sync")
    try:
        csv_path = DATA_DIR / "Social_Metrics_Master.csv"
        if not csv_path.exists():
            store = get_store()
            df = store.export_df()
            if df.empty:
                _log("[Background] Drive sync failed: No local CSV or SQLite data found.")
                return
            df.to_csv(csv_path, index=False)

        local_df = pd.read_csv(csv_path)
        sync_engine = DriveSync()
        new_rows = await run_in_thread(sync_engine.push_update, local_df)
        _log(f"[Background] Drive sync finished: {new_rows} new rows uploaded")
    except Exception as exc:
        _log(f"[Background] Drive sync failed: {exc}")


async def run_queue_task() -> None:
    _log("[Background] Filling queue slots")
    try:
        manager = get_queue_manager()
        await manager.fill_slots()
        _log("[Background] Queue check finished")
    except Exception as exc:
        _log(f"[Background] Queue fill failed: {exc}")


@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    if API_KEY and request.url.path not in {"/", "/docs", "/openapi.json"}:
        if request.headers.get("x-api-key") != API_KEY:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    return await call_next(request)


@app.on_event("startup")
async def startup_check():
    if not API_KEY:
        logger.warning("OPEN_METRIC_API_KEY not set. API is unauthenticated.")
    try:
        response = requests.get(OLLAMA_STATUS_URL, timeout=2)
        if response.status_code != 200:
            logger.warning("Ollama check failed: status %s", response.status_code)
    except Exception as exc:
        logger.warning("Ollama not reachable at %s: %s", OLLAMA_STATUS_URL, exc)


@app.get("/")
async def health_check():
    return {"status": "online", "system": "Open-Metric Orchestrator"}


@app.get("/stats")
async def get_latest_stats():
    store = get_store()
    latest = store.latest_row()
    if latest:
        return latest

    csv_path = DATA_DIR / "Social_Metrics_Master.csv"
    if not csv_path.exists():
        return {"error": "No data yet. Run harvester."}

    try:
        df = pd.read_csv(csv_path)
        if df.empty:
            return {}
        return df.iloc[-1].to_dict()
    except Exception as exc:
        return {"error": str(exc)}


@app.get("/queue", response_model=List[Post])
async def get_queue():
    manager = get_queue_manager()
    return manager.queue_data


@app.post("/queue/add")
async def add_post(post: Post):
    manager = get_queue_manager()

    if not post.id:
        import uuid

        post.id = f"post_{str(uuid.uuid4())[:8]}"

    new_entry = post.model_dump()
    manager.queue_data.append(new_entry)
    manager._save_queue()
    return {"status": "added", "post": new_entry}


@app.post("/action/harvest")
async def trigger_harvest():
    asyncio.create_task(run_harvester_task())
    return {"status": "started", "message": "Harvester running in background."}


@app.post("/harvest")
async def trigger_harvest_alias():
    return await trigger_harvest()


@app.post("/action/sync")
async def trigger_sync():
    asyncio.create_task(run_sync_task())
    return {"status": "started", "message": "Analyst sync running in background."}


@app.post("/sync-drive")
async def trigger_sync_drive():
    asyncio.create_task(run_drive_sync_task())
    return {"status": "started", "message": "Drive sync running in background."}


@app.post("/action/fill_queue")
async def trigger_queue_fill():
    asyncio.create_task(run_queue_task())
    return {"status": "started", "message": "Queue fill running in background."}


@app.get("/logs")
async def get_logs():
    if not LOG_PATH.exists():
        return {"lines": []}

    try:
        with open(LOG_PATH, "r", encoding="utf-8") as handle:
            lines = handle.readlines()
        return {"lines": [line.rstrip("\n") for line in lines[-50:]]}
    except Exception as exc:
        return {"error": str(exc)}


@app.post("/generate")
async def generate_content(req: GenerateRequest):
    try:
        engine = CreativeEngine()
        content = await run_in_thread(engine.generate_caption, req.topic, req.tone)
        return {"content": content}
    except Exception as exc:
        _log(f"[CreativeEngine] Generation failed: {exc}")
        return {"content": "Error: AI generation failed."}


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
