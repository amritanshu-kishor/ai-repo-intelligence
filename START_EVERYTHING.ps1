# Repository Intelligence Platform - ONE-CLICK STARTUP
# PowerShell version for better Windows compatibility

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Repository Intelligence Platform" -ForegroundColor Cyan
Write-Host " ONE-CLICK STARTUP" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "[1/4] Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "     ✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "     ✗ ERROR: Python not found!" -ForegroundColor Red
    Write-Host "     Please install Python 3.12 or higher" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check directories
Write-Host ""
Write-Host "[2/4] Checking directories..." -ForegroundColor Yellow
if (-not (Test-Path "parser-workflow")) {
    Write-Host "     ✗ ERROR: parser-workflow directory not found!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
if (-not (Test-Path "repo-ai")) {
    Write-Host "     ✗ ERROR: repo-ai directory not found!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "     ✓ Directories found" -ForegroundColor Green

# Start Parser-Workflow
Write-Host ""
Write-Host "[3/4] Starting Parser-Workflow Backend (Port 8001)..." -ForegroundColor Yellow
$parserJob = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd parser-workflow; python main.py" -PassThru -WindowStyle Normal
Start-Sleep -Seconds 3
Write-Host "     ✓ Parser-Workflow started (PID: $($parserJob.Id))" -ForegroundColor Green

# Start Repo-AI
Write-Host ""
Write-Host "[4/4] Starting Repo-AI Frontend+Backend (Port 5000)..." -ForegroundColor Yellow
$repoaiJob = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd repo-ai; python app.py" -PassThru -WindowStyle Normal
Start-Sleep -Seconds 5
Write-Host "     ✓ Repo-AI started (PID: $($repoaiJob.Id))" -ForegroundColor Green

# Open browser
Write-Host ""
Write-Host "Opening browser..." -ForegroundColor Yellow
Start-Sleep -Seconds 2
Start-Process "http://localhost:5000"
Write-Host "     ✓ Browser opened" -ForegroundColor Green

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " ✓ ALL SYSTEMS RUNNING!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Services:" -ForegroundColor White
Write-Host "  • Parser-Workflow: http://localhost:8001" -ForegroundColor White
Write-Host "  • Repo-AI Frontend: http://localhost:5000" -ForegroundColor White
Write-Host "  • API Docs: http://localhost:8001/docs" -ForegroundColor White
Write-Host ""
Write-Host "Two PowerShell windows have opened:" -ForegroundColor Yellow
Write-Host "  1. Parser-Workflow Backend" -ForegroundColor Yellow
Write-Host "  2. Repo-AI Frontend+Backend" -ForegroundColor Yellow
Write-Host ""
Write-Host "To stop: Close both PowerShell windows or press Ctrl+C in each" -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Ready to upload repositories!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Read-Host "Press Enter to keep this window open (or close to exit)"

# Made with Bob
