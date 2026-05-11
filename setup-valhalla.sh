#!/bin/bash
# Valhalla Routing Engine Setup & Installation
# This script sets up Valhalla for production-grade routing

set -e

echo "🚀 Valhalla Smart Routing Engine Setup"
echo "======================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
VALHALLA_HOME="${VALHALLA_HOME:-.}/valhalla"
DATA_DIR="${VALHALLA_HOME}/data"
TILES_DIR="${VALHALLA_HOME}/tiles"
CONFIG_DIR="${VALHALLA_HOME}/config"
MAPS_REGION="${MAPS_REGION:-africa/zimbabwe}" # Default Zimbabwe, Zambia, Botswana

echo -e "${YELLOW}[1/5] Installing Valhalla dependencies...${NC}"

# Install system dependencies
if command -v apt-get &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y \
        build-essential \
        cmake \
        curl \
        git \
        pkg-config \
        libboost-all-dev \
        libprotobuf-dev \
        protobuf-compiler \
        libprime-server-dev \
        libzmq3-dev \
        libcurl4-openssl-dev
elif command -v brew &> /dev/null; then
    brew install cmake boost protobuf libzmq
fi

echo -e "${GREEN}✓ Dependencies installed${NC}"

echo -e "${YELLOW}[2/5] Cloning Valhalla repository...${NC}"

if [ ! -d "valhalla" ]; then
    git clone --depth=1 https://github.com/valhalla/valhalla.git
else
    echo "Valhalla repository already exists"
fi

cd valhalla

echo -e "${GREEN}✓ Repository cloned${NC}"

echo -e "${YELLOW}[3/5] Building Valhalla...${NC}"

mkdir -p build
cd build

cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -DENABLE_PYTHON_BINDINGS=ON \
    -DENABLE_SERVICES=ON \
    -DENABLE_DATA_TOOLS=ON

make -j$(nproc)
sudo make install

echo -e "${GREEN}✓ Valhalla built and installed${NC}"

cd ..

echo -e "${YELLOW}[4/5] Downloading map tiles...${NC}"

mkdir -p ${DATA_DIR}
mkdir -p ${TILES_DIR}
mkdir -p ${CONFIG_DIR}

# Download OSM data for Zimbabwe (minimal example)
echo "Downloading OpenStreetMap data for Zimbabwe..."

# Using Geofabrik OSM downloads
OSM_URL="https://download.geofabrik.de/africa/zimbabwe-latest.osm.pbf"
echo "Fetching from: $OSM_URL"

if command -v wget &> /dev/null; then
    wget -O ${DATA_DIR}/zimbabwe.osm.pbf ${OSM_URL}
elif command -v curl &> /dev/null; then
    curl -o ${DATA_DIR}/zimbabwe.osm.pbf ${OSM_URL}
fi

# Build tiles from OSM data
echo "Building routing tiles (this may take 10-30 minutes for a country)..."
valhalla_build_tiles \
    -c ${CONFIG_DIR}/valhalla.json \
    ${DATA_DIR}/zimbabwe.osm.pbf

echo -e "${GREEN}✓ Tiles built${NC}"

echo -e "${YELLOW}[5/5] Creating configuration files...${NC}"

# Create valhalla.json configuration
cat > ${CONFIG_DIR}/valhalla.json << 'EOF'
{
  "valhalla": {
    "mjolnir": {
      "data_processing": {
        "allow_alt_name": true,
        "use_urban_tag": true,
        "use_living_streets": false,
        "use_track": true,
        "allow_unpaved_roads": true,
        "use_ferry": true,
        "use_toll": true,
        "ferry_use_penalty": 0
      },
      "import_bike_share_stations": false,
      "tile_dir": "./tiles",
      "timezone": [
        {
          "tzfile": "/usr/share/zoneinfo",
          "shapefile": ""
        }
      ],
      "admin": "",
      "include_driveways": true,
      "include_construction": false,
      "include_restrictions": true
    },
    "service_limits": {
      "auto": {
        "max_distance": 100000,
        "max_locations": 20,
        "max_matrix_distance": 650000,
        "max_matrix_locations": 250
      },
      "pedestrian": {
        "max_distance": 250000,
        "max_locations": 50,
        "max_matrix_distance": 500000,
        "max_matrix_locations": 250
      },
      "bicycle": {
        "max_distance": 500000,
        "max_locations": 50,
        "max_matrix_distance": 500000,
        "max_matrix_locations": 250
      },
      "truck": {
        "max_distance": 100000,
        "max_locations": 20,
        "max_matrix_distance": 650000,
        "max_matrix_locations": 250
      },
      "bikeshare": {
        "max_distance": 15000,
        "max_locations": 4,
        "max_matrix_distance": 200000,
        "max_matrix_locations": 50
      }
    },
    "httpserver": {
      "service": {
        "listen": "0.0.0.0",
        "port": 8002
      },
      "interrupt": {
        "listen": "0.0.0.0",
        "port": 8003
      }
    },
    "logging": {
      "type": "std_out",
      "level": "info"
    }
  }
}
EOF

echo -e "${GREEN}✓ Configuration created${NC}"

# Create systemd service file
echo -e "${YELLOW}Creating systemd service...${NC}"

sudo tee /etc/systemd/system/valhalla.service > /dev/null <<EOF
[Unit]
Description=Valhalla Routing Engine
After=network.target

[Service]
Type=simple
User=valhalla
ExecStart=/usr/local/bin/valhalla_service ${CONFIG_DIR}/valhalla.json
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo useradd -m valhalla || true
sudo chown -R valhalla:valhalla ${VALHALLA_HOME}

echo -e "${GREEN}✓ Systemd service created${NC}"

echo ""
echo -e "${GREEN}✅ Valhalla installation complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Start Valhalla: sudo systemctl start valhalla"
echo "2. Enable on boot: sudo systemctl enable valhalla"
echo "3. Check status: sudo systemctl status valhalla"
echo "4. Test API: curl http://localhost:8002/route -X POST -d '{\"locations\":[{\"lat\":17.8252,\"lon\":25.2753},{\"lat\":17.8832,\"lon\":25.8232}]}'"
echo ""
echo "Configuration file: ${CONFIG_DIR}/valhalla.json"
echo "Data directory: ${DATA_DIR}"
echo "Tiles directory: ${TILES_DIR}"
