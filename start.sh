#!/bin/bash
# Railway startup script

echo "🚀 Starting Nia Learning Assistant..."

# Start the application
uvicorn main:app --host 0.0.0.0 --port $PORT
