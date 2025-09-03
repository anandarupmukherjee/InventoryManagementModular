#!/bin/bash

# Exit on error
set -e

echo "1. Ensuring permissions and directories..."
mkdir -p /code/staticfiles
chmod -R 755 /code/staticfiles
ls -la /code/staticfiles

echo "2. Running migrations..."
python manage.py migrate

echo "3. Running collectstatic with simple storage..."
export DJANGO_STATICFILES_STORAGE=django.contrib.staticfiles.storage.StaticFilesStorage
# python manage.py collectstatic --noinput --verbosity 2

echo "4. Checking staticfiles directory after collectstatic..."
ls -la /code/staticfiles

echo "5. Switching to ManifestStaticFilesStorage and starting server..."
export DJANGO_STATICFILES_STORAGE=django.contrib.staticfiles.storage.ManifestStaticFilesStorage
python manage.py runserver 0.0.0.0:8000
