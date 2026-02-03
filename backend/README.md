# Backend Operations

This folder contains the Python automation layer for Open-Metric. It is designed to run headlessly on a schedule (Task Scheduler or cron).

**Prerequisites**
- Python 3.10+
- Playwright browsers: `python -m playwright install`

**Install**
```
pip install -r backend/requirements.txt
```

**Configuration**
Create `backend/config/.env` from `backend/config/.env.example` and fill in values.

Required for Google Drive:
```
GOOGLE_APPLICATION_CREDENTIALS=../keys/service_account.json
GOOGLE_DRIVE_FOLDER_ID=YOUR_FOLDER_ID_HERE
```

Metricool optional values:
```
METRICOOL_EMAIL=you@example.com
METRICOOL_PASSWORD=your_password
METRICOOL_COOKIES_PATH=../keys/metricool_cookies.json
METRICOOL_ANALYTICS_URL=https://app.metricool.com/...
```

Buffer optional values:
```
BUFFER_EMAIL=you@example.com
BUFFER_PASSWORD=your_password
BUFFER_COOKIES_PATH=../keys/buffer_cookies.json
BUFFER_MAX_QUEUE=10
BUFFER_HEADLESS=true
```

**Key Scripts**
- `backend/db_init.py`
- `backend/modules/drive_sync.py`
- `backend/modules/harvester_metricool.py`
- `backend/modules/queue_manager.py`

**Usage**
1. Initialize the Drive CSV:
```
python backend/db_init.py
```
2. Run Metricool harvester:
```
python backend/modules/harvester_metricool.py
```
3. Run Buffer queue feeder:
```
python backend/modules/queue_manager.py
```

**Local Queue**
Create or edit `backend/data_cache/pending_posts.json`. Example shape:
```
[
  {
    "id": "post_001",
    "text": "Post text",
    "image_path": "",
    "platforms": ["linkedin"],
    "status": "pending"
  }
]
```

**Notes**
- Use cookies to avoid frequent logins. Store them in `backend/keys/`.
- `backend/config/.env`, `backend/keys/`, and `backend/data_cache/` are gitignored.
- Headless selectors may drift; update them in the modules if UI changes.
