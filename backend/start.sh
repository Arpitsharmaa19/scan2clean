#!/bin/bash
set -e
cd "$(dirname "$0")"

# Verify PORT is set, default to 10000 if not
PORT=${PORT:-10000}

echo "--> Starting migration..."
python manage.py migrate --no-input

echo "--> Starting Gunicorn on 0.0.0.0:$PORT"
# Use Gunicorn with Uvicorn workers for production-grade ASGI handling
# -k uvicorn.workers.UvicornWorker: Use Uvicorn worker class
# --bind 0.0.0.0:$PORT: Explicitly bind to all interfaces on the correct port
# --chdir backend: Ensure we are in the correct directory (though root-dir setting handles this mostly)
# --workers 4: standard worker count
# --access-logfile -: log to stdout
exec gunicorn config.asgi:application \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:$PORT \
    --workers 4 \
    --access-logfile - \
    --error-logfile -
