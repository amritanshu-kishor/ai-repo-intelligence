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
