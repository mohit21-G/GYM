# Google Fitness AI Chatbot - API Documentation

## Base URL
- Local Development: `http://localhost:3000/api/v1`
- Production / Docker: `http://localhost/api/v1`
- Interactive Swagger UI: `http://localhost:3000/docs`

---

## 1. Authentication & RBAC

### Security Standards
- **Token Delivery**: Bearer token in HTTP Header `Authorization: Bearer <accessToken>`.
- **Identity Enforcement**: Customer ID is ALWAYS extracted from the verified JWT payload (`req.user.id`). Frontends NEVER provide `user_id` in request bodies.
- **Roles**:
  - `CUSTOMER`: Access strictly limited to own data and conversation sessions.
  - `ADMIN`: Global administration, system telemetry, master catalogs, user status controls, and audit trails.
- **Status Checks**: Every request verifies status. `SUSPENDED` or `INACTIVE` accounts receive `403 Forbidden`.

---

### Customer Authentication Endpoints

#### 1. Register Customer
- **Endpoint**: `POST /auth/register`
- **Access**: Public
- **Request Body**:
  ```json
  {
    "name": "Mohit Gangani",
    "email": "mohit@example.com",
    "password": "StrongPassword123",
    "timezone": "Asia/Kolkata",
    "preferredLanguage": "en",
    "age": 28,
    "gender": "MALE",
    "heightCm": 175,
    "currentWeightKg": 75.5,
    "targetWeightKg": 70.0,
    "activityLevel": "MODERATE"
  }
  ```
- **Response** (`201 Created`):
  ```json
  {
    "success": true,
    "statusCode": 201,
    "data": {
      "user": {
        "id": "c1f7a8b2-...",
        "name": "Mohit Gangani",
        "email": "mohit@example.com",
        "role": "CUSTOMER",
        "status": "ACTIVE",
        "timezone": "Asia/Kolkata",
        "preferredLanguage": "en"
      },
      "accessToken": "eyJhbGciOi...",
      "refreshToken": "eyJhbGciOi..."
    },
    "timestamp": "2026-09-27T13:08:00.000Z"
  }
  ```

#### 2. Customer Login
- **Endpoint**: `POST /auth/login`
- **Access**: Public
- **Request Body**:
  ```json
  {
    "email": "mohit@example.com",
    "password": "StrongPassword123"
  }
  ```
- **Response** (`200 OK`):
  ```json
  {
    "success": true,
    "statusCode": 200,
    "data": {
      "user": { ... },
      "accessToken": "eyJhbGciOi...",
      "refreshToken": "eyJhbGciOi..."
    },
    "timestamp": "2026-09-27T13:08:00.000Z"
  }
  ```

#### 3. Refresh Access Token (Token Rotation)
- **Endpoint**: `POST /auth/refresh`
- **Access**: Public
- **Request Body**:
  ```json
  {
    "refreshToken": "eyJhbGciOi..."
  }
  ```
- **Response** (`200 OK`):
  ```json
  {
    "success": true,
    "statusCode": 200,
    "data": {
      "accessToken": "eyJhbGciOi...",
      "refreshToken": "eyJhbGciOi..."
    },
    "timestamp": "2026-09-27T13:08:00.000Z"
  }
  ```

#### 4. Customer Logout
- **Endpoint**: `POST /auth/logout`
- **Access**: Authenticated (`CUSTOMER` or `ADMIN`)
- **Headers**: `Authorization: Bearer <accessToken>`
- **Request Body** (Optional):
  ```json
  {
    "refreshToken": "eyJhbGciOi..."
  }
  ```
- **Response** (`200 OK`):
  ```json
  {
    "success": true,
    "statusCode": 200,
    "data": {
      "message": "Logged out successfully"
    },
    "timestamp": "2026-09-27T13:08:00.000Z"
  }
  ```

#### 5. Get Current Profile
- **Endpoint**: `GET /auth/me`
- **Access**: Authenticated (`CUSTOMER` or `ADMIN`)
- **Headers**: `Authorization: Bearer <accessToken>`
- **Response** (`200 OK`):
  ```json
  {
    "success": true,
    "statusCode": 200,
    "data": {
      "id": "c1f7a8b2-...",
      "name": "Mohit Gangani",
      "email": "mohit@example.com",
      "role": "CUSTOMER",
      "status": "ACTIVE",
      "profile": {
        "age": 28,
        "gender": "MALE",
        "heightCm": 175,
        "currentWeightKg": 75.5,
        "targetWeightKg": 70.0
      }
    },
    "timestamp": "2026-09-27T13:08:00.000Z"
  }
  ```

---

### Admin Authentication Endpoints

#### 1. Admin Login
- **Endpoint**: `POST /admin/auth/login`
- **Access**: Public (requires account with `ADMIN` role)
- **Response** (`200 OK`):
  ```json
  {
    "success": true,
    "statusCode": 200,
    "data": {
      "user": {
        "id": "a9e8d7c6-...",
        "name": "System Administrator",
        "email": "admin@Fitness-ai.com",
        "role": "ADMIN",
        "status": "ACTIVE"
      },
      "accessToken": "eyJhbGciOi...",
      "refreshToken": "eyJhbGciOi..."
    }
  }
  ```

#### 2. Admin Refresh
- **Endpoint**: `POST /admin/auth/refresh`
- **Access**: Public

#### 3. Admin Logout
- **Endpoint**: `POST /admin/auth/logout`
- **Access**: Authenticated (`ADMIN` only)

#### 4. Admin Profile
- **Endpoint**: `GET /admin/auth/me`
- **Access**: Authenticated (`ADMIN` only)

---

## 2. Customer Health Logging APIs

All endpoints below require standard JWT authentication (`Authorization: Bearer <accessToken>`). User ownership is automatically enforced via token identity.

### Food Logs (`/api/v1/food-logs`)
- `POST /food-logs`: Create food entry with historical nutrition snapshot.
- `GET /food-logs?page=1&limit=10&mealType=LUNCH&startDate=2026-09-01&endDate=2026-09-30`: Paginated list.
- `GET /food-logs/:id`: Fetch specific log.
- `PATCH /food-logs/:id`: Update log.
- `DELETE /food-logs/:id`: Delete log.

### Activity Logs (`/api/v1/activity-logs`)
- `POST /activity-logs`: Create workout/exercise log (MET * Weight(kg) * Duration/60).
- `GET /activity-logs?page=1&limit=10`: Paginated activities.
- `GET /activity-logs/:id`: Fetch single activity.
- `PATCH /activity-logs/:id`: Update log.
- `DELETE /activity-logs/:id`: Delete log.

### Weight Logs (`/api/v1/weight-logs`)
- `POST /weight-logs`: Record weight; calculates BMI & updates user profile current weight.
- `GET /weight-logs?page=1&limit=10`: Paginated weight records.
- `GET /weight-logs/:id`: Single weight entry.
- `PATCH /weight-logs/:id`: Update weight.
- `DELETE /weight-logs/:id`: Delete weight entry.

### Sleep Logs (`/api/v1/sleep-logs`)
- `POST /sleep-logs`: Record sleep with start/end time, duration, quality, deep/REM breakdowns.
- `GET /sleep-logs?page=1&limit=10`: Paginated sleep logs.
- `GET /sleep-logs/:id`: Single sleep log.
- `PATCH /sleep-logs/:id`: Update sleep log.
- `DELETE /sleep-logs/:id`: Delete sleep log.

### Hydration Logs (`/api/v1/hydration-logs`)
- `POST /hydration-logs`: Record water intake in ml.
- `GET /hydration-logs?page=1&limit=10`: Paginated hydration records.
- `GET /hydration-logs/:id`: Single hydration log.
- `PATCH /hydration-logs/:id`: Update hydration log.
- `DELETE /hydration-logs/:id`: Delete hydration log.

### Customer Profile (`/api/v1/users/profile`)
- `GET /users/profile`: Fetch current profile and daily health targets (calories, water, sleep).
- `PATCH /users/profile`: Update profile fields and targets.

---

## 3. Conversational AI Chat Orchestration

All chat endpoints require `Authorization: Bearer <accessToken>`.

### 1. Send Message
- **Endpoint**: `POST /chat/message`
- **Request Body**:
  ```json
  {
    "sessionId": "optional-uuid",
    "message": "Savare 2 roti ane daal khadhi"
  }
  ```
- **Response** (`200 OK`):
  ```json
  {
    "sessionId": "a1b2c3d4-...",
    "replyMessage": "Logged 2 rotis and 1 bowl of daal for breakfast.",
    "detectedIntent": "CREATE_FOOD_LOG",
    "cardType": "LOG_RESULT",
    "cardData": {
      "type": "FOOD",
      "food": { "name": "Roti", "quantity": 2, "mealType": "BREAKFAST" },
      "calculatedNutrition": { "calories": 208, "proteinG": 6.2, "carbsG": 38.0, "fatG": 1.2 }
    }
  }
  ```

### 2. List Chat Sessions
- **Endpoint**: `GET /chat/sessions`
- **Access**: Customer only

### 3. Get Session Message History
- **Endpoint**: `GET /chat/sessions/:id/messages`
- **Access**: Customer only

---

## 4. Food Logs & Fitbit-Style Food Cards

### 1. Daily Grouped Food Summary
- **Endpoint**: `GET /food-logs/daily-summary?date=YYYY-MM-DD`
- **Access**: Customer only
- **Response** (`200 OK`):
  ```json
  {
    "success": true,
    "statusCode": 200,
    "data": {
      "date": "2026-09-28",
      "groupedFoodCards": [
        {
          "foodKey": "food_seed-food-khapli-wheat-rotli",
          "foodMasterId": "seed-food-khapli-wheat-rotli",
          "foodName": "Khapli Wheat Rotli",
          "categoryName": "Breads & Grains",
          "icon": "wheat",
          "totalQuantity": 5,
          "unit": "pieces",
          "totalCalories": 425,
          "entryCount": 2,
          "macros": {
            "proteinG": 17.5,
            "carbsG": 82.5,
            "fatG": 4.0,
            "fiberG": 16.0
          },
          "entries": [
            {
              "id": "uuid-1",
              "foodMasterId": "seed-food-khapli-wheat-rotli",
              "foodName": "Khapli Wheat Rotli",
              "quantity": 2,
              "unit": "piece",
              "calories": 170,
              "mealType": "LUNCH",
              "loggedAt": "2026-09-28T14:26:00.000Z",
              "timeFormatted": "2:26 PM",
              "macros": {
                "proteinG": 7.0,
                "carbsG": 33.0,
                "fatG": 1.6,
                "fiberG": 6.4
              }
            },
            {
              "id": "uuid-2",
              "foodMasterId": "seed-food-khapli-wheat-rotli",
              "foodName": "Khapli Wheat Rotli",
              "quantity": 3,
              "unit": "piece",
              "calories": 255,
              "mealType": "LUNCH",
              "loggedAt": "2026-09-28T14:27:00.000Z",
              "timeFormatted": "2:27 PM",
              "macros": {
                "proteinG": 10.5,
                "carbsG": 49.5,
                "fatG": 2.4,
                "fiberG": 9.6
              }
            }
          ]
        }
      ],
      "dailyNutritionSummary": {
        "date": "2026-09-28",
        "totalCalories": 425,
        "targetCalories": 2000,
        "remainingCalories": 1575,
        "percentOfTarget": 21,
        "macros": {
          "proteinG": 17.5,
          "carbsG": 82.5,
          "fatG": 4.0,
          "fiberG": 16.0
        },
        "totalEntries": 2,
        "distinctFoodsCount": 1
      }
    }
  }
  ```

### 2. Standard Food Log CRUD
- `POST /food-logs`: Create individual food log.
- `GET /food-logs?page=1&limit=15&startDate=...&endDate=...`: Filter and list user's food logs.
- `GET /food-logs/:id`: Fetch single food log.
- `PATCH /food-logs/:id`: Update food log.
- `DELETE /food-logs/:id`: Delete food log.

---

## 5. Health Dashboard & Summaries

### 1. Daily Health Dashboard
- **Endpoint**: `GET /dashboard/today?date=YYYY-MM-DD`
- **Access**: Customer only
- **Response**: Authoritative calculation of calories consumed, burned, net, targets, macros breakdown, hydration, sleep quality, and current weight trend.

### 2. Weekly Health Trends
- **Endpoint**: `GET /dashboard/week`
- **Response**: 7-day chart-ready history with daily points and weekly averages.

### 3. Monthly Health Trends
- **Endpoint**: `GET /dashboard/month`
- **Response**: 30-day chart-ready history with daily points and monthly trends.

---

## 5. Administrative Management & Audit APIs

All administrative endpoints require `Authorization: Bearer <accessToken>` and `Role.ADMIN`. Non-admin accounts receive `403 Forbidden`.

### Customer Management
- `GET /admin/customers?page=1&limit=20&name=...&status=ACTIVE&sort=newest`: Paginated customer directory with log counts.
- `GET /admin/customers/:id`: Full customer inspection (profile, targets, log counts, recent health logs).
- `PATCH /admin/customers/:id/status`: Update account status (`ACTIVE`, `INACTIVE`, `SUSPENDED`). Inactivations revoke active refresh tokens and write immutable audit records.
- `GET /admin/customers/:id/chats`: Read-only customer chat session history inspection.

### Master Catalogs
- `GET /admin/foods`: List canonical food items with search and category filters.
- `POST /admin/foods`: Create new canonical food entry (calories, macros, serving unit, synonyms).
- `GET /admin/foods/:id`: Get food item by ID.
- `PATCH /admin/foods/:id`: Update canonical food item.
- `DELETE /admin/foods/:id`: Delete food item.
- `GET /admin/food-categories`: List food categories.
- `POST /admin/food-categories`: Create food category.
- `GET /admin/activities`: List canonical exercise activities with MET values.
- `POST /admin/activities`: Create activity with MET value.
- `PATCH /admin/activities/:id`: Update activity entry.
- `DELETE /admin/activities/:id`: Delete activity entry.
- `GET /admin/activity-categories`: List workout categories.
- `POST /admin/activity-categories`: Create workout category.

### Monitoring & Auditing
- `GET /admin/ai/usage?page=1&limit=20&provider=...&status=...`: AI telemetry metrics (prompt/completion tokens, latency, estimated USD cost, failure rates).
- `GET /admin/audit-logs?page=1&limit=20&action=...`: Immutable administrative activity audit log browser.
- `GET /admin/dashboard`: Global system statistics, health logs overview, and 7-day activity chart data.

---

## 6. System Health Probes

- `GET /health`: Overall system health and service dependencies.
- `GET /health/database`: Tests MySQL connectivity and query latency.
- `GET /health/redis`: Tests Redis connection or reports robust in-memory fallback.
- `GET /health/ai`: Reports active AI provider readiness and timeout settings.

