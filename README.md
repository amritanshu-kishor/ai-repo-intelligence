# Repository Intelligence — Run & Host Instructions

This project uses a FastAPI-based "parser" service (in `parser-workflow`) and a Flask-based main app (in `repo-ai`). Run both services in parallel (two terminals) during development.

## LLM Options & Access
The project now includes additional LLM provider options exposed via the UI/configuration: Grok, Gemini, and other compatible providers. During a recent hackathon `bob` access was available and used for testing, but that access is temporary and not guaranteed long-term — configure and provide your own preferred provider credentials (see `repo-ai/config.py` or environment variables).

## Refined local run order
For a smooth local startup, follow this order:

1. Run any setup/install scripts first (optional):

```bash
# from repo root (if provided)
# INSTALL_ALL_DEPENDENCIES.bat
# or follow the Prerequisites section to install requirements
```

2. Start helper/background scripts that the parser may rely on (one-off):

```bash
cd parser-workflow
python run_server.py   # prints API/docs URL and picks a free port if needed
```

3. In two separate terminals start the backends (parser + repo-ai):

- Terminal A — Parser (FastAPI / Uvicorn):

```bash
cd parser-workflow
python run_server.py
# or: uvicorn main:app --reload --host 127.0.0.1 --port 8001
```

- Terminal B — Main app (Flask):

```bash
cd repo-ai
python app.py
```

4. Open the UI at `http://localhost:5000` (or the printed host/port) and proceed to upload a repository and use the configured LLM provider.

Notes: ensure the parser backend URL in `repo-ai` matches the parser port (the helper script may choose a different free port if the default is busy).

## Prerequisites
- Python 3.10+ (Windows-compatible)
- Install dependencies (from the repo root or per-subproject):

```bash
python -m pip install -r parser-workflow/requirements-minimal.txt
python -m pip install -r repo-ai/requirements-minimal.txt
```

## Run locally (development)

Open two terminals.

Terminal A — parser (FastAPI + Uvicorn)

1. Change to the parser folder:

```bash
cd parser-workflow
```

2a. Recommended (uses helper that finds a free port):

```bash
python run_server.py
```

2b. Or run Uvicorn directly (reload enabled):

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Notes: the helper `run_server.py` will print the API and docs URL and fallback to a free port if the configured port is busy.

Terminal B — main app (Flask)

```bash
cd repo-ai
python app.py
```

This starts the Flask testing interface on `http://localhost:5000` by default. The Flask app will attempt to contact the parser service for indexing and health checks.

### Verify

- Parser docs: open `http://127.0.0.1:8000/docs` (or the printed URL from `run_server.py`).
- Main app health: `http://127.0.0.1:5000/api/health`

## Running in Production / Hosting notes

FastAPI (parser) — recommended: run behind an ASGI process manager (Gunicorn + Uvicorn workers) or a container.

Example (Linux):

```bash
pip install gunicorn uvicorn
gunicorn -k uvicorn.workers.UvicornWorker main:app -w 4 -b 0.0.0.0:8000
```

Flask (main app) — recommended: use Gunicorn on Linux, or Waitress on Windows.

Example (Linux):

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 repo-ai.app:app
```

Example (Windows):

```bash
pip install waitress
waitress-serve --port=5000 repo-ai.app:app
```

Deployment options:
- Docker + Docker Compose to run both services and a reverse proxy (Nginx).
- Host each service separately on cloud providers (e.g., Azure App Service, AWS ECS, or GCP Run) and configure DNS / proxy.

## Notes & Troubleshooting
- If a port is already in use, `parser-workflow/run_server.py` will pick a free port and print it.
- Ensure the parser service URL is reachable from the main app; update integration endpoints if you deploy services to different hosts.
- For CI and automated checks, keep the local dev commands (`uvicorn` and `python app.py`) as they are quick to run.

---

If you want, I can add a `docker-compose.yml` that brings both services up together and exposes the health endpoints. Want me to create that next?
# AI-Bob Consolidated Documentation

This single consolidated document replaces the multiple individual Markdown files. It contains the essential setup and run steps, key fixes, and troubleshooting notes needed to run the platform. Originals were removed to keep the repository clean; ask if you want any of them restored.

## Quick Start - Minimal Steps
- Prerequisite: Python 3.12 installed and available as `py -3.12`.
- Create virtual environment (first time):

```powershell
py -3.12 -m venv venv
venv\Scripts\activate.bat
python -m pip install --upgrade pip
```

- Install dependencies (one-time):

```powershell
# Parser workflow
cd parser-workflow
pip install -r requirements.txt
# Repo AI
cd ..\repo-ai
pip install -r requirements.txt
```

- Start systems:

```powershell
# Terminal 1 - Parser Workflow
cd parser-workflow
python start_backend.py
# Terminal 2 - Repo AI
cd repo-ai
python app.py
```

- Health checks:

```powershell
curl http://localhost:8001/docs
curl http://localhost:5000/api/health
```

## One-line One-click (if using provided scripts)
- First-time install: run `INSTALL_ALL_DEPENDENCIES.bat`.
- Start everything: run `START_ALL_SYSTEMS.bat` (or `START_ALL_WITH_VENV.bat` if using venv).

## Upload & Use
1. Open Repo AI UI: http://localhost:5000
2. Upload repository ZIP via the UI or use the API:

```powershell
curl -X POST http://localhost:5000/api/upload-repository -F "file=@your-repo.zip"
```

3. After upload, ask a query via UI or API:

```powershell
curl -X POST http://localhost:5000/api/ask-query -H "Content-Type: application/json" -d '{"query":"What breaks if auth.py changes?"}'
```

## Restart Procedure (apply fixes)
- If you update code, restart both services so changes take effect:

```powershell
# Stop both with Ctrl+C, then:
cd parser-workflow
python start_backend.py
cd ..\repo-ai
python app.py
```

## Key Integration Notes
- Repo AI (`repo-ai`) integrates with parser-workflow (`parser-workflow`) via HTTP endpoints (default: `http://127.0.0.1:8001`).
- Ensure `.env` in `repo-ai` has `USE_MOCK_DATA=false` to prefer live data.
- If parser-workflow is down, the system returns empty results (not mock) unless `USE_MOCK_DATA=true`.

## Important Fixes (summary)
- Removed static SAMPLE_GRAPH fallback; parser-workflow now returns real graphs when uploaded.
- Context builder now prefers live parser-workflow data and only uses mock when explicitly configured.
- Added repository session management to isolate uploads and rebuilt graphs per upload.
- Added validation to detect mock/static data patterns and warn.
- Parser/Repo integration includes health checks, retries, and graceful fallbacks.

## Troubleshooting Checklist
- Parser-workflow not responding: verify process on port 8001 and API docs reachable.
- Repo AI shows `data_source: mock`: check `repo-ai/.env` and parser-workflow health.
- Graph shows 0 nodes or 0 edges: verify repository has internal imports and check parser-workflow logs for node/edge counts.
- Ports in use: use `netstat -ano | findstr :<port>` and `taskkill /PID <pid> /F`.

## Minimal Commit & Push Steps
```powershell
# after changes
git add .
git commit -m "Consolidate docs; ignore batch files"
git push origin main
```

## Where to look for more details
- All original `.md` files were consolidated. If you need a full original file restored, tell me which one and I will recover it.

## Contact/Restore
- Reply with filenames to restore; I can extract and restore individual originals on request.
