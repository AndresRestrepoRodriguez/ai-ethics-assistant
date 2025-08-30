#!/bin/bash
# user-data.sh - EC2 Instance Initialization Script
# This script runs automatically when the EC2 instance first starts
# It sets up the environment for your RAG application

# Exit on any error
set -e

# Log everything to a file for debugging
exec > >(tee -a /var/log/user-data.log)
exec 2>&1

echo "========================================="
echo "Starting EC2 Instance Setup"
echo "Time: $(date)"
echo "========================================="

# Step 1: Update the system
echo "📦 Updating system packages..."
apt-get update
apt-get upgrade -y

# Step 2: Install basic tools
echo "🔧 Installing basic tools..."
apt-get install -y \
    curl \
    wget \
    git \
    htop \
    vim \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

# Step 3: Install Docker
echo "🐳 Installing Docker..."
# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update and install Docker
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add ubuntu user to docker group (so you don't need sudo)
usermod -aG docker ubuntu

# Enable Docker to start on boot
systemctl enable docker
systemctl start docker

# Verify Docker installation
docker --version
docker compose version

# Step 4: Install Nginx (for reverse proxy)
echo "🌐 Installing Nginx..."
apt-get install -y nginx

# Create a basic nginx configuration for your app
cat > /etc/nginx/sites-available/rag-app <<'EOF'
server {
    listen 80;
    server_name _;
    
    # Main application (Gradio)
    location / {
        proxy_pass http://localhost:7860;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
    
    # API endpoints
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # API documentation
    location /docs {
        proxy_pass http://localhost:8000/docs;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # Health check endpoint
    location /internal/health {
        proxy_pass http://localhost:8000/internal/health;
        proxy_set_header Host $host;
    }
}
EOF

# Enable the site
ln -sf /etc/nginx/sites-available/rag-app /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test and restart nginx
nginx -t
systemctl restart nginx
systemctl enable nginx

# Step 5: Create application directory
echo "📁 Creating application directory..."
mkdir -p /app
chown ubuntu:ubuntu /app

# Step 6: Install AWS CLI (already available via IAM role)
echo "☁️ Installing AWS CLI..."
apt-get install -y awscli

# Step 7: Set up log rotation for Docker
echo "📝 Setting up log rotation..."
cat > /etc/docker/daemon.json <<'EOF'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF

systemctl restart docker

# Step 8: Create a helpful message for when you SSH in
cat > /etc/motd <<'EOF'

========================================
🚀 RAG Assistant Server Ready!
========================================

Quick Commands:
- cd /app                    # Go to application directory
- docker ps                  # See running containers
- docker compose logs -f     # View application logs
- docker compose restart     # Restart application
- sudo nginx -t             # Test nginx config
- sudo systemctl status nginx # Check nginx status

Next Steps:
1. Clone your repository to /app
2. Set up your .env file
3. Run: docker compose up -d

========================================

EOF

# Step 9: Set up swap space (helpful for small instances)
echo "💾 Setting up swap space..."
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' | tee -a /etc/fstab

# Step 10: Install monitoring tools (optional but helpful)
echo "📊 Installing monitoring tools..."
# Install netdata for system monitoring (optional)
# wget -O /tmp/netdata-kickstart.sh https://my-netdata.io/kickstart.sh
# sh /tmp/netdata-kickstart.sh --dont-wait

echo "========================================="
echo "✅ EC2 Instance Setup Complete!"
echo "Time: $(date)"
echo "========================================="

# Send a success signal (you can see this in EC2 console)
# This helps you know when the instance is fully ready
/opt/aws/bin/cfn-signal -e 0 --stack none --resource none --region us-east-1 || true