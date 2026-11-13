#!/bin/sh
set -e

# Run database migrations
alembic upgrade head

# Run seed script (idempotent)
python app/seed.py

# Execute the main command
exec "$@"
