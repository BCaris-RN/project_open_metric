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
