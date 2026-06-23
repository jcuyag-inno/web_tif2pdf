# Tif2PDF Deployment Guide

## Overview
This guide provides step-by-step instructions for deploying the Tif2PDF application using Docker Compose. PostgreSQL, RabbitMQ, web server, Celery worker, and Celery Beat are all orchestrated via Docker Compose on a shared bridge network.

---

## Prerequisites

- Docker Desktop or Docker Engine installed
- Docker Compose v2.0+
- 2GB+ available RAM
- Ports 8000, 5432, 5672, 15672 available

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│           tif2pdf_network (bridge)                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │
│  │   postgres   │  │  rabbitmq    │  │   web       │  │
│  │   :5432      │  │  :5672       │  │   :8000     │  │
│  └──────────────┘  └──────────────┘  └─────────────┘  │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐                    │
│  │   celery     │  │ celery-beat  │                    │
│  │   worker     │  │  scheduler   │                    │
│  └──────────────┘  └──────────────┘                    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Step 1: Clone or Prepare Project

Ensure your project directory contains:
- `docker-compose.yml`
- `Dockerfile`
- `requirements.txt`
- `manage.py`
- `tif2pdf/settings.py`

---

## Step 2: Start All Services

Start all containers (Postgres, RabbitMQ, web, celery, celery-beat) in one command:

```bash
docker compose up -d --pull always
```

**What this does:**
- Pulls latest base images
- Builds the web/celery/celery-beat image from local Dockerfile
- Creates bridge network `tif2pdf_network`
- Starts all 5 services with health checks
- Respects `depends_on` conditions (web/celery wait for Postgres & RabbitMQ to be healthy)

**Verify all services are running:**

```bash
docker compose ps
```

Expected output:
```
NAME                  IMAGE                          STATUS
tif2pdf_web           tif2pdf-web                    Up (healthy)
tif2pdf_celery        tif2pdf-celery                 Up
tif2pdf_celery_beat   tif2pdf-celery-beat            Up
tif2pdf_postgres      postgres:15-alpine             Up (healthy)
tif2pdf_rabbitmq      rabbitmq:3-management-alpine   Up (healthy)
```

---

## Step 3: Run Database Migrations

On first deployment (or after adding new migrations), apply them:

```bash
docker compose exec web python manage.py migrate
```

This initializes all Django tables in PostgreSQL.

---

## Step 4: Create Admin User (Optional)

```bash
docker compose exec web python manage.py createsuperuser
```

Follow the prompts to create a Django admin account.

---

## Step 5: Verify Services and Connectivity

### Check web application:
```bash
curl http://localhost:8000
```

Expected: Django response (or admin login page)

### Check Celery worker status:
```bash
docker compose logs celery --tail 30
```

Expected: `celery@<container-id> ready.`

### Check Celery Beat status:
```bash
docker compose logs celery-beat --tail 10
```

Expected: Beat scheduler initialization logs

### Check PostgreSQL:
```bash
docker compose exec postgres psql -U postgres -d tif2pdf -c "SELECT 1;"
```

Expected: `1` (single row)

### Check RabbitMQ:
```bash
docker compose exec rabbitmq rabbitmq-diagnostics -q ping
```

Expected: `ok`

### Access RabbitMQ Management UI:
- URL: `http://localhost:15672`
- Username: `guest`
- Password: `guest`

---

## Service Environment Variables

All environment variables are configured in `docker-compose.yml`. Key variables:

| Service | Variable | Value | Purpose |
|---------|----------|-------|---------|
| web, celery, celery-beat | `DB_ENGINE` | `django.db.backends.postgresql` | Enable PostgreSQL |
| web, celery, celery-beat | `DB_HOST` | `postgres` | PostgreSQL hostname (service name) |
| web, celery, celery-beat | `DB_PORT` | `5432` | PostgreSQL port |
| web, celery, celery-beat | `DB_USER` | `postgres` | PostgreSQL user |
| web, celery, celery-beat | `DB_PASSWORD` | `postgres` | PostgreSQL password |
| web, celery, celery-beat | `DB_NAME` | `tif2pdf` | Database name |
| web, celery, celery-beat | `CELERY_BROKER_URL` | `amqp://guest:[REDACTED]@rabbitmq:5672//` | RabbitMQ broker |
| web, celery, celery-beat | `CELERY_RESULT_BACKEND` | `rpc://` | Celery result storage |
| web, celery, celery-beat | `DATA_MOUNT_PATH` | `/app/data/mnt` | Data volume mount point |
| postgres | `POSTGRES_USER` | `postgres` | Postgres superuser |
| postgres | `POSTGRES_PASSWORD` | `postgres` | Postgres password |
| postgres | `POSTGRES_DB` | `tif2pdf` | Initial database |
| rabbitmq | `RABBITMQ_DEFAULT_USER` | `guest` | RabbitMQ user |
| rabbitmq | `RABBITMQ_DEFAULT_PASS` | `guest` | RabbitMQ password |

---

## Updating Code and Rebuilding

When you make changes to application code:

### Option 1: Rebuild and restart just the web service
```bash
docker compose build web
docker compose up --no-deps -d web
```

### Option 2: Rebuild all services and restart everything
```bash
docker compose build
docker compose up -d
```

### Option 3: Use Compose Watch for automatic live reloads (development)
Add this to `docker-compose.yml` under the `web` service:

```yaml
web:
  develop:
    watch:
      - action: sync+restart
        path: .
        target: /code
```

Then run:
```bash
docker compose watch
```

---

## Managing Services

### View logs for a specific service:
```bash
docker compose logs web -f         # web server
docker compose logs celery -f      # celery worker
docker compose logs celery-beat -f # celery beat
docker compose logs postgres -f    # PostgreSQL
docker compose logs rabbitmq -f    # RabbitMQ
```

### View logs for all services:
```bash
docker compose logs -f
```

### Restart a service:
```bash
docker compose restart web          # Restart web
docker compose restart celery       # Restart celery
docker compose restart postgres     # Restart postgres
```

### Execute a command in a running container:
```bash
docker compose exec web python manage.py shell
docker compose exec web python manage.py createsuperuser
docker compose exec postgres psql -U postgres
```

### Stop all services (keep data):
```bash
docker compose stop
```

### Start stopped services:
```bash
docker compose start
```

### Stop and remove all services (keep data/volumes):
```bash
docker compose down
```

### Stop and remove everything including volumes (destroys data):
```bash
docker compose down -v
```

---

## Networking

All services communicate via the `tif2pdf_network` bridge network using service names:

- Web/Celery → Postgres: `DB_HOST=postgres:5432`
- Web/Celery → RabbitMQ: `CELERY_BROKER_URL=amqp://...@rabbitmq:5672//`
- External access:
  - Web: `http://localhost:8000`
  - RabbitMQ UI: `http://localhost:15672`
  - Postgres: `localhost:5432` (from host machine only)

---

## Data Persistence

- **Database data:** Stored in Docker volume `tif2pdf_db_data`
- **Application data:** Volume mounted at `/app/data/mnt` (map to `./test_files` by default)

View volumes:
```bash
docker volume ls | grep tif2pdf
```

Inspect volume:
```bash
docker volume inspect tif2pdf_db_data
```

---

## Production Considerations

### Security:
1. Change default RabbitMQ credentials in `docker-compose.yml`
2. Change default PostgreSQL credentials in `docker-compose.yml`
3. Use a `.env` file for sensitive variables (with `env_file:` in compose file)
4. Set `DEBUG=False` in Django settings for production
5. Use strong `SECRET_KEY`

### Performance:
1. Increase Celery worker concurrency (set `CELERY_WORKER_CONCURRENCY` in settings)
2. Scale workers horizontally by running multiple celery containers
3. Configure PostgreSQL memory and connection limits
4. Use external result backend (e.g., Redis) instead of `rpc://`

### Monitoring:
1. Use `docker compose logs` or centralized logging (ELK, Splunk, etc.)
2. Monitor container resource usage: `docker stats`
3. Set up Celery monitoring with Flower
4. Enable RabbitMQ monitoring via management UI

### Backup:
1. Back up `tif2pdf_db_data` volume regularly
2. Back up application files in `./test_files` (or mapped volume)

---

## Troubleshooting

### Services won't start
```bash
docker compose logs
```
Check for errors in log output. Common issues:
- Port already in use (change port mapping in `docker-compose.yml`)
- Insufficient memory (increase Docker memory limit)
- Old images cached (use `docker compose pull` first)

### Postgres connection refused
```bash
docker compose logs postgres
docker compose exec postgres pg_isready -U postgres
```
Verify Postgres is healthy and DNS resolution works.

### Celery not processing tasks
```bash
docker compose logs celery
```
Check that:
- Celery worker is connected to RabbitMQ
- Tasks are defined in `api/tasks.py`
- No exceptions in task execution

### RabbitMQ connection refused
```bash
docker compose logs rabbitmq
docker compose exec rabbitmq rabbitmq-diagnostics -q ping
```

### Database migrations not applied
```bash
docker compose exec web python manage.py showmigrations
docker compose exec web python manage.py migrate
```

### Out of disk space
```bash
docker system df
docker system prune -a
```

---

## Useful Commands Summary

```bash
# Start services
docker compose up -d

# Stop services
docker compose down

# View logs
docker compose logs -f

# Execute command
docker compose exec web python manage.py migrate

# Rebuild images
docker compose build

# Pull latest base images
docker compose pull

# View container status
docker compose ps

# View resource usage
docker stats

# Access database
docker compose exec postgres psql -U postgres -d tif2pdf

# Clear everything
docker compose down -v
```

---

## Environment Files (Production)

Create a `.env` file for sensitive data:

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
RABBITMQ_DEFAULT_USER=rabbit_user
RABBITMQ_DEFAULT_PASS=your_secure_password
SECRET_KEY=your_django_secret_key
DEBUG=False
```

Reference in `docker-compose.yml`:
```yaml
services:
  postgres:
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
```

Then start with:
```bash
docker compose --env-file .env up -d
```

---

## Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Django with Docker](https://docs.docker.com/language/python/develop/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [RabbitMQ Documentation](https://www.rabbitmq.com/documentation.html)
- [PostgreSQL Docker Image](https://hub.docker.com/_/postgres)
