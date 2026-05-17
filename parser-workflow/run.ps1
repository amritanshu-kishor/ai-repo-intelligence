# Start the Repository Intelligence API (picks a free port if needed).
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Host "Virtual env not found. Run: python -m venv .venv" -ForegroundColor Red
    exit 1
}

& $python run_server.py
