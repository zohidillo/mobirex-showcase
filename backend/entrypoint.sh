#!/bin/sh

set -e

echo "Waiting for postgres..."

while ! nc -z "$DB_HOST" 5432; do
  sleep 1
done

echo "Postgres started"

python manage.py migrate
python manage.py collectstatic --noinput

exec "$@"
