# AI Bob Platform - Complete Startup Script
# This script handles all dependencies and starts both systems

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🚀 AI Bob Platform - Complete Startup" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if Python is installed
function Test-Python {
    try {
        $pythonVersion = python --version 2>&1
        Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "✗ Python not found. Please install Python 3.9+" -ForegroundColor Red
        return $false
    }
}

# Function to check if pip is installed
function Test-Pip {
    try {
        $pipVersion = pip --version 2>&1
        Write-Host "✓ pip found: $pipVersion" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "✗ pip not found. Please install pip" -ForegroundColor Red
        return $false
    }
}

# Function to install dependencies for a project
function Install-Dependencies {
    param (
        [string]$ProjectPath,
        [string]$ProjectName
    )
    
    Write-Host ""
    Write-Host "📦 Installing dependencies for $ProjectName..." -ForegroundColor Yellow
    
    if (Test-Path "$ProjectPath\requirements.txt") {
        Push-Location $ProjectPath
        try {
            pip install -r requirements.txt --quiet
            Write-Host "✓ Dependencies installed for $ProjectName" -ForegroundColor Green
            return $true
        }
        catch {
            Write-Host "✗ Failed to install dependencies for $ProjectName" -ForegroundColor Red
            Write-Host "Error: $_" -ForegroundColor Red
            return $false
        }
        finally {
            Pop-Location
        }
    }
    else {
        Write-Host "✗ requirements.txt not found in $ProjectPath" -ForegroundColor Red
        return $false
    }
}

# Function to check if port is in use
function Test-Port {
    param ([int]$Port)
    
    $connection = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    return $null -ne $connection
}

# Function to kill process on port
function Stop-ProcessOnPort {
    param ([int]$Port)
    
    $connection = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    if ($connection) {
        $processId = $connection.OwningProcess
        Write-Host "Stopping process on port $Port (PID: $processId)..." -ForegroundColor Yellow
        Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
        Write-Host "✓ Port $Port freed" -ForegroundColor Green
    }
}

# Function to check if .env exists
function Test-EnvFile {
    param ([string]$ProjectPath)
    
    if (Test-Path "$ProjectPath\.env") {
        Write-Host "✓ .env file found" -ForegroundColor Green
        return $true
    }
    else {
        Write-Host "⚠ .env file not found - will use defaults" -ForegroundColor Yellow
        return $false
    }
}

# Main execution
Write-Host "Step 1: Checking prerequisites..." -ForegroundColor Cyan
Write-Host "-----------------------------------------------------------"

# Check Python and pip
if (-not (Test-Python)) {
    Write-Host ""
    Write-Host "Please install Python from https://www.python.org/downloads/" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

if (-not (Test-Pip)) {
    Write-Host ""
    Write-Host "Please install pip" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Get base directory
$baseDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$parserDir = Join-Path $baseDir "parser-workflow"
$repoAiDir = Join-Path $baseDir "repo-ai"

Write-Host ""
Write-Host "Step 2: Checking project directories..." -ForegroundColor Cyan
Write-Host "-----------------------------------------------------------"

if (-not (Test-Path $parserDir)) {
    Write-Host "✗ parser-workflow directory not found" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "✓ parser-workflow directory found" -ForegroundColor Green

if (-not (Test-Path $repoAiDir)) {
    Write-Host "✗ repo-ai directory not found" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "✓ repo-ai directory found" -ForegroundColor Green

Write-Host ""
Write-Host "Step 3: Installing dependencies..." -ForegroundColor Cyan
Write-Host "-----------------------------------------------------------"

# Install parser-workflow dependencies
if (-not (Install-Dependencies -ProjectPath $parserDir -ProjectName "Parser Workflow")) {
    Write-Host ""
    Write-Host "Failed to install Parser Workflow dependencies" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Install repo-ai dependencies
if (-not (Install-Dependencies -ProjectPath $repoAiDir -ProjectName "Repo AI")) {
    Write-Host ""
    Write-Host "Failed to install Repo AI dependencies" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Step 4: Checking configuration..." -ForegroundColor Cyan
Write-Host "-----------------------------------------------------------"

# Check .env files
Push-Location $repoAiDir
Test-EnvFile -ProjectPath $repoAiDir
Pop-Location

Write-Host ""
Write-Host "Step 5: Checking and freeing ports..." -ForegroundColor Cyan
Write-Host "-----------------------------------------------------------"

# Check and free ports
$ports = @(8000, 5000)
foreach ($port in $ports) {
    if (Test-Port -Port $port) {
        Write-Host "Port $port is in use" -ForegroundColor Yellow
        Stop-ProcessOnPort -Port $port
    }
    else {
        Write-Host "✓ Port $port is available" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "Step 6: Starting services..." -ForegroundColor Cyan
Write-Host "-----------------------------------------------------------"

# Start Parser Workflow Backend
Write-Host ""
Write-Host "Starting Parser Workflow Backend (Port 8000)..." -ForegroundColor Yellow
Push-Location $parserDir
$parserProcess = Start-Process python -ArgumentList "run_server.py" -PassThru -WindowStyle Normal
Pop-Location
Start-Sleep -Seconds 5

if ($parserProcess.HasExited) {
    Write-Host "✗ Parser backend failed to start" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "✓ Parser backend started (PID: $($parserProcess.Id))" -ForegroundColor Green

# Start Repo AI
Write-Host ""
Write-Host "Starting Repo AI (Port 5000)..." -ForegroundColor Yellow
Push-Location $repoAiDir
$repoAiProcess = Start-Process python -ArgumentList "app.py" -PassThru -WindowStyle Normal
Pop-Location
Start-Sleep -Seconds 5

if ($repoAiProcess.HasExited) {
    Write-Host "✗ Repo AI failed to start" -ForegroundColor Red
    Stop-Process -Id $parserProcess.Id -Force -ErrorAction SilentlyContinue
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "✓ Repo AI started (PID: $($repoAiProcess.Id))" -ForegroundColor Green

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "✓ All systems started successfully!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Access Points:" -ForegroundColor Cyan
Write-Host "  Parser Backend API:  http://localhost:8000/docs" -ForegroundColor White
Write-Host "  Repo AI Interface:   http://localhost:5000" -ForegroundColor White
Write-Host ""
Write-Host "Process IDs:" -ForegroundColor Cyan
Write-Host "  Parser Backend:  $($parserProcess.Id)" -ForegroundColor White
Write-Host "  Repo AI:         $($repoAiProcess.Id)" -ForegroundColor White
Write-Host ""
Write-Host "Opening browser..." -ForegroundColor Yellow
Start-Sleep -Seconds 2

# Open browser
Start-Process "http://localhost:5000"

Write-Host ""
Write-Host "Press any key to stop all services..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

Write-Host ""
Write-Host "Stopping all services..." -ForegroundColor Yellow

Stop-Process -Id $parserProcess.Id -Force -ErrorAction SilentlyContinue
Stop-Process -Id $repoAiProcess.Id -Force -ErrorAction SilentlyContinue

Write-Host "✓ All services stopped" -ForegroundColor Green
Write-Host ""
Write-Host "Goodbye! 👋" -ForegroundColor Cyan

# Made with Bob
