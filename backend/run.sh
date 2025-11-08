#!/bin/bash
# Script to run the FastAPI backend server
cd "$(dirname "$0")"
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000

