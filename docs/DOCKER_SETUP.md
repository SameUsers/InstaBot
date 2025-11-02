# Docker Setup Guide

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Docker Compose Services](#docker-compose-services)
4. [Configuration](#configuration)
5. [Startup Process](#startup-process)
6. [Volumes and Persistence](#volumes-and-persistence)
7. [Networking](#networking)
8. [Useful Commands](#useful-commands)
9. [Troubleshooting](#troubleshooting)
10. [Production Considerations](#production-considerations)

## Overview

InstaBot uses Docker Compose to orchestrate a multi-container application consisting of:

- **app**: FastAPI application container
- **db**: PostgreSQL 16 database
- **minio**: MinIO object storage for images

All containers are connected through a custom bridge network and use named volumes for data persistence.

## Quick Start

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- Git

### Initial Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/instabot.git
   cd instabot
   ```

2. **Create environment file**
   ```bash
   cp config/.env.example config/.env
   ```

3. **Configure environment variables**
   Edit `config/.env` with your settings:
   ```bash
   nano config/.env  # or use your preferred editor
   ```

4. **Start all services**
   ```bash
   docker compose up --build -d
   ```

5. **Verify services are running**
   ```bash
   docker compose ps
   ```

6. **Check application logs**
   ```bash
   docker compose logs -f app
   ```

### Access Points

Once running, access the following services:

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/
- **MinIO Console**: http://localhost:9001
- **MinIO API**: http://localhost:9000
- **PostgreSQL**: localhost:5432

## Docker Compose Services

### PostgreSQL Database Service

```yaml
db:
  image: postgres:16-alpine
  container_name: instabot_postgres
```

**Features**:
- PostgreSQL 16 on Alpine Linux (lightweight)
- Persistent data via `postgres_data` volume
- Health checks using `pg_isready`
- Auto-restart unless stopped
- Port 5432 exposed to host

**Configuration**:
- Database name, user, password via environment variables
- Default credentials: `postgres/postgres` (change in production!)

### MinIO Object Storage

```yaml
minio:
  image: minio/minio:latest
  container_name: instabot_minio
```

**Features**:
- S3-compatible object storage
- Auto-creates `images` bucket on startup
- Web console for management
- Persistent data via `minio_data` volume
- Ports 9000 (API) and 9001 (Console) exposed

**Configuration**:
- Root credentials via `MINIO_USER` and `MINIO_PASSWORD`
- Bucket name via `MINIO_BUCKET`
- Default: `admin/password123` (change in production!)

### FastAPI Application

```yaml
app:
  build:
    context: .
    dockerfile: Dockerfile
  container_name: instabot_app
```

**Features**:
- Multi-stage Docker build
- Automatic migrations on startup
- Runs test suite before starting
- Auto-restart unless stopped
- Health checks via FastAPI endpoint

**Configuration**:
- Environment variables from `config/.env`
- Dependencies on `db` and `minio` services
- Read-only volume mount for development

## Configuration

### Environment Variables

All configuration is done through environment variables in `config/.env`:

**Database**:
- `DB_HOST=db` - Service name in Docker network
- `DB_PORT=5432` - PostgreSQL port
- `DB_USER=postgres` - Database user
- `DB_PASSWORD=postgres` - Database password
- `DB_NAME=instagram` - Database name

**JWT Authentication**:
- `ACCESS_TOKEN_SECRET` - Secret for signing access tokens
- `REFRESH_TOKEN_SECRET` - Secret for signing refresh tokens
- `ACCESS_TOKEN_EXP=600` - Access token expiration (minutes)
- `REFRESH_TOKEN_EXP=30` - Refresh token expiration (days)

**MinIO**:
- `MINIO_HOST=minio` - Service name in Docker network
- `MINIO_PORT=9000` - MinIO API port
- `MINIO_USER=admin` - MinIO root user
- `MINIO_PASSWORD=password123` - MinIO root password
- `MINIO_BUCKET=images` - Default bucket
- `MINIO_PUBLIC_URL` - Public URL for objects (required for Instagram)

**OpenRouter AI**:
- `OPENROUTER_KEY` - Your API key
- `OPENROUTER_MODEL_KEY` - Model for text generation
- `OPENROUTER_IMAGE_MODEL_KEY` - Model for image generation

**Instagram**:
- `VERIFY_TOKEN` - Webhook verification token

See `config/.env.example` for complete list and descriptions.

### Production Settings

For production deployments:

1. **Generate strong secrets**:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Use environment-specific databases**:
   ```bash
   DB_NAME=instabot_production
   ```

3. **Configure proper CORS**:
   Update `main.py` to restrict origins

4. **Use secrets management**:
   - AWS Secrets Manager
   - HashiCorp Vault
   - Kubernetes Secrets

## Startup Process

The application follows this startup sequence:

```
┌─────────────────────────────────────────┐
│ 1. Wait for PostgreSQL                  │
│    - Health check using pg_isready      │
│    - Retries every 2 seconds            │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ 2. Run Alembic Migrations               │
│    - alembic -c config/alembic.ini      │
│    - upgrade head                        │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ 3. Run Unit Tests                       │
│    - pytest -c config/pytest.ini        │
│    - source/tests/unit/                 │
│    - Must pass to continue              │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ 4. Run Integration Tests                │
│    - source/tests/integration/          │
│    - Skip if no tests                   │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ 5. Run API Tests                        │
│    - source/tests/api/                  │
│    - Must pass to continue              │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ 6. Start FastAPI Application            │
│    - uvicorn main:app                   │
│    - Background tasks initialized       │
└─────────────────────────────────────────┘
```

**Important**: If any test fails, the container exits with error code 1.

To bypass tests during development (not recommended), modify `scripts/entrypoint.sh`.

## Volumes and Persistence

### Named Volumes

The setup uses two named volumes:

1. **postgres_data**
   - Stores PostgreSQL database files
   - Persists data between container restarts
   - Location on host: Docker-managed

2. **minio_data**
   - Stores MinIO buckets and objects
   - Persists uploaded images
   - Location on host: Docker-managed

### Accessing Volume Data

**Inspect volume**:
```bash
docker volume inspect instabot_postgres_data
docker volume inspect instabot_minio_data
```

**Backup PostgreSQL**:
```bash
docker compose exec db pg_dump -U postgres instagram > backup.sql
```

**Restore PostgreSQL**:
```bash
docker compose exec -T db psql -U postgres instagram < backup.sql
```

**Backup MinIO**:
```bash
docker compose exec minio mc mirror /data backup/
```

### Removing Data

To start fresh (⚠️ **deletes all data**):
```bash
docker compose down -v
```

## Networking

### Custom Network

All services connect to a bridge network `instabot_instabot_network`:

```yaml
networks:
  instabot_network:
    driver: bridge
```

**Benefits**:
- Services can reach each other by name
- Isolation from other Docker networks
- Automatic DNS resolution

**Service Discovery**:
- `db` → Database service
- `minio` → MinIO service
- `app` → Application service

**Network Aliases**:
Each service can be accessed by its container name or service name.

### Port Exposure

**Host → Container**:
- `8000` → `app:8000` - FastAPI
- `9000` → `minio:9000` - MinIO API
- `9001` → `minio:9001` - MinIO Console
- `5432` → `db:5432` - PostgreSQL

**Internal Communication**:
All services use internal network names.

## Useful Commands

### Container Management

```bash
# View running containers
docker compose ps

# View all containers (including stopped)
docker compose ps -a

# Start services
docker compose up -d

# Stop services
docker compose stop

# Stop and remove containers
docker compose down

# Rebuild without cache
docker compose build --no-cache

# Pull latest images
docker compose pull
```

### Logs

```bash
# All services
docker compose logs

# Specific service
docker compose logs app
docker compose logs db
docker compose logs minio

# Follow logs (tail -f)
docker compose logs -f app

# Last 100 lines
docker compose logs --tail=100 app

# Since specific time
docker compose logs --since 10m app
```

### Executing Commands

```bash
# Open bash in container
docker compose exec app bash

# Run specific command
docker compose exec app python
docker compose exec db psql -U postgres

# Check environment
docker compose exec app env

# Run migrations manually
docker compose exec app alembic -c config/alembic.ini upgrade head
```

### Database Operations

```bash
# Connect to PostgreSQL
docker compose exec db psql -U postgres -d instagram

# Create backup
docker compose exec db pg_dump -U postgres instagram > backup_$(date +%Y%m%d).sql

# Restore backup
docker compose exec -T db psql -U postgres instagram < backup.sql

# View database size
docker compose exec db psql -U postgres -c "SELECT pg_size_pretty(pg_database_size('instagram'));"
```

### Testing

```bash
# Run all tests
docker compose exec app pytest -c config/pytest.ini

# Run specific test file
docker compose exec app pytest -c config/pytest.ini source/tests/api/test_auth.py

# Run with coverage
docker compose exec app pytest -c config/pytest.ini --cov=source --cov-report=html

# Run specific test
docker compose exec app pytest -c config/pytest.ini -k "test_login"
```

## Troubleshooting

### Common Issues

#### 1. Port Already in Use

**Error**: `Bind for 0.0.0.0:8000 failed: port is already allocated`

**Solution**: Either stop the service using the port or change the mapping:

```yaml
ports:
  - "8001:8000"  # Use 8001 instead of 8000
```

#### 2. Database Connection Failed

**Error**: `could not connect to server`

**Solutions**:
- Check if PostgreSQL container is healthy: `docker compose ps`
- Verify database credentials in `config/.env`
- Check database logs: `docker compose logs db`
- Wait longer for DB to start (add retry logic)

#### 3. MinIO Bucket Not Created

**Error**: Bucket doesn't exist

**Solutions**:
- Check MinIO logs: `docker compose logs minio`
- Verify entrypoint.sh has bucket creation
- Manually create bucket via Console

#### 4. Tests Failing

**Error**: Container exits with code 1

**Solutions**:
- Check test output: `docker compose logs app | grep -A 50 "FAILED"`
- Verify database is accessible
- Check environment variables are set correctly
- Run tests outside Docker to debug

#### 5. Out of Memory

**Error**: Containers killed or slow

**Solutions**:
- Increase Docker memory limit
- Reduce concurrent operations
- Optimize queries
- Use lightweight images (Alpine)

### Debugging Tips

**Enable verbose output**:
```bash
docker compose up --verbose
```

**Inspect container**:
```bash
docker compose exec app sh  # Alpine doesn't have bash
```

**Check resource usage**:
```bash
docker stats
```

**View network configuration**:
```bash
docker network inspect instabot_instabot_network
```

## Production Considerations

### Security

1. **Change default passwords** for all services
2. **Use secrets management** instead of .env files
3. **Enable HTTPS** with reverse proxy (Nginx/Traefik)
4. **Restrict network access** to database
5. **Regular security updates** for base images
6. **Backup encryption** for sensitive data

### Performance

1. **Resource limits**:
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2'
         memory: 2G
   ```

2. **Database connection pooling** configured in app
3. **CDN for static assets** (MinIO objects)
4. **Horizontal scaling** of app containers
5. **Read replicas** for database

### Monitoring

1. **Health checks** configured for all services
2. **Structured logging** with Loguru
3. **Metrics collection** (Prometheus/DataDog)
4. **Alerting** for failures
5. **Log aggregation** (ELK/Loki)

### Backup Strategy

1. **Daily database backups** to S3
2. **Point-in-time recovery** enabled
3. **MinIO replication** to secondary region
4. **Test restore procedures** monthly
5. **Automated backup verification**

### High Availability

1. **Multiple app instances** behind load balancer
2. **Database replication** (primary + standby)
3. **MinIO clustering** for object storage
4. **Auto-restart policies** configured
5. **Health check orchestration**

### Scaling

**Vertical**: Increase resources per container

**Horizontal**: Add more app containers
```bash
docker compose up --scale app=3
```

**Database**: Use managed PostgreSQL service (AWS RDS, etc.)

**Storage**: Use managed S3 instead of MinIO

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Docker Hub](https://hub.docker.com/_/postgres)
- [MinIO Documentation](https://min.io/docs/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
