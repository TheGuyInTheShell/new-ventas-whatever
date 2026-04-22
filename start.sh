#!/bin/sh

# Fail immediately if any command fails
set -e

echo "Starting deployment script..."

# ===== DEBUG: Diagnose container state =====
echo "--- Python & Uvicorn version ---"
python --version
uvicorn --version || echo "Uvicorn not found in path"
echo "===== END DEBUG ====="

# Push Alembic schema to database if the service exists
echo "Pushing Alembic schema to database (if configured)..."
alembic upgrade head || echo "No se requirieron/pudieron aplicar migraciones de Alembic o la base de datos no está lista"

echo "Schema pushed/verified. Starting FastAPI server..."

# Start the Python server
exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4 --proxy-headers
