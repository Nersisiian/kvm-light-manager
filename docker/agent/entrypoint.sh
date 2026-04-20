#!/bin/sh
set -e

echo "Waiting for Redis..."
while ! nc -z redis 6379; do
  sleep 1
done
echo "Redis started"

echo "Starting Agent server..."
exec python -m agent.main