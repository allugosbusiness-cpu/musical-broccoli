release: python manage.py migrate --noinput
web: gunicorn Logistics.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --worker-class sync --timeout 60 --log-level info
