# Concurrent Development Server Launcher Script
$ErrorActionPreference = "Stop"

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host " Starting Pharmacy Solver Development Servers" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

$PythonExe = if (Test-Path ".venv312\Scripts\python.exe") {
    (Resolve-Path ".venv312\Scripts\python.exe").Path
} elseif (Test-Path ".venv\Scripts\python.exe") {
    (Resolve-Path ".venv\Scripts\python.exe").Path
} else {
    "python"
}

function Test-PortBindable {
    param([string]$Address, [int]$Port)
    $ip = if ($Address -eq "0.0.0.0") { [System.Net.IPAddress]::Any } else { [System.Net.IPAddress]::Parse($Address) }
    $listener = [System.Net.Sockets.TcpListener]::new($ip, $Port)
    try {
        $listener.Start()
        return $true
    } catch {
        return $false
    } finally {
        $listener.Stop()
    }
}

function Find-AvailablePort {
    param([string]$Address, [int]$PreferredPort)
    if (Test-PortBindable -Address $Address -Port $PreferredPort) {
        return $PreferredPort
    }
    foreach ($candidate in (($PreferredPort + 1)..($PreferredPort + 25))) {
        if (Test-PortBindable -Address $Address -Port $candidate) {
            return $candidate
        }
    }
    throw "Could not find an available TCP port starting from $PreferredPort on $Address."
}

# Parse ports and host from app_config.yaml via core.config
$PyCmd = 'from core.config import APP_CONFIG; s = APP_CONFIG.get("server", {}); print(",".join([str(s.get("backend_port", 8000)), str(s.get("frontend_port", 5173)), str(s.get("host", "127.0.0.1"))]))'
$PortsCsv = & $PythonExe -c $PyCmd
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($PortsCsv)) {
    throw "Failed to read server configuration from app_config.yaml."
}

$PortArray = $PortsCsv.Trim().Split(",")
$ConfiguredBackendPort = [int]$PortArray[0]
$ConfiguredFrontendPort = [int]$PortArray[1]
$ServerHost = $PortArray[2]

$BackendPort = Find-AvailablePort -Address $ServerHost -PreferredPort $ConfiguredBackendPort
if ($BackendPort -ne $ConfiguredBackendPort) {
    Write-Warning "Backend port $ConfiguredBackendPort is reserved or in use on $ServerHost; falling back to port $BackendPort."
}

$FrontendPort = Find-AvailablePort -Address $ServerHost -PreferredPort $ConfiguredFrontendPort
if ($FrontendPort -ne $ConfiguredFrontendPort) {
    Write-Warning "Frontend port $ConfiguredFrontendPort is reserved or in use on $ServerHost; falling back to port $FrontendPort."
}

Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Backend Host & Port : http://${ServerHost}:${BackendPort}" -ForegroundColor Green
Write-Host "  Frontend Host & Port: http://${ServerHost}:${FrontendPort}" -ForegroundColor Green
Write-Host "  Swagger Docs URL    : http://${ServerHost}:${BackendPort}/docs" -ForegroundColor Green
Write-Host "=====================================================`n" -ForegroundColor Cyan

# Launch FastAPI backend in background job
Write-Host "Launching FastAPI Backend..." -ForegroundColor Yellow
$BackendJob = Start-Job -ScriptBlock {
    param($cwd, $py, $bindHost, $port)
    Set-Location $cwd
    $env:PORT = "$port"
    & $py -m uvicorn backend.main:app --host $bindHost --port $port --reload
} -ArgumentList (Get-Location).Path, $PythonExe, $ServerHost, $BackendPort

# Wait for backend readiness before launching Vite so proxy requests never hit an unbound port
$HealthUrl = "http://${ServerHost}:${BackendPort}/api/health"
$BackendReady = $false
for ($i = 0; $i -lt 40; $i++) {
    if ($BackendJob.State -in @("Failed", "Stopped", "Completed")) {
        $JobOutput = Receive-Job -Job $BackendJob -ErrorAction SilentlyContinue
        Remove-Job -Job $BackendJob -Force -ErrorAction SilentlyContinue
        throw "FastAPI backend exited unexpectedly:`n$($JobOutput -join "`n")"
    }
    try {
        $resp = Invoke-RestMethod -Uri $HealthUrl -TimeoutSec 1 -ErrorAction Stop
        if ($resp.status -eq "ok") {
            $BackendReady = $true
            break
        }
    } catch {
        Start-Sleep -Milliseconds 250
    }
}

if (-not $BackendReady) {
    $JobOutput = Receive-Job -Job $BackendJob -ErrorAction SilentlyContinue
    Stop-Job -Job $BackendJob -ErrorAction SilentlyContinue
    Remove-Job -Job $BackendJob -Force -ErrorAction SilentlyContinue
    throw "Timed out waiting for FastAPI backend at $HealthUrl.`n$($JobOutput -join "`n")"
}

Write-Host "FastAPI Backend is ready!" -ForegroundColor Green

# Launch Vite frontend in current process
Write-Host "Launching Vite Frontend..." -ForegroundColor Yellow
Push-Location -Path "frontend"
try {
    $env:VITE_API_TARGET = "http://${ServerHost}:${BackendPort}"
    npx --no-install vite --port $FrontendPort --host $ServerHost
} finally {
    Pop-Location
    Write-Host "`nStopping background FastAPI job..." -ForegroundColor Red
    Stop-Job -Job $BackendJob -ErrorAction SilentlyContinue
    Remove-Job -Job $BackendJob -Force -ErrorAction SilentlyContinue
}
