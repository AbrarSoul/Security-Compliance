#!/usr/bin/env bash
# Run the API using the project virtualenv (not system/conda Python).
set -e
cd "$(dirname "$0")"

if [[ ! -d .venv ]]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
fi

if [[ ! -f .env ]]; then
  echo "Copying .env.example to .env"
  cp .env.example .env
fi

exec .venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
