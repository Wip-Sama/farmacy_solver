# Concurrent Development Server Launcher Script
$ErrorActionPreference = "Stop"

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host " Starting Pharmacy Solver Development Servers" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

# Parse ports from app_config.yaml via Python helper
$PortsJson = .\.venv312\Scripts\python -c "import yaml; cfg = yaml.safe_load(open('app_config.yaml')); print(f'{cfg.get(\"server\", {}).get(\"backend_port\", 8000)},{cfg.get(\"server\", {}).get(\"frontend_port\", 5173)},{cfg.get(\"server\", {}).get(\"host\", \"127.0.0.1\")}')"
$PortArray = $PortsJson.Split(",")
$BackendPort = $PortArray[0]
$FrontendPort = $PortArray[1]
$Host = $PortArray[2]

Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Backend Host & Port : http://$Host`:$BackendPort" -ForegroundColor Green
Write-Host "  Frontend Host & Port: http://$Host`:$FrontendPort" -ForegroundColor Green
Write-Host "  Swagger Docs URL    : http://$Host`:$BackendPort/docs" -ForegroundColor Green
Write-Host "=====================================================`n" -ForegroundColor Cyan

# Launch FastAPI backend in background job
$BackendScript = ".venv312\Scripts\python -m uvicorn backend.main:app --host $Host --port $BackendPort --reload"
Write-Host "Launching FastAPI Backend..." -ForegroundColor Yellow
$BackendJob = Start-Job -ScriptBlock {
    param($cwd, $cmd)
    Set-Location $cwd
    Invoke-Expression $cmd
} -ArgumentList (Get-Location).Path, $BackendScript

# Launch Vite frontend in current process
Write-Host "Launching Vite Frontend..." -ForegroundColor Yellow
Set-Location -Path "frontend"
try {
    npm run dev -- --port $FrontendPort --host $Host
} finally {
    Write-Host "`nStopping background FastAPI job..." -ForegroundColor Red
    Stop-Job -Job $BackendJob
    Remove-Job -Job $BackendJob
}
