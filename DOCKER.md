# LearnForge — Docker Setup

## Directory structure

```
learnforge/                   ← project root (put this folder anywhere)
├── docker-compose.yml        ← the whole stack in one file
├── Dockerfile.api            ← Django + Celery image
├── Dockerfile.web            ← Vue build + Nginx image
├── .env.example              ← copy to .env and fill in
├── .env                      ← your secrets (never commit this)
├── nginx/
│   └── nginx.conf            ← Nginx config (proxies /api, serves /media)
├── learnforge_api/           ← Django project (your existing code)
└── learnforge_web/           ← Vue project (your existing code)
```

---

## First-time setup

```bash
# 1. Copy and fill in environment variables
cp .env.example .env
# Edit .env — set SECRET_KEY, DB_PASSWORD, ALLOWED_HOSTS, CORS_ALLOWED_ORIGINS

# 2. Build and start all containers
docker-compose up --build -d

# 3. Create the first teacher account
docker-compose exec api python manage.py create_teacher \
  --email teacher@yourschool.com \
  --name "Your Name" \
  --password "yourpassword"

# 4. Open the app
# http://localhost  (or whatever WEB_PORT is set to in .env)
```

---

## Daily commands

```bash
# Start everything
docker-compose up -d

# Stop everything
docker-compose down

# View all logs
docker-compose logs -f

# View logs for one service
docker-compose logs -f api
docker-compose logs -f worker
docker-compose logs -f web

# Restart one service (e.g. after a code change)
docker-compose restart api

# Rebuild and restart after code changes
docker-compose up --build -d api worker

# Run a Django management command
docker-compose exec api python manage.py <command>

# Open a Django shell
docker-compose exec api python manage.py shell

# Run migrations manually
docker-compose exec api python manage.py migrate

# Open a PostgreSQL shell
docker-compose exec db psql -U learnforge_user -d learnforge
```

---

## Update the application

When you push new code:

```bash
# Rebuild changed services and redeploy with zero downtime
docker-compose up --build -d api worker web
```

Docker Compose only rebuilds images that changed. Existing containers keep
running while new ones start.

---

## Portainer setup

1. Install Portainer on your server:
```bash
docker volume create portainer_data
docker run -d -p 9000:9000 \
  --name portainer \
  --restart=unless-stopped \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v portainer_data:/data \
  portainer/portainer-ce
```

2. Open Portainer at `http://your-server:9000`
3. Go to **Stacks** → **Add stack** → **Upload** → select `docker-compose.yml`
4. Add environment variables in the Portainer UI (same as `.env`)
5. Deploy — Portainer manages the whole stack from the web UI

---

## Data persistence

All important data lives in Docker named volumes:

| Volume | Contains | Backup command |
|---|---|---|
| `postgres_data` | All database data | `docker-compose exec db pg_dump -U learnforge_user learnforge > backup.sql` |
| `media_files` | Uploaded videos, HLS segments | `docker cp $(docker-compose ps -q api):/app/media ./media-backup` |
| `redis_data` | Celery task queue (ephemeral, safe to lose) | Not needed |

Volumes survive `docker-compose down`. Only `docker-compose down -v` deletes them.

---

## Production checklist

- [ ] `SECRET_KEY` is a long random string (50+ chars)
- [ ] `DEBUG=False` in `.env`
- [ ] `DB_PASSWORD` is strong and unique
- [ ] `ALLOWED_HOSTS` includes your domain
- [ ] `CORS_ALLOWED_ORIGINS` includes your frontend URL
- [ ] `WEB_PORT=80` (or 443 with SSL — see SSL section below)
- [ ] Portainer is password-protected
- [ ] Regular database backups scheduled

---

## SSL / HTTPS (optional but recommended for production)

Add a reverse proxy container in front of Nginx using Caddy — it handles
SSL certificates from Let's Encrypt automatically:

Add to `docker-compose.yml`:

```yaml
  caddy:
    image: caddy:alpine
    restart: unless-stopped
    networks: [learnforge]
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
    depends_on: [web]

volumes:
  caddy_data:
```

Create `Caddyfile`:
```
yourdomain.com {
    reverse_proxy web:80
}
```

Change `WEB_PORT` to something other than 80 (e.g. 8080) since Caddy now owns port 80/443.
