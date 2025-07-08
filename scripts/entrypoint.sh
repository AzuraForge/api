# ========== DOSYA: api/scripts/entrypoint.sh ==========
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

# === YENİ: ALEMİC GEÇİŞİNİ UYGULAMA ADIMI ===
echo "API: Running database migrations to 'head'..."
alembic upgrade head
echo "API: Database migrations complete."
# === YENİ ADIM SONU ===

echo "Starting application command: $@"
exec "$@"