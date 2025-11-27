# Docker Deployment Guide

This guide covers deploying the Bybit Volume Scanner using Docker.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/Tchekda/HockeyPenStats.git
cd HockeyPenStats/bybit

# Start with Docker Compose
docker-compose up -d

# Access the web interface
open http://localhost:5000
```

## Prerequisites

- Docker 20.10 or later
- Docker Compose 2.0 or later (optional, but recommended)

## Using Docker Compose (Recommended)

### Start the Service

```bash
docker-compose up -d
```

### View Logs

```bash
# Follow logs
docker-compose logs -f

# View last 100 lines
docker-compose logs --tail=100
```

### Stop the Service

```bash
docker-compose down
```

### Restart the Service

```bash
docker-compose restart
```

### Update to Latest Version

```bash
# Pull latest image
docker-compose pull

# Restart with new image
docker-compose up -d
```

## Using Docker Directly

### Build from Source

```bash
docker build -t bybit-scanner .
```

### Run the Container

```bash
docker run -d \
  --name bybit-scanner \
  -p 5000:5000 \
  -v $(pwd)/data:/app/data \
  --restart unless-stopped \
  bybit-scanner
```

### Using Pre-built Images

Pull from GitHub Container Registry:

```bash
docker pull ghcr.io/tchekda/hockeypen-stats/bybit-scanner:latest

docker run -d \
  --name bybit-scanner \
  -p 5000:5000 \
  -v $(pwd)/data:/app/data \
  --restart unless-stopped \
  ghcr.io/tchekda/hockeypen-stats/bybit-scanner:latest
```

## Configuration

### Environment Variables

- `DATA_FILE`: Path to volume data JSON file (default: `/app/data/volume_data.json`)

Example with custom data file:

```bash
docker run -d \
  --name bybit-scanner \
  -p 5000:5000 \
  -v $(pwd)/data:/app/data \
  -e DATA_FILE=/app/data/custom_volume.json \
  bybit-scanner
```

### Volume Mounts

The container uses a volume mount for persistent data:

```bash
-v $(pwd)/data:/app/data
```

This ensures your volume history survives container restarts and updates.

### Port Mapping

By default, the web interface runs on port 5000. To use a different port:

```bash
docker run -d \
  --name bybit-scanner \
  -p 8080:5000 \  # Maps host port 8080 to container port 5000
  -v $(pwd)/data:/app/data \
  bybit-scanner
```

Then access at `http://localhost:8080`

## Management Commands

### View Container Logs

```bash
docker logs -f bybit-scanner
```

### Stop Container

```bash
docker stop bybit-scanner
```

### Start Container

```bash
docker start bybit-scanner
```

### Restart Container

```bash
docker restart bybit-scanner
```

### Remove Container

```bash
docker stop bybit-scanner
docker rm bybit-scanner
```

### Execute Commands Inside Container

```bash
# Open a shell
docker exec -it bybit-scanner /bin/bash

# View volume data
docker exec bybit-scanner cat /app/data/volume_data.json

# Check Python version
docker exec bybit-scanner python --version
```

## Health Checks

The Docker Compose configuration includes a health check:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:5000/api/status"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

Check health status:

```bash
docker inspect --format='{{.State.Health.Status}}' bybit-scanner
```

## Troubleshooting

### Container Won't Start

Check logs:
```bash
docker logs bybit-scanner
```

### Permission Issues with Volume

Ensure the data directory is writable:
```bash
mkdir -p data
chmod 755 data
```

### Port Already in Use

Change the port mapping:
```bash
docker run -d -p 5001:5000 ...  # Use port 5001 instead
```

### Container Keeps Restarting

Check health status and logs:
```bash
docker ps -a
docker logs bybit-scanner
```

### Clear All Data

```bash
# Stop and remove container
docker-compose down

# Remove data directory
rm -rf data

# Start fresh
docker-compose up -d
```

## Production Deployment

### Using Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml bybit

# List services
docker stack services bybit

# Remove stack
docker stack rm bybit
```

### Using Kubernetes

Example Kubernetes deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bybit-scanner
spec:
  replicas: 1
  selector:
    matchLabels:
      app: bybit-scanner
  template:
    metadata:
      labels:
        app: bybit-scanner
    spec:
      containers:
      - name: bybit-scanner
        image: ghcr.io/tchekda/hockeypen-stats/bybit-scanner:latest
        ports:
        - containerPort: 5000
        volumeMounts:
        - name: data
          mountPath: /app/data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: bybit-scanner-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: bybit-scanner
spec:
  selector:
    app: bybit-scanner
  ports:
  - port: 5000
    targetPort: 5000
  type: LoadBalancer
```

### Behind a Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name scanner.example.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Multi-Architecture Support

The GitHub Actions workflow builds for multiple architectures:

- `linux/amd64` (x86_64)
- `linux/arm64` (ARM 64-bit, Apple Silicon, etc.)

Pull the appropriate image for your platform:

```bash
# Docker automatically selects the correct architecture
docker pull ghcr.io/tchekda/hockeypen-stats/bybit-scanner:latest
```

## Security Considerations

### Running as Non-Root User

To run the container as a non-root user:

```bash
docker run -d \
  --user 1000:1000 \
  -p 5000:5000 \
  -v $(pwd)/data:/app/data \
  bybit-scanner
```

### Network Isolation

For additional security, use a custom network:

```bash
# Create network
docker network create bybit-network

# Run container in network
docker run -d \
  --network bybit-network \
  --name bybit-scanner \
  -p 5000:5000 \
  -v $(pwd)/data:/app/data \
  bybit-scanner
```

### Read-Only Root Filesystem

For extra security:

```bash
docker run -d \
  --read-only \
  --tmpfs /tmp \
  -p 5000:5000 \
  -v $(pwd)/data:/app/data \
  bybit-scanner
```

## Monitoring

### View Resource Usage

```bash
docker stats bybit-scanner
```

### Export Logs

```bash
docker logs bybit-scanner > scanner-logs.txt
```

### Prometheus Metrics (Future Enhancement)

Consider adding Prometheus metrics endpoint for production monitoring.

## Backup and Restore

### Backup Volume Data

```bash
# Create backup
docker run --rm \
  -v bybit_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/volume-data-backup.tar.gz -C /data .
```

### Restore Volume Data

```bash
# Restore from backup
docker run --rm \
  -v bybit_data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/volume-data-backup.tar.gz -C /data
```

## Updates

### Automated Updates with Watchtower

```bash
docker run -d \
  --name watchtower \
  -v /var/run/docker.sock:/var/run/docker.sock \
  containrrr/watchtower \
  bybit-scanner \
  --interval 300
```

This will automatically update the container every 5 minutes if a new image is available.

## Support

For issues related to Docker deployment, please open an issue on GitHub:
https://github.com/Tchekda/HockeyPenStats/issues
