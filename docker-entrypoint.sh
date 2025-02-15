#!/bin/bash

# Esperar a que PostgreSQL esté disponible
until PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c '\q'; do
  >&2 echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

>&2 echo "PostgreSQL is up - executing command"

# Aplicar migraciones
python manage.py migrate

# Iniciar Daphne
exec daphne -b 0.0.0.0 -p 8000 daphne_server:application
