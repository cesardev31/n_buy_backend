# Usar una imagen base oficial de Python
FROM python:3.11-slim

# Establecer variables de entorno
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE=n_buy_backend.settings
ENV GOOGLE_API_KEY="dummy_key_for_build"

# Establecer el directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Crear directorios necesarios
RUN mkdir -p /app/static /app/media

# Copiar el proyecto
COPY . .

# Configurar whitenoise para archivos estáticos
ENV DJANGO_SETTINGS_MODULE=n_buy_backend.settings
ENV STATIC_ROOT=/app/static
ENV MEDIA_ROOT=/app/media

# Exponer puerto
EXPOSE 8000

# Comando para iniciar
CMD daphne -b 0.0.0.0 -p $PORT daphne_server:application
