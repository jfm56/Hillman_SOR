# Server Deployment Guide

## Quick Start

### 1. Copy files to server

```bash
# From your local machine, copy the project to your server
scp -r /path/to/sor-ai-system user@YOUR_SERVER_IP:~/hillmann-ai
```

Or clone from git on the server:
```bash
ssh user@YOUR_SERVER_IP
git clone https://github.com/jfm56/Hillman_SOR.git hillmann-ai
cd hillmann-ai
```

### 2. Run the deployment script

```bash
cd hillmann-ai
./deploy.sh
```

The script will:
- Install Docker if needed
- Create secure `.env` file
- Build and start all services
- Pull the AI models

### 3. Access the application

- **URL**: `http://YOUR_SERVER_IP`
- **Admin login**: `admin@hillmann.com` / `admin123`

⚠️ **Change the admin password after first login!**

---

## Manual Deployment

If you prefer manual steps:

### Prerequisites

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Log out and back in

# Install Docker Compose plugin
sudo apt-get update
sudo apt-get install -y docker-compose-plugin
```

### Configure Environment

```bash
cp .env.example .env
nano .env
```

Update these values:
```
POSTGRES_PASSWORD=your_secure_password
SECRET_KEY=generate_with_openssl_rand_hex_32
API_URL=http://YOUR_SERVER_IP
CORS_ORIGINS=http://YOUR_SERVER_IP
```

### Start Services

```bash
# Create directories
mkdir -p storage/templates models ssl

# Build and start
docker compose -f docker-compose.prod.yml up -d --build

# Pull AI models
docker exec sor_ollama ollama pull llama3.2
docker exec sor_ollama ollama pull nomic-embed-text
```

---

## Server Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU      | 4 cores | 8 cores     |
| RAM      | 8 GB    | 16 GB       |
| Storage  | 20 GB   | 50 GB       |
| OS       | Ubuntu 20.04+ | Ubuntu 22.04 |

> **Note**: The Ollama LLM requires significant RAM. 8GB is minimum, 16GB recommended.

---

## Useful Commands

```bash
# View logs
docker compose -f docker-compose.prod.yml logs -f

# View specific service logs
docker compose -f docker-compose.prod.yml logs -f backend

# Restart services
docker compose -f docker-compose.prod.yml restart

# Stop all services
docker compose -f docker-compose.prod.yml down

# Update and redeploy
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

---

## Firewall Setup

```bash
# Allow HTTP
sudo ufw allow 80/tcp

# Allow HTTPS (if using SSL)
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable
```

---

## Adding SSL (HTTPS)

For production with a domain name:

```bash
# Install certbot
sudo apt-get install certbot

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com

# Copy certs to ssl directory
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/
```

Then update `nginx.conf` to enable HTTPS.

---

## Troubleshooting

### Services won't start
```bash
docker compose -f docker-compose.prod.yml logs
```

### Out of memory
The Ollama container needs ~4-6GB RAM. Reduce memory usage:
```bash
# Edit docker-compose.prod.yml, reduce memory limit
deploy:
  resources:
    limits:
      memory: 4G
```

### Database connection issues
```bash
docker compose -f docker-compose.prod.yml restart db
docker compose -f docker-compose.prod.yml restart backend
```

### Reset everything
```bash
docker compose -f docker-compose.prod.yml down -v
docker system prune -a
./deploy.sh
```
