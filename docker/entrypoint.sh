#!/bin/sh
set -eu

if [ "${DJANGO_RUN_MIGRATIONS:-0}" = "1" ]; then
    poetry run python manage.py migrate --noinput
fi

exec "$@"
