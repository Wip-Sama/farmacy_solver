@echo off
cd /d "%~dp0.."
echo Building Docker image for UNICAL Demacs Pharmacy Solver...
docker build -t pharmacy-solver:latest .
if %ERRORLEVEL% EQU 0 (
    echo.
    echo Successfully built Docker image: pharmacy-solver:latest
) else (
    echo.
    echo Docker build failed with error code %ERRORLEVEL%.
)
