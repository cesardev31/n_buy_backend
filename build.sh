#!/bin/bash
set -o errexit

# Actualizar pip e instalar dependencias
python -m pip install --upgrade pip
pip install -r requirements.txt

# Aplicar migraciones
python manage.py migrate 