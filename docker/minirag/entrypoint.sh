#!/bin/bash
set -e 

echo "Creating database if not exists..."
PGPASSWORD=${POSTGRES_PASSWORD} psql -h ${POSTGRES_HOST} -U ${POSTGRES_USERNAME} -tc "SELECT 1 FROM pg_database WHERE datname = '${POSTGRES_MAIN_DB}'" | grep -q 1 || \
PGPASSWORD=${POSTGRES_PASSWORD} psql -h ${POSTGRES_HOST} -U ${POSTGRES_USERNAME} -c "CREATE DATABASE ${POSTGRES_MAIN_DB};"

echo "Running Database Migrations..."
cd /app/models/db_schemas/minirag/
alembic upgrade head
cd /app
echo "Database Migrations Completed."

exec "$@"
