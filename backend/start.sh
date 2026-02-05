#!/bin/bash
set -e

# Verify PORT is set, default to 10000 if not (for local testing mostly)
PORT=${PORT:-10000}

echo "--> Starting app on 0.0.0.0:$PORT"

# Run migrations one more time to be safe (idempotent)
python manage.py migrate --no-input

# Start Daphne
# We explicitly allow all IPs (-b 0.0.0.0) and use the rendered PORT
exec daphne -b 0.0.0.0 -p $PORT config.asgi:application
