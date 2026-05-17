# AI Bob Platform - Dependency Installation Script
# This script installs all required dependencies for both systems

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "AI Bob Platform - Dependency Installation" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Function to check Python
function Test-Python {
    try {
        $pythonVersion = python --version 2>&1
        Write-Host "Python found: $pythonVersion" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "Python not found" -ForegroundColor Red
        return $false
    }
}

# Function to install dependencies
function Install-ProjectDependencies {
    param (
        [string]$ProjectPath,
        [string]$ProjectName
    )
    
    Write-Host ""
    Write-Host "Installing $ProjectName dependencies..." -ForegroundColor Yellow
    Write-Host "-----------------------------------------------------------"
    
    if (-not (Test-Path "$ProjectPath\requirements.txt")) {
        Write-Host "requirements.txt not found in $ProjectPath" -ForegroundColor Red
        return $false
    }
    
    Push-Location $ProjectPath
    
    try {
        Write-Host "Running: pip install -r requirements.txt" -ForegroundColor Gray
        pip install -r requirements.txt
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "$ProjectName dependencies installed successfully" -ForegroundColor Green
            return $true
        }
        else {
            Write-Host "Failed to install $ProjectName dependencies" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "Error installing $ProjectName dependencies: $_" -ForegroundColor Red
        return $false
    }
    finally {
        Pop-Location
    }
}

# Main execution
Write-Host "Step 1: Checking Python installation..." -ForegroundColor Cyan
Write-Host "-----------------------------------------------------------"

if (-not (Test-Python)) {
    Write-Host ""
    Write-Host "Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.9+ from https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host ""
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

$allDirsExist = $true

if (Test-Path $parserDir) {
    Write-Host "parser-workflow directory found" -ForegroundColor Green
}
else {
    Write-Host "parser-workflow directory not found" -ForegroundColor Red
    $allDirsExist = $false
}

if (Test-Path $repoAiDir) {
    Write-Host "repo-ai directory found" -ForegroundColor Green
}
else {
    Write-Host "repo-ai directory not found" -ForegroundColor Red
    $allDirsExist = $false
}

if (-not $allDirsExist) {
    Write-Host ""
    Write-Host "Some directories are missing. Cannot continue." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Step 3: Installing dependencies..." -ForegroundColor Cyan
Write-Host "============================================================"

# Install parser-workflow dependencies
$parserSuccess = Install-ProjectDependencies -ProjectPath $parserDir -ProjectName "Parser Workflow"

# Install repo-ai dependencies
$repoAiSuccess = Install-ProjectDependencies -ProjectPath $repoAiDir -ProjectName "Repo AI"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Installation Summary" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

if ($parserSuccess) {
    Write-Host "Parser Workflow: Dependencies installed" -ForegroundColor Green
}
else {
    Write-Host "Parser Workflow: Installation failed" -ForegroundColor Red
}

if ($repoAiSuccess) {
    Write-Host "Repo AI: Dependencies installed" -ForegroundColor Green
}
else {
    Write-Host "Repo AI: Installation failed" -ForegroundColor Red
}

Write-Host ""

if ($parserSuccess -and $repoAiSuccess) {
    Write-Host "All dependencies installed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next step: Run START_ALL_SYSTEMS.bat to start the platform" -ForegroundColor Cyan
    $exitCode = 0
}
else {
    Write-Host "Some dependencies failed to install" -ForegroundColor Red
    Write-Host "Please check the errors above and try again" -ForegroundColor Yellow
    $exitCode = 1
}

Write-Host ""
Read-Host "Press Enter to exit"
exit $exitCode

# Made with Bob
