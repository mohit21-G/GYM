# Production Deployment & Container Orchestration Guide

This guide details the complete deployment lifecycle for the **Google Fitness AI Chatbot** platform, spanning local developer workflows, Docker multi-container environments, and enterprise production deployments.

---

## Architecture Overview

```
                      +-----------------------------+
                      |       Internet Users        |
                      +--------------+--------------+
                                     |
                          HTTP:80 / HTTPS:443
                                     |
                      +--------------v--------------+
                      |        Nginx Gateway        |
                      +-------+--------------+------+
                              |              |
          /api/v1, /docs      |              |  / (SPA routing)
                              |              |
                +-------------v----+   +-----v-------------+
                |  Backend (Nest)  |   |  Frontend (React) |
                +-------+----+-----+   +-------------------+
                        |    |
           Prisma / SQL |    | Cache / PubSub
                        |    |
           +------------v-+  +--v-----------+
           | MySQL 8.0 DB |  |  Redis 7.0   |
           +--------------+  +--------------+
```

---

## 1. Local Development (Native)

### Prerequisites
- Node.js 20+ (LTS)
- npm 9+
- MySQL 8.0 Server running on port `3306`
- (Optional) Redis Server running on port `6379` (In-memory fallback activates automatically if Redis is absent)

### Step 1: Clone & Configure Environment
```bash
cp .env.example .env
```
Ensure your `DATABASE_URL` matches your local MySQL instance:
```env
DB_HOST=localhost
DB_PORT=3306
DB_USERNAME=root
DB_PASSWORD=your_mysql_password
DB_DATABASE=google-Fitness-ai-chatbot
DATABASE_URL="mysql://root:your_mysql_password@localhost:3306/google-Fitness-ai-chatbot"
```

### Step 2: Database Migration & Seeding
```bash
cd backend
npm install
npx prisma generate
npx prisma db push
npm run prisma:seed
```

### Step 3: Run Backend Development Server
```bash
npm run start:dev
```
- API Base: `http://localhost:3000/api/v1`
- Swagger Docs: `http://localhost:3000/docs`

### Step 4: Run Frontend Development Server
In a separate terminal:
```bash
cd frontend
npm install
npm run dev
```
- App UI: `http://localhost:5173`
- Admin UI: `http://localhost:5173/admin/login`

---

## 2. Docker Compose Deployment

The provided [docker-compose.yml](file:///d:/gym/docker-compose.yml) orchestrates 5 containers:
1. `mysql`: MySQL 8.0 database with persistent storage (`mysql_data`) and native health checks.
2. `redis`: Redis 7-alpine cache and rate limiter (`redis_data`) with health checks.
3. `backend`: NestJS application running in production mode.
4. `frontend`: React SPA built with Vite and served via Nginx.
5. `nginx`: Reverse proxy routing `/api/` to backend and `/` to frontend.

### Important: DB Host Inside Docker
- When running locally outside containers: `DB_HOST=localhost`
- When running inside Docker containers: `DB_HOST=mysql` (Docker network bridge DNS)

### Launching Docker Environment
```bash
# 1. Build and launch all services in detached mode
docker-compose up -d --build

# 2. Verify all service health checks
docker-compose ps

# 3. View live logs
docker-compose logs -f backend
```

### Running Migrations & Seed Inside Docker
```bash
# Run Prisma push inside the running backend container
docker-compose exec backend npx prisma db push

# Seed initial admin, food master, and activity catalog
docker-compose exec backend npm run prisma:seed
```

---

## 3. Environment Variables Reference

| Variable | Description | Default |
| :--- | :--- | :--- |
| `NODE_ENV` | Runtime environment (`development`, `production`, `test`) | `production` |
| `BACKEND_PORT` | Port exposed by backend service | `3000` |
| `FRONTEND_PORT` | Port exposed by frontend service | `5173` |
| `MYSQL_PORT` | External port mapped to MySQL | `3306` |
| `REDIS_PORT` | External port mapped to Redis | `6379` |
| `NGINX_HTTP_PORT` | Public HTTP gateway port | `80` |
| `NGINX_HTTPS_PORT` | Public HTTPS gateway port | `443` |
| `DB_HOST` | Database host (`localhost` locally, `mysql` in Docker) | `mysql` |
| `DATABASE_URL` | Prisma MySQL connection string | `mysql://root:123456@mysql:3306/google-Fitness-ai-chatbot` |
| `REDIS_HOST` | Redis host (`localhost` locally, `redis` in Docker) | `redis` |
| `JWT_SECRET` | Secret key for signing Access Tokens | Required |
| `JWT_REFRESH_SECRET` | Secret key for signing Refresh Tokens | Required |
| `AI_PROVIDER` | Selected AI engine (`cloudflare`, `openai`, `mistral`, `gemini`) | `cloudflare` |
| `AI_MODEL` | Provider model name | `@cf/zai-org/glm-4.7-flash` |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare account identifier | Optional |
| `CLOUDFLARE_API_TOKEN` | Cloudflare API Bearer token | Optional |
| `VITE_API_BASE_URL` | Base API URL baked into frontend build | `/api/v1` |

---

## 4. Health Verification & Monitoring

The backend exposes 4 dedicated health probes for orchestrators (Kubernetes / Docker Swarm):

1. **Overall Health Check:**
   ```http
   GET /api/v1/health
   ```
   Returns 200 OK with status `ok` or `degraded`.

2. **Database Connectivity:**
   ```http
   GET /api/v1/health/database
   ```
   Executes `SELECT 1` against MySQL and reports roundtrip latency.

3. **Cache / Redis Status:**
   ```http
   GET /api/v1/health/redis
   ```
   Reports `connected` with latency or `standby` (in-memory fallback mode).

4. **AI Engine Readiness:**
   ```http
   GET /api/v1/health/ai
   ```
   Reports configured provider, model, and timeout thresholds.

---

## 5. Troubleshooting & FAQ

### Database Connection Refused
- Check that the MySQL container is healthy: `docker-compose ps mysql`.
- Verify `DATABASE_URL` uses `@mysql:3306` (inside Docker) or `@localhost:3306` (native).
- Ensure port `3306` is not occupied by an existing local MySQL service.

### Redis Unavailable / Standby
- Redis is designed to be **optional**. If Redis is stopped or fails to connect, the backend automatically transitions to the in-memory cache without crashing or interrupting customer sessions.

### Multilingual AI Processing Issues
- Verify `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` if using Cloudflare Workers AI.
- Check backend logs: `docker-compose logs backend | grep AIProvider`.
- Check Admin AI telemetry dashboard at `/admin/ai-usage` for error messages and failure counts.
