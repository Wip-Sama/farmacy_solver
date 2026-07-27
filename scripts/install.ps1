# One-Click Environment Setup Script for Windows PowerShell
$ErrorActionPreference = "Stop"

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host " Pharmacy Scheduling System - Installation Script" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

# 1. Verify Python Installation
Write-Host "`n[1/3] Checking Python installation..." -ForegroundColor Yellow
$PythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $PythonCmd) {
    Write-Error "Python 3.10+ is required but not found in PATH."
    exit 1
}
Write-Host "Found Python: $($PythonCmd.Source)" -ForegroundColor Green

# Create virtual environment if not present
if (-not (Test-Path ".venv312")) {
    Write-Host "Creating Python virtual environment (.venv312)..." -ForegroundColor Yellow
    python -m venv .venv312
}

# 2. Install Python Dependencies
Write-Host "`n[2/3] Installing Python backend dependencies from requirements.txt..." -ForegroundColor Yellow
.\.venv312\Scripts\pip install -r requirements.txt
Write-Host "Python dependencies installed successfully!" -ForegroundColor Green

# 3. Install Frontend Node Dependencies
Write-Host "`n[3/3] Installing frontend Node dependencies..." -ForegroundColor Yellow
$NodeCmd = Get-Command node -ErrorAction SilentlyContinue
if (-not $NodeCmd) {
    Write-Error "Node.js 18+ is required but not found in PATH."
    exit 1
}

Set-Location -Path "frontend"
npm install
Set-Location -Path ".."
Write-Host "Frontend dependencies installed successfully!" -ForegroundColor Green

Write-Host "`n=====================================================" -ForegroundColor Cyan
Write-Host " Setup complete! Run .\scripts\dev.ps1 to start dev servers." -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
