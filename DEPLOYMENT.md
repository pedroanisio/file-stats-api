# File Stats API - Deployment Guide

This guide explains how to deploy the File Stats API using Docker and Docker Compose.

## 🚀 Quick Start

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- `curl` (for health checks)

### Simple Deployment

1. **Clone and navigate to the project:**
```bash
git clone <repository-url>
cd file-stats-api
```

2. **Deploy using the script:**
```bash
./deploy.sh
```

3. **Access the API:**
- API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- Redoc: http://localhost:8000/redoc

## 📋 Deployment Options

### Option 1: Using the Deployment Script (Recommended)

The `deploy.sh` script provides several commands:

```bash
# Deploy the API (default)
./deploy.sh deploy

# Deploy with Traefik reverse proxy
./deploy.sh deploy-traefik

# Check status
./deploy.sh status

# View logs
./deploy.sh logs

# Stop services
./deploy.sh stop

# Restart services
./deploy.sh restart

# Complete cleanup
./deploy.sh cleanup
```

### Option 2: Manual Docker Compose

```bash
# Basic deployment
docker-compose up -d file-stats-api

# With Traefik reverse proxy
docker-compose --profile traefik up -d

# Production deployment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 🔧 Configuration

### Volume Mounts

The API needs access to directories you want to analyze. Configure volume mounts in `docker-compose.yml`:

```yaml
volumes:
  # Mount host directories (read-only recommended)
  - /home:/mnt/home:ro
  - /var/log:/mnt/logs:ro
  - /opt:/mnt/opt:ro
  - ./data:/data:rw  # Local data directory
```

### Environment Variables

Key environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `production` | Environment name |
| `LOG_LEVEL` | `info` | Logging level |
| `TZ` | `UTC` | Timezone |
| `API_WORKERS` | `1` | Number of worker processes |

### Resource Limits

Adjust resource limits in `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      memory: 512M
      cpus: '0.5'
    reservations:
      memory: 256M  
      cpus: '0.25'
```

## 🏗️ Architecture

### Components

1. **File Stats API** - Main FastAPI application
2. **Traefik** (Optional) - Reverse proxy and load balancer
3. **Volumes** - Host filesystem mounts

### Security Features

- Non-root user execution
- Read-only root filesystem (production)
- Capability dropping
- No new privileges
- Secure volume mounts

## 🌐 Production Deployment

### Using Production Configuration

```bash
# Deploy with production overrides
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Production Checklist

- [ ] Configure proper volume mounts
- [ ] Set up SSL/TLS certificates
- [ ] Configure monitoring and logging
- [ ] Set resource limits
- [ ] Enable security hardening
- [ ] Configure backups
- [ ] Set up health monitoring

### SSL/TLS Configuration

For HTTPS in production, configure Traefik with Let's Encrypt:

1. Update `docker-compose.prod.yml`:
```yaml
- --certificatesresolvers.letsencrypt.acme.email=your@email.com
```

2. Add labels to your service:
```yaml
labels:
  - "traefik.http.routers.api.tls.certresolver=letsencrypt"
```

## 📊 Monitoring

### Health Checks

The API includes built-in health checks:

```bash
# Check API health
curl http://localhost:8000/

# Check container health
docker-compose ps
```

### Logs

View application logs:

```bash
# Follow logs
./deploy.sh logs

# Or directly with Docker
docker-compose logs -f file-stats-api
```

## 🔍 Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   # Ensure the deploy script is executable
   chmod +x deploy.sh
   ```

2. **Port Already in Use**
   ```bash
   # Check what's using port 8000
   lsof -i :8000
   
   # Stop conflicting services or change port
   ```

3. **Volume Mount Issues**
   ```bash
   # Verify host paths exist and are accessible
   ls -la /path/to/mount
   
   # Check container permissions
   docker-compose exec file-stats-api ls -la /mnt/
   ```

### Debug Mode

Enable debug logging:

```bash
# Set environment variable
LOG_LEVEL=debug docker-compose up -d
```

## 🔄 Updates and Maintenance

### Updating the Application

```bash
# Stop services
./deploy.sh stop

# Pull latest code
git pull

# Rebuild and deploy
./deploy.sh deploy
```

### Database Migrations

If you add database functionality later:

```bash
# Run migrations
docker-compose exec file-stats-api python manage.py migrate
```

## 📈 Scaling

### Horizontal Scaling

```bash
# Scale to multiple instances
docker-compose up -d --scale file-stats-api=3
```

### Load Balancing

Traefik automatically load balances between multiple instances.

## 🛡️ Security Considerations

1. **File System Access**: Mount only necessary directories
2. **Network Security**: Use proper firewall rules
3. **Container Security**: Regular image updates
4. **Secrets Management**: Use Docker secrets for sensitive data
5. **SSL/TLS**: Always use HTTPS in production

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Traefik Documentation](https://doc.traefik.io/traefik/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)

## 🆘 Support

For deployment issues:

1. Check the logs: `./deploy.sh logs`
2. Verify configuration: `./deploy.sh status`
3. Review this guide
4. Check the main README.md 