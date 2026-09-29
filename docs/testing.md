# Testing Strategy & QA Verification Suite

This document outlines the testing architecture, test matrices, and verification procedures for the **Google Fitness AI Chatbot** platform.

---

## 1. Testing Architecture & Structure

The codebase employs automated test suites covering:
- **Unit Tests**: Business logic, nutrition calculation, MET formulas, date/time parsing, AI providers, and auth guards.
- **Service Integration Tests**: Multi-provider fallback, sliding window rate limiting, and chat orchestration.
- **Security & Authorization Tests**: RBAC verification, Customer isolation (IDOR protection), and audit logging.

```
backend/src/
├── ai/
│   ├── ai.service.spec.ts                     # AI provider fallback, telemetry, retry
│   ├── date-time.normalizer.spec.ts           # IST timezone, Gujarati/Hindi date keywords
│   ├── intent-extraction.service.spec.ts      # 17 canonical intents, multilingual extraction
│   └── providers/
│       └── cloudflare.provider.spec.ts        # GLM-4.7-Flash, <think> tag sanitization
├── modules/
│   ├── activity-logs/
│   │   └── activity-business.service.spec.ts  # MET calorie formulas, intensity scaling
│   ├── admin/
│   │   ├── services/admin-analytics.service.spec.ts # AI token telemetry, audit logs, KPIs
│   │   ├── services/admin-customers.service.spec.ts # Customer CRUD, status, chat review
│   │   └── services/admin-masters.service.spec.ts   # Food & Activity master catalog CRUD
│   ├── auth/
│   │   └── auth.service.spec.ts               # bcrypt, JWT rotation, token revocation
│   ├── dashboard/
│   │   └── dashboard.service.spec.ts          # Today, 7-day, 30-day aggregates & trends
│   ├── food-logs/
│   │   └── food-business.service.spec.ts      # Indian food nutrition, portion scaling
│   ├── health/
│   │   └── health.service.spec.ts             # Overall, DB, Redis, and AI health probes
│   ├── redis/
│   │   └── redis.service.spec.ts              # In-memory fallback, rate limiting, TTL
│   └── weight-logs/
│       └── weight-business.service.spec.ts    # lbs-to-kg, BMI, trend analysis
```

---

## 2. 33-Point Production QA Checklist

| # | Check Item | Verification Status | Implementation |
| :--- | :--- | :--- | :--- |
| 1 | Customer Registration | ✅ PASSED | `POST /api/v1/auth/register` with validation |
| 2 | Customer Login/Logout/Refresh | ✅ PASSED | `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout` |
| 3 | Protected Chatbot Access | ✅ PASSED | `JwtAuthGuard` enforced on `/api/v1/chat/*` |
| 4 | Admin Login/Logout/Refresh | ✅ PASSED | Verified with `Role.ADMIN` check |
| 5 | Role Authorization | ✅ PASSED | `RolesGuard` rejects non-admin users with 403 Forbidden |
| 6 | Customer Data Isolation | ✅ PASSED | All customer queries scoped by `where: { userId: currentUser.id }` |
| 7 | Food Logging | ✅ PASSED | Authoritative lookup in `foods` master table; nutrition computed by backend |
| 8 | Activity Logging | ✅ PASSED | Authoritative MET formula: $\text{MET} \times \text{kg} \times \frac{\text{duration}}{60}$ |
| 9 | Weight Logging | ✅ PASSED | lbs-to-kg conversion, delta calculation, trend detection |
| 10 | Sleep Logging | ✅ PASSED | Cross-midnight duration calculation, quality evaluation |
| 11 | Hydration Logging | ✅ PASSED | ml/glass/liter normalization, target percentage progress |
| 12 | Follow-up Messages | ✅ PASSED | `ChatContextService` sliding-window context retains missing entity memory |
| 13 | Clarification Flow | ✅ PASSED | Backend yields `CLARIFICATION` card with clickable suggestion pills |
| 14 | English Input | ✅ PASSED | "Logged 2 rotis and 1 bowl dal" |
| 15 | Hindi Input | ✅ PASSED | "मैंने आज सुबह 30 मिनट दौड़ लगाई" |
| 16 | Gujarati Input | ✅ PASSED | "સવારે ૨ રોટલી અને ૧ વાટકી દાળ ખાધી" |
| 17 | Hinglish Input | ✅ PASSED | "Aaj maine 45 minute gym kiya aur 500ml pani piya" |
| 18 | Gujlish Input | ✅ PASSED | "Savare 2 katori khichdi ane chaas lidhi" |
| 19 | Roman Hindi | ✅ PASSED | "Raat ko 8 baje khana khaya" |
| 20 | Roman Gujarati | ✅ PASSED | "Kaale 5 km cycling kari" |
| 21 | Date/Time Normalization | ✅ PASSED | `DateTimeNormalizer` with `Asia/Kolkata` timezone context |
| 22 | Dashboard Calculations | ✅ PASSED | `GET /api/v1/dashboard/today` (calories, macros, water, sleep, weight) |
| 23 | Admin Customer Management | ✅ PASSED | Search, filter by status, sort, paginated listing |
| 24 | Customer Details Inspector | ✅ PASSED | Profile, log counts, recent health logs, chatbot conversations |
| 25 | Admin Master Data | ✅ PASSED | Full CRUD for foods, food categories, activities, activity categories |
| 26 | AI Usage Monitoring | ✅ PASSED | Token counters (prompt/completion/total), latency, cost estimation |
| 27 | Audit Trail Logs | ✅ PASSED | Immutable records created on every administrative mutation |
| 28 | Redis Health | ✅ PASSED | Connected check with graceful in-memory fallback |
| 29 | Database Health | ✅ PASSED | `GET /api/v1/health/database` executing `SELECT 1` |
| 30 | AI Provider Health | ✅ PASSED | `GET /api/v1/health/ai` verifying provider readiness and timeouts |
| 31 | Docker Multi-Stage Build | ✅ PASSED | Optimized multi-stage Dockerfiles for backend and frontend |
| 32 | Frontend Production Build | ✅ PASSED | `tsc && vite build` clean compilation |
| 33 | Backend Production Build | ✅ PASSED | `nest build` clean compilation |

---

## 3. Multilingual Test Matrix

The natural language engine parses health intents across scripts and transliterations:

| Input Phrase | Detected Intent | Normalized Entities |
| :--- | :--- | :--- |
| `"Ate 2 rotis and 1 bowl dal"` | `CREATE_FOOD_LOG` | `food: roti (2), dal (1 bowl)` |
| `"સવારે ૨ વાટકી ખીચડી ખાધી"` | `CREATE_FOOD_LOG` | `food: khichdi (2 vatki), time: morning` |
| `"Aaj sham ko 45 min running ki"` | `CREATE_ACTIVITY_LOG` | `activity: running, duration: 45 min` |
| `"7 thi 9 gym ma workout karyo"` | `CREATE_ACTIVITY_LOG` | `activity: workout, duration: 120 min` |
| `"Pani 750ml pidhu"` | `CREATE_HYDRATION_LOG` | `amountMl: 750` |
| `"Kal raat ko 7 ghante soya"` | `CREATE_SLEEP_LOG` | `durationMinutes: 420` |
| `"Vajan aaje 71.5 kg chhe"` | `CREATE_WEIGHT_LOG` | `weightKg: 71.5` |
| `"Show my calories today"` | `GET_TODAY_SUMMARY` | `date: today` |

---

## 4. Running Tests

### Backend Unit & Integration Tests
```bash
cd backend

# Run all test suites
npm test

# Run specific integration tests
npm test -- chat.service.spec.ts
```

### Fitbit-Style Food Cards Integration Suite
```bash
# Verify new food logging, repeated food logging, distinct cards, idempotency, data isolation
node scratch/test-fitbit-food-cards.js
```

| Check Item | Result | Expected Outcome |
| :--- | :--- | :--- |
| **New food logging** | ✅ PASSED | Single collapsed card, total quantity, total calories, `1 entry` |
| **Repeated food logging** | ✅ PASSED | Same card updated to `X entries`, totals summed, prior entries preserved |
| **Independent card expansion** | ✅ PASSED | Each card toggles independently; multiple cards can stay open |
| **Collapsed by default** | ✅ PASSED | Cards default to compact summary mode with chevron |
| **Expanded history accuracy** | ✅ PASSED | Individual entries display timestamp, meal badge, quantity, calories |
| **Different foods** | ✅ PASSED | Unrelated foods (e.g. Khapli Roti vs Banana) yield distinct cards |
| **Daily grouping** | ✅ PASSED | Grouped strictly by local calendar date (`YYYY-MM-DD`) |
| **Idempotency** | ✅ PASSED | Network retries within 5s deduplicated automatically |
| **Customer data isolation** | ✅ PASSED | Verified with multi-user registration and query isolation |

# Run tests with coverage reporting
npm run test:cov

# Run specific suite
npx jest src/ai/providers/cloudflare.provider.spec.ts
```

### Type Checking & Build Verification
```bash
# Backend
cd backend
npx tsc --noEmit
npm run build

# Frontend
cd frontend
npx tsc --noEmit
npm run build
```
