release: echo "Starting migrations..." && python manage.py migrate --verbosity 3 && echo "Migrations complete"
web: gunicorn Logistics.wsgi --log-level debug
