@echo off
cd /d "%~dp0.."
echo Starting UNICAL Demacs Pharmacy Solver container...
docker compose up -d
if %ERRORLEVEL% EQU 0 (
    echo.
    echo Application running successfully at: http://localhost:8001/
    echo Data directory mounted at: %CD%\data
) else (
    echo.
    echo Docker compose failed. Attempting standalone docker run...
    docker run -d -p 8001:8001 -v "%CD%\data:/app/data" --name pharmacy_solver_app pharmacy-solver:latest
    if %ERRORLEVEL% EQU 0 (
        echo Application running successfully at: http://localhost:8001/
    )
)
