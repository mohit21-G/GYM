# Google Fitness AI Chatbot - Database Architecture & Schema

## 1. Overview
The database layer is implemented using **MySQL 8.0** managed through **Prisma ORM**. All database credentials, ports, and connection strings are strictly environment-driven via `DATABASE_URL`.

## 2. Models & Entities

### Users & Authentication
- **`users`**:
  - `id`: UUID primary key
  - `name`: Full user name
  - `username`: Unique handle (optional)
  - `email`: Unique email address used for credentials
  - `password_hash`: Bcrypt hashed password
  - `role`: `CUSTOMER` | `ADMIN`
  - `status`: `ACTIVE` | `INACTIVE` | `SUSPENDED`
  - `timezone`: User's primary timezone (default: `Asia/Kolkata`)
  - `preferred_language`: e.g. `en`, `hi`, `gu`
  - `last_login_at`, `created_at`, `updated_at`
- **`user_profiles`**:
  - One-to-one relationship with `users` (cascading delete)
  - Stores physical metrics: `age`, `gender`, `height_cm`, `current_weight_kg`, `target_weight_kg`
  - Targets: `daily_calorie_target`, `daily_water_ml_target`, `daily_sleep_minutes_target`, `activity_level`

### Conversational Chat Logs
- **`chat_sessions`**: Groups related user messages into continuous threads.
- **`chat_messages`**:
  - `sender`: `USER` | `ASSISTANT` | `SYSTEM`
  - `message`: Text content
  - `raw_entities`: Captured JSON entity payload from AI
  - `detected_intent`: Extracted intent (e.g., `LOG_FOOD`, `LOG_ACTIVITY`)
  - `ai_provider` & `ai_model`: Model utilized (e.g. `@cf/zai-org/glm-4.7-flash`)
  - `prompt_tokens`, `completion_tokens`, `total_tokens`, `latency_ms`

### Food Master & Historical Logs
- **`food_categories`**:
  - High level grouping: *Breads & Grains, Pulses & Lentils, Dairy, Proteins, Fruits, Vegetables, Snacks, Beverages*.
- **`foods`**:
  - Authoritative nutritional master library.
  - Stores standard serving sizes, calories, protein, carbs, fat, fiber, sodium, and natural language synonyms (e.g. *khapli rotli, chapati, fulka*).
- **`food_logs`**:
  - Individual consumption event.
  - **Important Architectural Rule**: Food logs store **historical nutrition snapshots** (`calories`, `protein_g`, `carbs_g`, `fat_g`, `fiber_g`). Even if the master record changes later, logged history remains mathematically immutable.

### Activities Master & Activity Logs
- **`activity_categories`**:
  - Categories: *Cardio & Aerobics, Strength & Conditioning, Sports & Games, Flexibility, Daily Tasks*.
- **`activities`**:
  - Master catalog with **MET (Metabolic Equivalent of Task)** values and synonyms (e.g. *gym, weight lifting, kasrat*).
- **`activity_logs`**:
  - Records exercise duration and intensity.
  - Authoritative calorie burn formula:
    $$\text{Calories Burned} = \text{MET} \times \text{User Weight (kg)} \times \frac{\text{Duration (minutes)}}{60}$$
  - Captures `user_weight_kg_snapshot` at the time of exercise.

### Health Telemetry Logs
- **`weight_logs`**: Body weight tracking with calculated BMI snapshot.
- **`sleep_logs`**: Sleep tracking with start/end time, duration, deep/REM breakdowns, and sleep quality.
- **`hydration_logs`**: Water intake tracking (in milliliters).

### Operations & Auditing
- **`ai_usage_logs`**: Telemetry tracking latency, token usage, intent, status, and error messages across all AI providers.
- **`admin_audit_logs`**: Security audit trail capturing every administrative mutation with admin ID, action type, IP address, user agent, and timestamp.

## 3. Seeding
Initial database seeding is automated via `npm run prisma:seed`:
- 8 Food Categories & comprehensive Indian and International healthy foods
- 5 Activity Categories & standardized MET activities
- System Administrator user generated securely via `ADMIN_EMAIL` and `ADMIN_PASSWORD` environment variables
