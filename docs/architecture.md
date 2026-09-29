# Google Fitness AI Chatbot - System Architecture

## 1. Overview
The **Google Fitness AI Chatbot** platform is an intelligent, multi-provider health and fitness assistant platform. It enables customers to log food, activity, hydration, sleep, and weight naturally using conversational language (including multilingual inputs like English, Hindi, Gujarati, Hinglish, and Gujlish), while providing administrators full oversight, audit logging, master catalog management, and AI usage metrics.

## 2. Core Architectural Principles
1. **Separation of Concerns**:
   - **Frontend**: Presentation, state management, rich responsive UX, and user interaction. NEVER calculates calories, interprets dates, directly accesses databases, or calls AI providers directly.
   - **Backend**: Strict authentication, authorization (RBAC), validation (DTOs & class-validator), business logic, master data resolution, nutrition calculations, AI orchestration, and audit logging.
   - **AI Providers**: Pure intent and entity extraction and conversational dialogue generation. The AI NEVER interacts directly with MySQL/Prisma, executes SQL, or decides nutritional ground truth.
2. **Provider Agnostic AI Layer**:
   - Standardized interface (`AIProvider`) supporting multiple interchangeable backends:
     - Cloudflare Workers AI (`@cf/zai-org/glm-4.7-flash`)
     - OpenAI (GPT-4o / GPT-4o-mini)
     - Mistral (Mistral Small / Large)
     - Google Gemini (Gemini 1.5 / 2.0 Flash)
   - Dynamic selection via environment variable `AI_PROVIDER`.
3. **Database & Data Layer**:
   - Relational MySQL storage mapped cleanly via **Prisma ORM**.
   - Redis-ready architecture for rate limiting, token revocation, provider health checks, and caching.

## 3. Request Flow Diagram
```
User Message (Text / Voice-to-Text)
       │
       ▼
React Customer Portal (Vite + Tailwind + Zustand)
       │ HTTP POST /api/v1/chat/message (Bearer JWT)
       ▼
NestJS Backend (Rate Limiting, Helmet, JWT Guard, Validation Pipe)
       │
       ▼
ChatService
       │
       ▼
AIService (Provider Factory)
       │
       ├─► Selected Provider (e.g. Cloudflare GLM-4.7-Flash / OpenAI / Gemini / Mistral)
       │
       ◄─ Normalized Intent & Entities (JSON)
       │
       ▼
Intent Router & Business Services:
   ├── FoodService (Nutrition DB Master Resolution, Portion Calc)
   ├── ActivityService (MET & Calorie Burn Calculation)
   ├── WaterService (Hydration Target & Logging)
   ├── SleepService (Duration & Sleep Quality)
   └── WeightService (BMI & Trend Tracking)
       │
       ▼
Prisma ORM (Transactions, Audit Logging)
       │
       ▼
MySQL Database (Users, Logs, Masters, ChatSessions, AuditLogs)
       │
       ▼
Structured Response (Formatted Message, Logged Entities, Updated Metrics)
       │
       ▼
React Customer UI (Chat Bubble + Live Dashboard Widgets Update)
```

## 4. Security & Isolation Architecture
- **Customer Isolation**: All log queries and mutations enforce `where: { userId: request.user.id }`.
- **Role-Based Access Control (RBAC)**:
  - `CUSTOMER`: Access strictly to own records and chat.
  - `ADMIN`: Full administrative overview, customer detail auditing (read-only health data by default), master catalog management, AI usage inspection, and system metrics.
- **Defensive API**: Helmet headers, strict CORS, rate-limiting guards, sanitized error outputs (no stack traces in production).
