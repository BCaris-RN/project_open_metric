# Project Open-Metric

Self-hosted meta-aggregator that orchestrates free-tier SaaS tools (Metricool, Buffer, NotebookLM) to emulate an enterprise social media stack.

**Status**
- Phase 1: Data lake on Google Drive (CSV bridge) implemented
- Phase 2: Metricool analytics harvester implemented
- Phase 3: Buffer queue manager implemented
- Phase 4: NotebookLM sync planned
- Phase 5: Flutter dashboard planned

**Architecture Summary**
- Google Drive CSV is the source of truth for analytics (NotebookLM-friendly schema).
- Playwright harvesters pull metrics from free-tier dashboards.
- Local queue enables unlimited scheduling by filling Buffer slots just in time.

**Repository Layout**
```
backend/
  config/
    .env.example
  data_cache/              # GitIgnored runtime cache
  keys/                    # GitIgnored service account + cookies
  db_init.py               # Creates Social_Metrics_Master.csv on Drive
  requirements.txt
  modules/
    drive_sync.py          # Delta sync: download -> dedup -> upload
    harvester_metricool.py # Metricool table scraper
    queue_manager.py       # Buffer queue feeder
lib/
  main.dart                # Flutter app (Phase 5)
```

**Quickstart**
1. Install backend deps:
```
pip install -r backend/requirements.txt
python -m playwright install
```
2. Create `backend/config/.env` from `backend/config/.env.example`.
3. Place your service account key at `backend/keys/service_account.json` and share the Drive folder with the service account email.
4. Initialize the Drive CSV:
```
python backend/db_init.py
```

**Run Harvester (Metricool)**
```
python backend/modules/harvester_metricool.py
```

**Run Publisher (Buffer)**
1. Create `backend/data_cache/pending_posts.json` with pending posts.
2. Run:
```
python backend/modules/queue_manager.py
```

**Environment Variables**
Required for Phase 1:
```
GOOGLE_APPLICATION_CREDENTIALS=../keys/service_account.json
GOOGLE_DRIVE_FOLDER_ID=YOUR_FOLDER_ID_HERE
```

Metricool (optional if cookies provided):
```
METRICOOL_EMAIL=you@example.com
METRICOOL_PASSWORD=your_password
METRICOOL_COOKIES_PATH=../keys/metricool_cookies.json
METRICOOL_ANALYTICS_URL=https://app.metricool.com/...
```

Buffer (optional if cookies provided):
```
BUFFER_EMAIL=you@example.com
BUFFER_PASSWORD=your_password
BUFFER_COOKIES_PATH=../keys/buffer_cookies.json
BUFFER_MAX_QUEUE=10
BUFFER_HEADLESS=true
```

**Security Notes**
- `backend/config/.env`, `backend/keys/`, and `backend/data_cache/` are gitignored.
- Use cookies to avoid frequent logins for headless automations.

**Disclaimer**
This project uses browser automation to interact with third-party services. Review each service's Terms of Service and use responsibly.
