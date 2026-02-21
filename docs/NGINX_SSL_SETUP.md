# NGINX Reverse Proxy + SSL Setup

## Architecture

```
User → VPN → HTTPS (443)
                ↓
            NGINX (SSL Termination)
                ↓
         ┌──────┴──────┐
         ↓             ↓
    Next.js        FastAPI
    (3000)         (8000)
```

## Option 1: System NGINX (Recommended for Production)

### Step 1: Install NGINX

```bash
sudo apt update
sudo apt install nginx
```

### Step 2: Generate Self-Signed SSL Certificate

For internal VPN-only access:

```bash
sudo openssl req -x509 -nodes -days 365 \
  -newkey rsa:2048 \
  -keyout /etc/ssl/private/hillmann.key \
  -out /etc/ssl/certs/hillmann.crt \
  -subj "/C=US/ST=State/L=City/O=Hillmann/CN=192.168.171.61"
```

### Step 3: Create NGINX Site Configuration

```bash
sudo nano /etc/nginx/sites-available/sor-app
```

Paste this configuration:

```nginx
upstream frontend {
    server 127.0.0.1:3000;
}

upstream backend {
    server 127.0.0.1:8000;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name 192.168.171.61 sor.hillmann.local;
    return 301 https://$host$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name 192.168.171.61 sor.hillmann.local;

    # SSL certificates
    ssl_certificate /etc/ssl/certs/hillmann.crt;
    ssl_certificate_key /etc/ssl/private/hillmann.key;

    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for AI operations
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # Large file uploads
        client_max_body_size 50M;
    }

    # WebSocket endpoint
    location /api/v1/ws {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }

    # Health check
    location /health {
        return 200 'OK';
        add_header Content-Type text/plain;
    }
}
```

### Step 4: Enable the Site

```bash
sudo ln -s /etc/nginx/sites-available/sor-app /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # Remove default site
sudo nginx -t  # Test configuration
sudo systemctl reload nginx
```

### Step 5: Update Docker Compose

Edit `docker-compose.prod.yml` to expose ports directly (no Docker NGINX):

```yaml
services:
  frontend:
    ports:
      - "127.0.0.1:3000:3000"
  
  backend:
    ports:
      - "127.0.0.1:8000:8000"
```

Remove or comment out the nginx service in docker-compose.prod.yml.

### Step 6: Firewall Configuration

```bash
sudo ufw allow 443/tcp
sudo ufw allow 80/tcp  # For redirect
sudo ufw reload
```

---

## Option 2: Docker NGINX with SSL

If you prefer to keep NGINX in Docker:

### Step 1: Create SSL Directory and Certificates

```bash
mkdir -p /home/jim/sor-ai-system/ssl
cd /home/jim/sor-ai-system/ssl

openssl req -x509 -nodes -days 365 \
  -newkey rsa:2048 \
  -keyout hillmann.key \
  -out hillmann.crt \
  -subj "/C=US/ST=State/L=City/O=Hillmann/CN=192.168.171.61"
```

### Step 2: Update docker-compose.prod.yml

```yaml
nginx:
  image: nginx:alpine
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./nginx-ssl.conf:/etc/nginx/nginx.conf:ro
    - ./ssl/hillmann.crt:/etc/ssl/certs/hillmann.crt:ro
    - ./ssl/hillmann.key:/etc/ssl/private/hillmann.key:ro
  depends_on:
    - frontend
    - backend
```

### Step 3: Deploy

```bash
docker-compose -f docker-compose.prod.yml up -d
```

---

## Verification

```bash
# Test HTTPS
curl -k https://192.168.171.61/health

# Test API
curl -k https://192.168.171.61/api/v1/health

# Check certificate
openssl s_client -connect 192.168.171.61:443 -servername 192.168.171.61
```

---

## Troubleshooting

### Certificate Warnings in Browser
Since this is a self-signed certificate, browsers will show a warning. Users can:
1. Click "Advanced" → "Proceed to site"
2. Add an exception for the certificate

### Check NGINX Status
```bash
sudo systemctl status nginx
sudo nginx -t
sudo tail -f /var/log/nginx/error.log
```

### Check Docker Logs
```bash
docker logs sor_nginx
docker logs sor_backend
docker logs sor_frontend
```
