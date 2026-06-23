# Tif2PDF

A Django-based TIFF-to-PDF conversion service deployed with Docker Compose.

## Requirements

- Docker Engine or Docker Desktop
- Docker Compose v2+
- At least 2GB RAM available
- Ports open: `8000`, `5432`, `5672`, `15672`

## Deployment

From the project root, start all services:

```bash
docker compose up -d --pull always
```

This starts:
- `web` (Django application)
- `celery` worker
- `celery-beat` scheduler
- `postgres` database
- `rabbitmq` message broker

## Database setup

After the first deployment or when new migrations exist, run:

```bash
docker compose exec web python manage.py migrate
```

## Create admin user (optional)

```bash
docker compose exec web python manage.py createsuperuser
```

## Verify deployment

Check containers:

```bash
docker compose ps
```

Check the web app:

```bash
curl http://localhost:8000
```

Check RabbitMQ management UI:

- `http://localhost:15672`
- username: `guest`
- password: `guest`

## Updating code

Rebuild and restart the web service only:

```bash
docker compose build web
docker compose up --no-deps -d web
```

Rebuild everything:

```bash
docker compose build
docker compose up -d
```

## Service management

View logs:

```bash
docker compose logs -f web
```

Restart a service:

```bash
docker compose restart web
```

Stop all services:

```bash
docker compose stop
```

Start stopped services:

```bash
docker compose start
```

Stop and remove containers (keep volumes):

```bash
docker compose down
```

Stop and remove containers and volumes:

```bash
docker compose down -v
```

## Notes

The Docker Compose configuration defines environment variables for PostgreSQL, RabbitMQ, Django, and Celery in `docker-compose.yml`.
