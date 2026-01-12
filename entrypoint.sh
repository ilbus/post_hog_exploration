#!/bin/bash
set -e

# Run migrations
echo "Running alembic upgrades..."
uv run alembic upgrade head

# Exec whatever command is passed to the container
exec "$@"
