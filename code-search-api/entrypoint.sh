#!/bin/bash

set -e

echo "Starting initialization process..."

# Check if indexing has already been completed
if [ -f "/app/indexing_completed" ]; then
    echo "Repositories already indexed, skipping..."
else
    echo "Starting repository indexing..."
    python /app/index_repos.py
    
    # Mark indexing as completed
    touch /app/indexing_completed
    echo "Indexing completed successfully!"
fi

# Start the FastAPI application
echo "Starting FastAPI application..."
exec uvicorn api:app --host 0.0.0.0 --port 8000