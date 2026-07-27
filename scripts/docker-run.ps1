$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location "$ScriptDir\.."
Write-Host "Starting UNICAL Demacs Pharmacy Solver container..." -ForegroundColor Cyan
docker compose up -d
if ($LASTEXITCODE -eq 0) {
    Write-Host "`nApplication Web UI running successfully at: http://localhost:8001/" -ForegroundColor Green
    Write-Host "Data directory mounted at: ${PWD}\data" -ForegroundColor Green
} else {
    Write-Host "`nDocker compose failed, attempting standalone docker run..." -ForegroundColor Yellow
    docker run -d -p 8001:8001 -v "${PWD}\data:/app/data" --name pharmacy_solver_app pharmacy-solver:latest
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Application running successfully at: http://localhost:8001/" -ForegroundColor Green
    }
}
