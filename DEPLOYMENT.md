# Tif2PDF Deployment Guide

## Overview
This guide provides step-by-step instructions for deploying the Tif2PDF application using Docker Compose with images pulled from GitHub Container Registry (GHCR). PostgreSQL and RabbitMQ are run as separate standalone containers.

---

## Prerequisites

- Docker Desktop or Docker Engine installed
- GitHub Account with access to the repository
- `GITHUB_TOKEN` with `read:packages` permission (for private registries)
- Docker Compose v1.29+

---

## Step 1: Authenticate with GitHub Container Registry

If your GHCR repository is private, authenticate Docker with your GitHub token:

```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u <your-github-username> --password-stdin
```

Or interactively:

```bash
docker login ghcr.io
```

When prompted:
- **Username:** Your GitHub username
- **Password:** Your GitHub Personal Access Token (with `read:packages` scope)

---

## Step 2: Start PostgreSQL Container (Standalone)

Run PostgreSQL as a separate container:

```bash
docker run -d \
  --name postgres-db \
  -e POSTGRES_USER=dbuser \
  -e POSTGRES_PASSWORD=dbpass123 \
  -e POSTGRES_DB=mydb \
  -p 5433:5432 \
  postgres:latest
```

**Verify it's running:**

```bash
docker ps --filter "name=postgres-db"
```

---

## Step 3: Start RabbitMQ Container (Standalone)

Run RabbitMQ as a separate container:

```bash
docker run -d \
  --hostname rabbit \
  --name rabbitmq \
  -p 5672:5672 \
  -p 15672:15672 \
  rabbitmq:3-management
```

**Verify it's running:**

```bash
docker ps --filter "name=rabbitmq"
```

**Access RabbitMQ Management UI:**
- URL: `http://localhost:15672`
- Username: `guest`
- Password: `guest`

---

## Step 4: Update docker-compose.yml

Update your `docker-compose.yml` to pull images from GHCR instead of building locally. Replace `<your-github-username>` with your actual GitHub username:

```yaml
version: '3.8'

services:
  web:
    image: ghcr.io/<your-github-username>/tif2pdf:latest
    pull_policy: always
    container_name: tif2pdf_web
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - ./test_files:/app/data/mnt
    ports:
      - "8000:8000"
    environment:
      - CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672//
      - CELERY_RESULT_BACKEND=rpc://
      - DATA_MOUNT_PATH=/app/data/mnt
      - DATABASE_URL=postgresql://dbuser:dbpass123@host.docker.internal:5433/mydb
    networks:
      - tif2pdf_network
    depends_on:
      - rabbitmq

  celery:
    image: ghcr.io/<your-github-username>/tif2pdf:latest
    pull_policy: always
    container_name: tif2pdf_celery
    command: celery -A tif2pdf worker --loglevel=info
    volumes:
      - ./test_files:/app/data/mnt
    environment:
      - CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672//
      - CELERY_RESULT_BACKEND=rpc://
      - DATA_MOUNT_PATH=/app/data/mnt
      - DATABASE_URL=postgresql://dbuser:dbpass123@host.docker.internal:5433/mydb
    networks:
      - tif2pdf_network
    depends_on:
      - rabbitmq

  celery-beat:
    image: ghcr.io/<your-github-username>/tif2pdf:latest
    pull_policy: always
    container_name: tif2pdf_celery_beat
    command: celery -A tif2pdf beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    volumes:
      - ./test_files:/app/data/mnt
    environment:
      - CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672//
      - CELERY_RESULT_BACKEND=rpc://
      - DATA_MOUNT_PATH=/app/data/mnt
      - DATABASE_URL=postgresql://dbuser:dbpass123@host.docker.internal:5433/mydb
    networks:
      - tif2pdf_network
    depends_on:
      - rabbitmq

networks:
  tif2pdf_network:
    driver: bridge
```

**Key Changes:**
- `image:` replaces `build:`
- `pull_policy: always` ensures latest image is pulled on every `docker compose up`
- `host.docker.internal` connects Docker containers to host PostgreSQL on port 5433
- Removed `rabbitmq` service (runs standalone)

---

## Step 5: Start Application Services via Docker Compose

Pull latest images and start the application:

```bash
docker compose up -d --pull always
```

**Verify services are running:**

```bash
docker compose ps
```

Expected output:
```
NAME                    STATUS
tif2pdf_web             Up (Healthy)
tif2pdf_celery          Up
tif2pdf_celery_beat     Up
```

---

## Step 6: Verify Connectivity

### Check web application:
```bash
curl http://localhost:8000
```

### Check Celery logs:
```bash
docker compose logs celery -f
```

### Check web logs:
```bash
docker compose logs web -f
```

### Verify PostgreSQL connection:
```bash
docker exec postgres-db psql -U dbuser -d mydb -c "SELECT 1;"
```

### Verify RabbitMQ connection:
```bash
docker exec rabbitmq rabbitmq-diagnostics -q ping
```

---

## Stopping All Services

### Stop Docker Compose services:
```bash
docker compose down
```

### Stop standalone containers:
```bash
docker stop postgres-db rabbitmq
```

### Remove all (including data):
```bash
docker compose down
docker rm postgres-db rabbitmq
docker volume prune
```

---

## Useful Commands

### Pull specific image version by commit SHA:
```bash
docker compose pull
```

### View running containers:
```bash
docker ps
```

### View all containers (including stopped):
```bash
docker ps -a
```

### Restart a service:
```bash
docker compose restart web
```

### Execute command in running container:
```bash
docker compose exec web python manage.py migrate
```

### View logs for all services:
```bash
docker compose logs -f
```

### Re-pull and recreate all services:
```bash
docker compose up -d --pull always --force-recreate
```

---

## Troubleshooting

### Images not pulling:
- Ensure you're logged in: `docker login ghcr.io`
- Verify GitHub username is correct in image URL
- Check token has `read:packages` permission

### Connection refused to PostgreSQL:
- Verify `postgres-db` is running: `docker ps --filter "name=postgres-db"`
- Check port mapping: `docker port postgres-db`
- Use `host.docker.internal` (not `localhost`) from Docker containers

### Connection refused to RabbitMQ:
- Verify `rabbitmq` is running: `docker ps --filter "name=rabbitmq"`
- Check port mapping: `docker port rabbitmq`
- Access management UI: `http://localhost:15672` (guest/guest)

### Celery not processing tasks:
- Check broker URL environment variable
- Verify RabbitMQ is running and accessible
- Review celery logs: `docker compose logs celery`

---

## Environment Variables

Update these in `docker-compose.yml` if needed:

| Variable | Default | Purpose |
|----------|---------|---------|
| `CELERY_BROKER_URL` | `amqp://guest:guest@rabbitmq:5672//` | RabbitMQ connection |
| `CELERY_RESULT_BACKEND` | `rpc://` | Celery result storage |
| `DATA_MOUNT_PATH` | `/app/data/mnt` | Application data mount point |
| `DATABASE_URL` | `postgresql://dbuser:dbpass123@host.docker.internal:5433/mydb` | PostgreSQL connection |

---

## Security Notes

- **Never commit** `GITHUB_TOKEN` or database passwords to version control
- Use `.env` files for sensitive data in production
- Change default RabbitMQ credentials (`guest:guest`) in production
- Use strong PostgreSQL passwords
- Keep images updated: `docker compose pull`
