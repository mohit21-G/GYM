# Google Fitness AI Chatbot - AI Provider Abstraction Architecture

## 1. Overview
The **AI Abstraction Layer** enables complete decoupling between core business logic and large language model providers. The system can dynamically switch between AI backends using environment variables without code modification.

## 2. Supported AI Providers

| Provider | Default Model | Configuration Variables |
| :--- | :--- | :--- |
| **Cloudflare Workers AI** | `@cf/zai-org/glm-4.7-flash` | `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN` |
| **OpenAI** | `gpt-4o-mini` | `OPENAI_API_KEY` |
| **Mistral AI** | `mistral-small-latest` | `MISTRAL_API_KEY` |
| **Google Gemini** | `gemini-1.5-flash` | `GEMINI_API_KEY` |

## 3. Switching Providers
To change the active AI provider, update your `.env`:

```env
# Switch to Cloudflare Workers AI GLM-4.7-Flash
AI_PROVIDER=cloudflare
AI_MODEL=@cf/zai-org/glm-4.7-flash

# Or switch to OpenAI
AI_PROVIDER=openai
AI_MODEL=gpt-4o-mini

# Or switch to Google Gemini
AI_PROVIDER=gemini
AI_MODEL=gemini-1.5-flash

# Or switch to Mistral AI
AI_PROVIDER=mistral
AI_MODEL=mistral-small-latest
```

## 4. Architectural Rules
1. **Isolated SDK/REST Calls**:
   - Provider implementation files reside exclusively in `backend/src/ai/providers/`.
   - Business services (`FoodService`, `ActivityService`, `ChatService`) never import provider SDKs or make external AI calls directly.
2. **Normalized Response Contract**:
   Every provider returns a standardized `AIResponse`:
   - `intent`: `LOG_FOOD` | `LOG_ACTIVITY` | `LOG_WEIGHT` | `LOG_SLEEP` | `LOG_HYDRATION` | `QUERY_STATS` | `GENERAL_CHAT` | `UNKNOWN`
   - `language`: e.g. `en`, `hi`, `gu`, `hinglish`, `gujlish`
   - `entities`: JSON object containing structured entities (e.g., `foodItems`, `activity`, `weight`, `sleep`, `hydration`, `dateReference`, `targetDate`)
   - `requiresClarification`: boolean flag indicating if required parameters are missing
   - `clarificationQuestion`: polite prompt asking for missing parameters
   - `replyText`: warm conversational feedback in the user's dialect
   - `tokens`: prompt, completion, and total token usage
   - `latencyMs`: execution time in milliseconds
3. **Telemetry & Audit Logging**:
   - All AI calls are automatically logged to the `ai_usage_logs` table with provider, model, latency, token consumption, and status (`SUCCESS` or `FAILED`).
4. **Resilience & Fallback**:
   - Configurable timeout (`AI_TIMEOUT_MS`, default 15s) and retries (`AI_MAX_RETRIES`, default 2) with exponential backoff.
   - Graceful fallback messaging to prevent user disruption in case of external provider downtime.
