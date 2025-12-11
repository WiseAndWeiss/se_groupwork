#!/bin/bash
set -e

# Wait for DB to become available (simple loop)
if [ -n "$MYSQL_HOST" ]; then
  echo "Waiting for database at $MYSQL_HOST:$MYSQL_PORT..."
  COUNTER=0
  until nc -z "$MYSQL_HOST" "$MYSQL_PORT"; do
    sleep 1
    COUNTER=$((COUNTER+1))
    if [ "$COUNTER" -gt 60 ]; then
      echo "Timed out waiting for database" >&2
      break
    fi
  done
fi

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn..."
exec gunicorn se_groupwork.wsgi:application --bind 0.0.0.0:8000 --workers ${WEB_CONCURRENCY:-3}
