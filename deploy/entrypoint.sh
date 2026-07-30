#!/bin/sh
set -eu

if [ "${MKE_RUN_STARTUP_TASKS:-0}" = "1" ]; then
    python manage.py migrate --noinput
    python manage.py collectstatic --noinput
fi

exec "$@"
