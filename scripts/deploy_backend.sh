#!/usr/bin/env bash
set -euo pipefail

echo "Starting FastAPI backend (dev mode) on :8000"
exec uvicorn AI-Book-Keeping.backend.main:app --reload --host 0.0.0.0 --port 8000

