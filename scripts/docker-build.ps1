$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location "$ScriptDir\.."
Write-Host "Building Docker image for UNICAL Demacs Pharmacy Solver..." -ForegroundColor Cyan
docker build -t pharmacy-solver:latest .
if ($LASTEXITCODE -eq 0) {
    Write-Host "`nSuccessfully built Docker image: pharmacy-solver:latest" -ForegroundColor Green
} else {
    Write-Host "`nDocker build failed with error code $LASTEXITCODE" -ForegroundColor Red
}
