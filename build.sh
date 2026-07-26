#!/usr/bin/env bash
set -euo pipefail

if [ -z "${VIRTUAL_ENV:-}" ]; then
  echo "Activating virtual environment..."
  if [ -d "venv" ]; then
    source venv/bin/activate
  else
    echo "No virtual environment found. Please create one first."
    exit 1
  fi
fi

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Applying database migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Creating superuser..."
DJANGO_SUPERUSER_USERNAME="${DJANGO_SUPERUSER_USERNAME:-sylvaline}"
DJANGO_SUPERUSER_EMAIL="${DJANGO_SUPERUSER_EMAIL:-sylvalinenzekwe@gmail.com}"
DJANGO_SUPERUSER_PASSWORD="${DJANGO_SUPERUSER_PASSWORD:-Success20}"

python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='${DJANGO_SUPERUSER_USERNAME}').exists() or User.objects.create_superuser(username='${DJANGO_SUPERUSER_USERNAME}', email='${DJANGO_SUPERUSER_EMAIL}', password='${DJANGO_SUPERUSER_PASSWORD}')"

echo "Build complete."
