#!/bin/sh
set -e

if [ ! -x /opt/venv/bin/uvicorn ]; then
  python -m venv /opt/venv
  /opt/venv/bin/pip install --no-cache-dir -r /app/requirements.txt
  chown -R app:app /opt/venv
fi

runuser -u app -- mkdir -p /app/var/logs

exec runuser -u app -- "$@"
