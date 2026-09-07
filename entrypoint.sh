#!/bin/sh
set -e

python manage.py migrate --noinput
python manage.py seed_demo

# One worker: multiple gunicorn processes each opening their own
# connection to one SQLite file risks "database is locked" under
# concurrent writes, and the free tier's 0.1 CPU gives no real
# parallelism from extra processes anyway. Threads give modest
# concurrency without that risk.
exec gunicorn config.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers 1 \
    --threads 4 \
    --timeout 60
