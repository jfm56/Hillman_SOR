#!/bin/bash
set -e

echo "=========================================="
echo "  Hillmann AI System - Server Deployment"
echo "=========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}Note: Some commands may require sudo${NC}"
fi

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker not found. Installing...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo -e "${GREEN}Docker installed. Please log out and back in, then run this script again.${NC}"
    exit 1
fi

# Check for Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}Docker Compose not found. Installing...${NC}"
    sudo apt-get update
    sudo apt-get install -y docker-compose-plugin
fi

# Check for .env file
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file from template...${NC}"
    cp .env.example .env
    
    # Generate secure secret key
    SECRET_KEY=$(openssl rand -hex 32)
    sed -i "s/change-this-to-a-secure-random-string/$SECRET_KEY/" .env
    
    # Generate secure database password
    DB_PASS=$(openssl rand -hex 16)
    sed -i "s/changeme_secure_password/$DB_PASS/" .env
    
    echo -e "${YELLOW}Please edit .env and set your server IP:${NC}"
    echo "  nano .env"
    echo ""
    echo "Update these values:"
    echo "  API_URL=http://YOUR_SERVER_IP"
    echo "  CORS_ORIGINS=http://YOUR_SERVER_IP"
    echo ""
    read -p "Press Enter after editing .env to continue..."
fi

# Create required directories
echo -e "${GREEN}Creating directories...${NC}"
mkdir -p storage/templates models ssl

# Pull images first
echo -e "${GREEN}Pulling Docker images...${NC}"
docker compose -f docker-compose.prod.yml pull

# Build and start services
echo -e "${GREEN}Building and starting services...${NC}"
docker compose -f docker-compose.prod.yml up -d --build

# Wait for services to be healthy
echo -e "${GREEN}Waiting for services to start...${NC}"
sleep 10

# Pull the Ollama model
echo -e "${GREEN}Pulling Ollama model (this may take a few minutes)...${NC}"
docker exec sor_ollama ollama pull llama3.2
docker exec sor_ollama ollama pull nomic-embed-text

# Show status
echo ""
echo -e "${GREEN}=========================================="
echo "  Deployment Complete!"
echo "==========================================${NC}"
echo ""
docker compose -f docker-compose.prod.yml ps
echo ""
echo -e "Access the application at: ${GREEN}http://$(curl -s ifconfig.me 2>/dev/null || echo 'YOUR_SERVER_IP')${NC}"
echo ""
echo "Default admin login:"
echo "  Email: admin@hillmann.com"
echo "  Password: admin123"
echo ""
echo -e "${YELLOW}IMPORTANT: Change the admin password after first login!${NC}"
