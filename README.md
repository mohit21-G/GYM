# Google Fitness AI Chatbot

A production-grade, enterprise health and fitness conversational platform built with NestJS, React, Prisma, MySQL, Redis, and a multi-provider AI abstraction layer natively supporting **Cloudflare Workers AI (GLM-4.7-Flash)**, **OpenAI (GPT-4o)**, **Mistral**, and **Google Gemini**.

---

## 🌟 Key Features

### 1. Multilingual Conversational Health Logging
- Log health activities naturally using **English, Hindi, Gujarati, Hinglish, Gujlish, and Romanized Hindi/Gujarati**.
- **17 Canonical Intents**: Automatic extraction of meals, workouts, water, weight, sleep, summaries, updates, and cancellations.
- **Strict Separation of Concerns**:
  - The AI engine never accesses MySQL/Prisma directly or calculates authoritative numbers.
  - The backend owns all nutrition lookups, portion scaling, MET calculations, date/time normalization (IST timezone), and customer data isolation.
  - The frontend never performs business logic or calculates calories.

### 2. Conversational UI & Rich Health Cards
- Interactive chat interface with real-time typing indicators and clickable clarification pills.
- Structured response cards for:
  - **Meals**: Portions, calories, and detailed macronutrient pills (Protein, Carbs, Fat, Fiber).
  - **Workouts**: Exercise duration, MET intensity, and authoritative calories burned.
  - **Hydration**: Volume in ml and visual progress toward the daily goal.
  - **Sleep**: Duration in hours/minutes and sleep quality badge.
  - **Weight**: Recorded weight, delta, and trend detection (UP, DOWN, STABLE).
  - **Summaries**: Total calories in vs out, net deficit/surplus, and macro distribution.

### 3. Customer Health Dashboard
- Daily health summary with circular/bar target progress rings.
- 7-day and 30-day chart-ready history with daily points and weekly averages.
- Recent activity timeline and log history browser with filters and deletion.
- Profile management for personal biometrics (height, current weight, target weight) and daily goals (calories, water, sleep).

### 4. Comprehensive Admin Portal (`/admin/*`)
- **Customer Management**: Paginated directory with search, status filters (`ACTIVE`, `INACTIVE`, `SUSPENDED`), customer profile inspector, and read-only chatbot history auditor.
- **Master Data Management**: Full CRUD for Indian Food items and Food Categories; Workout activities with MET values and Activity Categories.
- **AI & Token Telemetry**: Request volume, input/output/total token tracking, latency, failure rates, and estimated USD costs.
- **Administrative Audit Trail**: Immutable logging of all administrative actions with client IP, user agent, and before/after payloads.

### 5. Multi-Provider AI Abstraction
- Seamlessly switch between AI engines by changing `AI_PROVIDER` and `AI_MODEL` in `.env`:
  - `cloudflare`: `@cf/zai-org/glm-4.7-flash` (with automatic `<think>...</think>` chain-of-thought stripping)
  - `openai`: `gpt-4o` or `gpt-4o-mini`
  - `mistral`: `mistral-small-latest`
  - `gemini`: `gemini-1.5-flash`
- Exponential backoff retry handling, graceful fallbacks, and telemetry logging to `ai_usage_logs`.

### 6. Production Security & Reliability
- **Helmet** & secure HTTP headers
- **CORS** with configurable origins
- **Sliding-Window Rate Limiting** with Redis or in-memory fallback
- **JWT Authentication** with Access/Refresh token rotation and revocation
- **Prisma Parameterized Queries** (SQL injection immune)
- **Role-Based Access Control (RBAC)** (`CUSTOMER` vs `ADMIN`)
- **Safe Error Responses**: `AllExceptionsFilter` strips internal database details and stack traces in production.
- **4 Dedicated Health Probes**: `/api/v1/health`, `/health/database`, `/health/redis`, `/health/ai`.

---

## 🚀 Tech Stack

- **Backend**: NestJS, TypeScript, Prisma ORM, MySQL 8.0, Redis 7.0, ioredis, bcrypt, Passport JWT, Swagger/OpenAPI.
- **Frontend**: React 18, TypeScript, Vite, React Router v6, Tailwind CSS, Zustand, Axios, Lucide Icons, date-fns.
- **Containerization**: Docker, Docker Compose, Nginx reverse proxy.

---

## 💻 Quick Start

### Prerequisites
- Node.js 20+
- MySQL 8.0
- (Optional) Redis 7.0 (In-memory fallback activates automatically if Redis is offline)

### 1. Environment Setup
```bash
cp .env.example .env
```

### 2. Backend Setup & Seeding
```bash
cd backend
npm install
npx prisma generate
npx prisma db push
npm run prisma:seed
npm run start:dev
```
- API Base: `http://localhost:3000/api/v1`
- Swagger Documentation: `http://localhost:3000/docs`

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
- Web App: `http://localhost:5173`
- Admin Portal: `http://localhost:5173/admin/login`

---

## 🐳 Docker Deployment

To launch all 5 containers (MySQL, Redis, Backend, Frontend, Nginx gateway):
```bash
docker-compose up -d --build
```
- Web Application: `http://localhost`
- API Backend: `http://localhost/api/v1`
- Swagger Docs: `http://localhost/docs`

---

## 📚 Documentation Index

- [Architecture & Design Principles](docs/architecture.md)
- [REST API Specifications](docs/api.md)
- [Database Schema & Prisma Models](docs/database.md)
- [Multi-Provider AI Abstraction](docs/ai-providers.md)
- [Production Deployment & Container Orchestration](docs/deployment.md)
- [Testing Strategy & QA Checklist](docs/testing.md)
