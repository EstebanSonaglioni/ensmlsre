#!/bin/sh
set -e

if [ ! -d /app/node_modules/next ]; then
  npm ci
fi

if [ -d /app/node_modules ] && [ "$(stat -c '%u' /app/node_modules)" != "1000" ]; then
  chown -R node:node /app/node_modules
fi

mkdir -p /app/.next
chown node:node /app/.next

exec su-exec node "$@"
