#!/bin/bash
# Complete Smart Routing System Deployment Script
# Sets up all components: Valhalla, PostgreSQL/TimescaleDB, Kafka, Redis, and Django

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Smart Routing & Trail System - Full Deployment   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
echo ""

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENVIRONMENT="${1:-.env.local}"

# Check if .env file exists
if [ ! -f "$PROJECT_ROOT/$ENVIRONMENT" ]; then
    echo -e "${YELLOW}[*] Creating $ENVIRONMENT from template...${NC}"
    cat > "$PROJECT_ROOT/$ENVIRONMENT" << 'ENVFILE'
# Environment Configuration
VALHALLA_SERVER=http://localhost:8002
OSRM_SERVER=http://router.project-osrm.org
KAFKA_BOOTSTRAP_SERVERS=kafka:29092
KAFKA_SECURITY_PROTOCOL=PLAINTEXT

# PostgreSQL/TimescaleDB
DB_ENGINE=postgresql
DB_NAME=fleet_db
DB_USER=fleet_user
DB_PASSWORD=fleet_secure_password_123
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Django
DEBUG=False
SECRET_KEY=django-insecure-change-this-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,api.fleet.local

# Fleet Configuration
FLEET_NAME=Fleet Management System
SUPPORT_EMAIL=admin@fleet.local
ENVFILE
    echo -e "${GREEN}✓ Created $ENVIRONMENT${NC}"
fi

echo -e "${YELLOW}[1/6] Checking Docker installation...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker not found. Please install Docker first.${NC}"
    exit 1
fi
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗ Docker Compose not found. Please install Docker Compose.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker and Docker Compose found${NC}"
echo ""

echo -e "${YELLOW}[2/6] Starting infrastructure (Kafka, TimescaleDB, Redis, etc.)...${NC}"
cd "$PROJECT_ROOT"

# Build and start services
docker-compose -f docker-compose.yml up -d

# Wait for services to be ready
echo -e "${YELLOW}   Waiting for services to start...${NC}"
sleep 15

# Check service health
for service in timescaledb kafka redis valhalla; do
    echo -e "${YELLOW}   Checking $service...${NC}"
    docker-compose ps | grep $service || echo -e "${YELLOW}   Warning: $service may not be running${NC}"
done

echo -e "${GREEN}✓ Infrastructure started${NC}"
echo ""

echo -e "${YELLOW}[3/6] Setting up Python environment...${NC}"
cd "$PROJECT_ROOT/server"

if command -v pipenv &> /dev/null; then
    echo -e "${YELLOW}   Installing Python dependencies with Pipenv...${NC}"
    pipenv install
    pipenv install kafka-python  # Additional for Kafka support
else
    echo -e "${YELLOW}   Pipenv not found, using pip...${NC}"
    python -m venv venv
    source venv/bin/activate 2>/dev/null || . venv/Scripts/activate
    pip install -r <(pipenv requirements) 2>/dev/null || pip install django djangorestframework django-cors-headers kafka-python requests
fi

echo -e "${GREEN}✓ Python environment ready${NC}"
echo ""

echo -e "${YELLOW}[4/6] Running Django migrations...${NC}"

# Wait for PostgreSQL to be ready
echo -e "${YELLOW}   Waiting for PostgreSQL to accept connections...${NC}"
for i in {1..30}; do
    if docker-compose exec -T timescaledb psql -U fleet_user -d fleet_db -c "SELECT 1" &> /dev/null; then
        echo -e "${GREEN}   ✓ PostgreSQL is ready${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

# Run migrations
python manage.py migrate

echo -e "${GREEN}✓ Django migrations complete${NC}"
echo ""

echo -e "${YELLOW}[5/6] Building React frontend...${NC}"
cd "$PROJECT_ROOT/client/Frontend"

if command -v npm &> /dev/null; then
    npm install
    npm run build
    echo -e "${GREEN}✓ React build complete${NC}"
else
    echo -e "${YELLOW}   npm not found, skipping frontend build${NC}"
fi
echo ""

echo -e "${YELLOW}[6/6] Creating service startup files...${NC}"

# Create systemd service file for Django
sudo tee /etc/systemd/system/fleet-django.service > /dev/null <<EOF
[Unit]
Description=Fleet Management Django Server
After=network.target docker-compose.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_ROOT/server
ExecStart=/bin/bash -c '. venv/bin/activate 2>/dev/null && python manage.py runserver 0.0.0.0:8000'
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for Kafka processor
sudo tee /etc/systemd/system/fleet-kafka.service > /dev/null <<EOF
[Unit]
Description=Fleet Management Kafka Stream Processor
After=network.target docker-compose.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_ROOT/server
ExecStart=/bin/bash -c '. venv/bin/activate 2>/dev/null && python kafka_processor.py'
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload

echo -e "${GREEN}✓ Service files created${NC}"
echo ""

echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          Deployment Complete! 🎉                   ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BLUE}Next Steps:${NC}"
echo ""
echo -e "${YELLOW}1. Start Services:${NC}"
echo "   # Option A: Direct (foreground)"
echo "   cd $PROJECT_ROOT/server"
echo "   python manage.py runserver 0.0.0.0:8000"
echo ""
echo "   # Option B: Systemd (background)"
echo "   sudo systemctl start fleet-django"
echo "   sudo systemctl start fleet-kafka"
echo ""

echo -e "${YELLOW}2. Start Frontend (development):${NC}"
echo "   cd $PROJECT_ROOT/client/Frontend"
echo "   npm run dev"
echo ""

echo -e "${YELLOW}3. Access Services:${NC}"
echo "   Frontend:     http://localhost:5173"
echo "   API:          http://localhost:8000/api/"
echo "   Kafka UI:     http://localhost:8080"
echo "   Grafana:      http://localhost:3000 (admin/admin123)"
echo "   pgAdmin:      http://localhost:5050 (admin@fleet.local/admin123)"
echo "   Kibana:       http://localhost:5601"
echo ""

echo -e "${YELLOW}4. Test Routing:${NC}"
echo "   curl -X POST http://localhost:8000/api/v2/routes/calculate \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"origin\": {\"lat\": 17.8252, \"lon\": 25.2753}, \"destination\": {\"lat\": 17.8832, \"lon\": 25.8232}, \"vehicle_id\": \"TRUCK-001\"}'"
echo ""

echo -e "${YELLOW}5. View Logs:${NC}"
echo "   # Django"
echo "   docker-compose logs -f"
echo ""
echo "   # Kafka"
echo "   docker-compose logs -f kafka"
echo ""
echo "   # Check all container status"
echo "   docker-compose ps"
echo ""

echo -e "${YELLOW}6. Shutdown:${NC}"
echo "   docker-compose down  # Stop containers"
echo "   docker-compose down -v  # Stop and remove volumes"
echo ""

echo -e "${BLUE}Documentation:${NC}"
echo "   Design Doc: $PROJECT_ROOT/SMART_ROUTING_SYSTEM_DESIGN.md"
echo ""
