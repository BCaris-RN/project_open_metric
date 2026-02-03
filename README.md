Project Open-Metric: The Meta-Aggregator
A "Headless" Social Media Orchestration Engine
Strategy: Free-Tier Orchestration Cost: $0/month Status: Alpha (Phase 1-2 Complete)
📖 Overview
Project Open-Metric is a Python-based "Meta-Aggregator" designed to replicate the functionality of enterprise social media suites (like Metricool Premium, Sprout Social) without the subscription costs.
Instead of using official, paid APIs, this architecture employs a "Hacker" Engineering Strategy: it treats free-tier SaaS tools (Buffer, Zoho Social, NotebookLM) not as end-user platforms, but as "Headless Modules" controlled by a central Python orchestrator.
The "Paywall Bridge" Philosophy
We bypass standard limitations (scheduling caps, 30-day data retention, AI credit limits) by:
1. Virtualizing Queues: Managing unlimited schedules locally and "drip-feeding" posts to free accounts via headless browsers.
2. Semantic Analytics: Replacing paid dashboards with Google NotebookLM, synced programmatically to a raw CSV database on Google Drive.
3. Local AI: Replacing paid AI assistants with self-hosted Ollama (Llama 4) instances.

--------------------------------------------------------------------------------
🏗 Architecture
The system operates on a hub-and-spoke model where Python acts as the central logic layer.
graph TD
    A[Social Platforms] -->|Scraping via Playwright/Instaloader| B(Python Orchestrator)
    B -->|Normalize & Append| C{Google Drive 'CSV Bridge'}
    C -->|Auto-Sync| D[NotebookLM 'Analyst']
    D -->|Insights & Reports| E[User]
    
    F[Local DB / CSV Schedule] -->|Read Queue| B
    B -->|Generate Content| G[Ollama / Llama 4]
    G -->|Drafts| B
    B -->|Headless Injection| H[Free Tier Buffer/Zoho]
    H -->|Publish| A

--------------------------------------------------------------------------------
🚀 Key Features & Bypasses
Feature
The Limitation
The "Open-Metric" Solution
Scheduling
Free plans cap queues (e.g., 10 posts).
Headless Worker Virtualization: We keep an infinite queue locally and only push the next post when a slot opens up.
Analytics
History limited to 30 days.
The CSV Bridge: Data is scraped daily and stored in an "append-only" CSV on Drive, retaining history indefinitely.
Reporting
PDF reports are paid-only.
NotebookLM: We use Google's free AI to generate "Traction Reports," slides, and deep-dive analysis from the CSV.
AI Content
Credit-based (paid) generation.
Local LLMs: We connect to a local Ollama instance (Llama 4) for unlimited, private content generation.
Multi-Account
One account per login.
Session Isolation: We use Playwright BrowserContexts to inject distinct state.json cookies for managing 50+ brands simultaneously.

--------------------------------------------------------------------------------
🛠 Tech Stack
• Core Logic: Python 3.10+
• Browser Automation: Playwright (Async API)
• Database: Google Drive (Storage) + Pandas (Processing)
• Analytics Engine: Google NotebookLM (Gemini 1.5 Pro)
• Content Generation: Ollama (Llama 4 / DeepSeek V3)
• Scraping: Instaloader (Instagram), BeautifulSoup4

--------------------------------------------------------------------------------
📂 Project Structure
/
├── backend/
│   ├── auth/
│   │   ├── auth_capture.py       # Helper to manually login & save cookies
│   │   └── state/                # Stores *.json session files (GitIgnored)
│   ├── db/
│   │   ├── db_init.py            # Initializes Master CSV on Drive
│   │   └── drive_sync.py         # Handles Delta Checks & Uploads
│   ├── modules/
│   │   ├── harvester.py          # Scrapes metrics (Metricool/Instaloader)
│   │   ├── worker_manager.py     # Headless publisher for Buffer/Zoho
│   │   ├── notebook_sync.py      # Automates NotebookLM "Sync" button
│   │   └── creative_engine.py    # Connects to local Ollama API
│   └── main.py                   # Central Orchestrator (Cron Job)
├── data/
│   ├── content_queue.csv         # Local unlimited schedule
│   └── social_metrics_master.csv # Local mirror of Drive DB
├── requirements.txt
└── README.md

--------------------------------------------------------------------------------
⚡ Workflow
Phase 1: Setup (The "One-Time" Login)
Because we avoid expensive APIs, we rely on session persistence.
1. Run python backend/auth/auth_capture.py.
2. Manually log in to Buffer, Metricool, and Google Drive in the browser window that pops up.
3. The script saves your cookies to backend/auth/state/*.json.
Phase 2: The Daily Loop (Orchestrator)
The main.py script runs continuously or via Cron:
1. Harvest: Runs harvester.py to scrape yesterday's performance metrics.
2. Normalize: Python calculates "Engagement Score" and "Best Time" math locally (helping NotebookLM).
3. Sync: Uploads the updated CSV to Drive and triggers notebook_sync.py to force-refresh the AI analyst.
4. Generate: Checks creative_engine.py; if the queue is low, prompts Llama 4 to write captions based on yesterday's winning topics.
5. Publish: Runs worker_manager.py. Checks if Buffer has a free slot (0-9/10). If yes, injects the next post from the local queue.

--------------------------------------------------------------------------------
📦 Installation
1. Clone the Repo:
2. Install Dependencies:
3. Configure Environment: Create a .env file for your Google Service Account (if using API for Drive) or rely on state.json for full headless usage.
4. Install Ollama (Optional for AI Gen): Download from ollama.com and pull the model:

--------------------------------------------------------------------------------
⚠️ Disclaimer
Educational Use Only. This project uses browser automation to interact with third-party services.
• Rate Limits: The orchestrator is designed to mimic human behavior (randomized delays), but aggressive usage may flag your accounts.
• TOS: Review the Terms of Service for Buffer, Zoho, and social platforms. The authors are not responsible for banned accounts.
