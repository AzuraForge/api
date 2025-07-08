#!/bin/sh
set -e

if [ -z "$DATABASE_URL" ]; then
    echo "DATABASE_URL not set. Attempting to build from Docker secrets..."
    POSTGRES_USER_FILE="/run/secrets/postgres_user"
    POSTGRES_PASSWORD_FILE="/run/secrets/postgres_password"
    if [ -f "$POSTGRES_USER_FILE" ]; then
        export POSTGRES_USER=$(cat "$POSTGRES_USER_FILE")
    else
        echo "PostgreSQL user secret not found!"
        if [ -n "$POSTGRES_HOST" ]; then exit 1; fi
    fi
    if [ -f "$POSTGRES_PASSWORD_FILE" ]; then
        export POSTGRES_PASSWORD=$(cat "$POSTGRES_PASSWORD_FILE")
    else
        echo "PostgreSQL password secret not found!"
        if [ -n "$POSTGRES_HOST" ]; then exit 1; fi
    fi
    if [ -n "$POSTGRES_USER" ] && [ -n "$POSTGRES_PASSWORD" ] && [ -n "$POSTGRES_HOST" ]; then
        export DATABASE_URL="postgresql+psycopg2://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_DB_PORT}/${POSTGRES_DB}"
        echo "DATABASE_URL constructed from secrets."
    else
        echo "Could not construct DATABASE_URL from secrets/env vars."
    fi
else
    echo "DATABASE_URL is already set. Skipping secret handling."
fi

if [ -n "$POSTGRES_HOST" ]; then
    echo "Waiting for PostgreSQL to be ready at ${POSTGRES_HOST}:${POSTGRES_DB_PORT}..."
    wait-for-it.sh "${POSTGRES_HOST}:${POSTGRES_DB_PORT}" -t 60 -- echo "PostgreSQL is up."
fi

# === YENİ VE GÜNCELLENMİŞ ALEMİC ADIMI ===
echo "API: Running database migrations to 'head'..."

# Python kullanarak 'azuraforge_dbmodels' paketinin içindeki alembic.ini dosyasının yolunu bul.
# Bu, yolun ortama göre değişmesinden etkilenmeyen sağlam bir yöntemdir.
ALEMBIC_INI_PATH=$(python -c "import os, azuraforge_dbmodels; print(os.path.join(os.path.dirname(azuraforge_dbmodels.__file__), 'alembic.ini'))")

echo "Found alembic.ini at: $ALEMBIC_INI_PATH"

# Alembic'e -c bayrağı ile konfigürasyon dosyasının yerini açıkça belirt.
alembic -c "$ALEMBIC_INI_PATH" upgrade head

echo "API: Database migrations complete."
# === YENİ ADIM SONU ===

echo "Starting application command: $@"
exec "$@"