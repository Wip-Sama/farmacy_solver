#!/usr/bin/env bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."
echo "Starting UNICAL Demacs Pharmacy Solver container..."
docker compose up -d
if [ $? -eq 0 ]; then
    echo ""
    echo "Application running successfully at: http://localhost:8001/"
    echo "Data directory mounted at: $(pwd)/data"
else
    echo ""
    echo "Docker compose failed, attempting standalone docker run..."
    docker run -d -p 8001:8001 -v "$(pwd)/data:/app/data" --name pharmacy_solver_app pharmacy-solver:latest
    if [ $? -eq 0 ]; then
        echo "Application running successfully at: http://localhost:8001/"
    fi
fi
