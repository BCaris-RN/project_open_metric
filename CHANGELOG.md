# Changelog

All notable changes are documented in this file.

## 2026-02-05
- Implemented NotebookLM sync via Google Drive uploads.
- Added SQLite as local metrics store and integrated it into the harvester and API.
- Added retry logic with backoff for Metricool and Buffer automation.
- Added optional API key protection for backend endpoints and Flutter client support.
- Improved backend logging and added Ollama availability check.
- Added Docker support for backend (`backend/Dockerfile`, `.dockerignore`).
- Sanitized secrets and documented secret-handling policy.
- Regenerated review exports with platform scaffolding and binary assets split into two files.
- Added startup CSV initialization when Drive env vars are set.
- Added selector fallbacks for Metricool navigation.
- Updated Flutter to respect system theme mode.
- Added config store and API endpoints for in-app credential management.
- Added Metricool interactive auth endpoint with cookie capture.
- Added backend sidecar launcher and readiness gating on the splash screen.
- Added Settings and Connect Accounts screens.
- Added backend status indicator in the Home screen app bar.
- Updated launch flow: Flutter now auto-starts the backend, removing the manual multi-step startup.
