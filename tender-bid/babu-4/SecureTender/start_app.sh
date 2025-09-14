#!/bin/bash
cd "$(dirname "$0")"
uv run uvicorn api_server:app --host 0.0.0.0 --port 5000 --reload