# Google Fitbit AI Chatbot

A production-ready conversational AI health and fitness logging platform built with NestJS, React, Prisma, MySQL, and multi-provider AI abstraction featuring Cloudflare Workers AI GLM-4.7-Flash, OpenAI, Gemini, and Mistral.

## Features
- **Intelligent Chatbot**: Log food, exercises, water intake, sleep, and weight naturally in English, Hindi, Gujarati, Hinglish, or Gujlish.
- **Customer Portal**: Modern, responsive dashboard with real-time health metrics, calorie tracking, interactive charts, and rich conversational UI.
- **Admin Portal**: User management, AI usage telemetry, master catalog management (food items and activities), and audit logs.
- **Pluggable AI Engine**: Switch seamlessly between Cloudflare Workers AI (`@cf/zai-org/glm-4.7-flash`), OpenAI, Gemini, and Mistral via simple environment variables.
- **Enterprise Architecture**: NestJS backend, Prisma ORM, MySQL database, Redis-ready caching/rate-limiting, strict RBAC, and Docker Compose orchestration.

## Tech Stack
- **Backend**: Node.js, NestJS, TypeScript, Prisma, MySQL, Redis, JWT, Helmet, Swagger/OpenAPI.
- **Frontend**: React 18, TypeScript, Vite, React Router v6, Tailwind CSS, Lucide Icons, Zustand, Axios.
- **AI Models**: Cloudflare GLM-4.7-Flash, OpenAI GPT-4o-mini, Google Gemini, Mistral.
- **Infrastructure**: Docker, Docker Compose, Nginx.

## Getting Started

### Prerequisites
- Node.js (v18+ or v20+)
- npm or yarn
- MySQL (v8.0) or Docker
- Redis (optional for development, required for production)

### Local Development Setup

1. **Clone the repository and copy environment configuration:**
   ```bash
   cp .env.example .env
   ```

2. **Backend Setup:**
   ```bash
   cd backend
   npm install
   npx prisma generate
   npm run start:dev
   ```
   Backend will be running on `http://localhost:3000`. Swagger API documentation is available at `http://localhost:3000/docs`.

3. **Frontend Setup:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   Frontend will be running on `http://localhost:5173`.

### Docker Deployment
To run the full stack with Docker Compose:
```bash
docker-compose up --build -d
```
The application will be accessible at:
- Web Application: `http://localhost:80`
- API Backend: `http://localhost:3000` or `http://localhost:80/api/v1`
- Swagger Docs: `http://localhost:80/docs`
