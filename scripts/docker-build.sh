#!/usr/bin/env bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."
echo "Building Docker image for UNICAL Demacs Pharmacy Solver..."
docker build -t pharmacy-solver:latest .
if [ $? -eq 0 ]; then
    echo ""
    echo "Successfully built Docker image: pharmacy-solver:latest"
else
    echo ""
    echo "Docker build failed."
fi
