#!/bin/bash
# Render deployment script - runs after buildCommand
# This script handles database migrations and other setup

set -e  # Exit on error

echo "=========================================="
echo "Starting Render Deployment Setup"
echo "=========================================="

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "⚠ Warning: DATABASE_URL is not set"
    echo "  Migrations will be skipped"
    exit 0
fi

echo "✓ DATABASE_URL is set"

# Wait for database to be ready (Render may take a moment)
echo "Waiting for database to be ready..."
sleep 5

# Run migrations
echo "Running Django migrations..."
python manage.py migrate --noinput

echo "=========================================="
echo "✓ Deployment setup complete!"
echo "=========================================="
