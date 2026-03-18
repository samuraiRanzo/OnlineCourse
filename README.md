# LearnForge LMS

Online course platform with video lessons, attendance tracking, exams, and certificates.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Vue 3 + PrimeVue 4 + Pinia + Vue Router |
| Backend | Django 5 + Django REST Framework + SimpleJWT |
| Database | PostgreSQL 16 |
| Task Queue | Celery + Redis |
| Video | FFmpeg → HLS streaming |
| Reverse Proxy | Nginx |
| Containers | Docker + Docker Compose |

## Repository Structure

```
learnforge/
├── backend/            Django API + Celery worker
│   ├── learnforge/     Django project settings, URLs, Celery config
│   ├── apps/
│   │   ├── users/      Custom auth, JWT login, teacher setup
│   │   ├── courses/    Courses, lessons, Q&A, HLS video upload
│   │   ├── attendance/ Sessions, 6-char check-in codes
│   │   ├── exams/      MCQ + open answer, retake policy
│   │   ├── certificates/ Auto-issued on completion
│   │   └── announcements/ Notices with unread badges
│   ├── manage.py
│   └── requirements.txt
├── frontend/           Vue 3 SPA
│   └── src/
│       ├── stores/     Pinia: auth, courses, exams, Q&A, etc.
│       ├── views/      Admin panel + student portal
│       └── components/ Reusable UI components
├── nginx/
│   └── nginx.conf      Proxies /api → Django, serves /media directly
├── Dockerfile.api      Django + FFmpeg image (used by api + worker)
├── Dockerfile.web      Vue build + Nginx image
├── docker-compose.yml  Full stack: db, redis, api, worker, web
└── .env.example        All required environment variables
```

## Quick Start

```bash
# 1. Clone
git clone https://github.com/yourname/learnforge.git
cd learnforge

# 2. Configure
cp .env.example .env
# Edit .env — set SECRET_KEY and DB_PASSWORD at minimum

# 3. Build and start
docker-compose up --build -d

# 4. Create teacher account
docker-compose exec api python manage.py create_teacher \
  --email teacher@yourschool.com \
  --name "Your Name" \
  --password "yourpassword"

# 5. Open
# http://localhost
```

## Common Commands

```bash
# View logs
docker-compose logs -f

# Restart after code change
docker-compose up --build -d api worker web

# Run Django management command
docker-compose exec api python manage.py <command>

# Database backup
docker-compose exec db pg_dump -U learnforge_user learnforge > backup.sql

# Stop everything
docker-compose down

# Stop and delete all data (careful!)
docker-compose down -v
```

## Local Development (without Docker)

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env    # fill in local DB credentials
python manage.py migrate
python manage.py create_teacher --email admin@local.com --name Admin --password admin123
python manage.py runserver

# Celery worker (separate terminal)
celery -A learnforge worker --loglevel=info --pool=solo   # --pool=solo on Windows

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

## Portainer Deployment

1. Install Portainer on your server
2. Go to **Stacks** → **Add Stack** → paste `docker-compose.yml`
3. Add environment variables (same as `.env`)
4. Deploy

For SSL, add Caddy in front of the `web` container — see `DOCKER.md`.

## Features

- **Teacher panel:** courses, lessons (text + self-hosted video), exam builder, attendance sessions, reports, announcements
- **Student portal:** lesson viewer with hls.js video player, lesson Q&A, exam with retake policy, attendance check-in with 6-char code, certificates
- **Video pipeline:** upload → Celery → FFmpeg → HLS segments → streams via Nginx
- **Auto certificates:** issued server-side when completion conditions are met
- **First-run setup:** `/setup` screen or `create_teacher` command — no manual DB access needed
