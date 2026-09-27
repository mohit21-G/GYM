export default () => ({
  nodeEnv: process.env.NODE_ENV || 'development',
  port: parseInt(process.env.BACKEND_PORT, 10) || 3000,
  apiPrefix: process.env.API_PREFIX || 'api/v1',
  corsOrigin: process.env.CORS_ORIGIN || 'http://localhost:5173',

  database: {
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT, 10) || 3306,
    username: process.env.DB_USERNAME || 'root',
    password: process.env.DB_PASSWORD || '123456',
    database: process.env.DB_DATABASE || 'google-fitbit-ai-chatbot',
    url: process.env.DATABASE_URL || 'mysql://root:123456@localhost:3306/google-fitbit-ai-chatbot',
  },

  redis: {
    host: process.env.REDIS_HOST || 'localhost',
    port: parseInt(process.env.REDIS_PORT, 10) || 6379,
    password: process.env.REDIS_PASSWORD || undefined,
  },

  jwt: {
    secret: process.env.JWT_SECRET || 'supersecretjwtkey_fitbit_ai_production_change_me_123456',
    expiresIn: process.env.JWT_EXPIRES_IN || '7d',
  },

  ai: {
    provider: process.env.AI_PROVIDER || 'cloudflare',
    model: process.env.AI_MODEL || '@cf/zai-org/glm-4.7-flash',
    timeoutMs: parseInt(process.env.AI_TIMEOUT_MS, 10) || 15000,
    maxRetries: parseInt(process.env.AI_MAX_RETRIES, 10) || 2,
    cloudflare: {
      accountId: process.env.CLOUDFLARE_ACCOUNT_ID || '',
      apiToken: process.env.CLOUDFLARE_API_TOKEN || '',
    },
    openai: {
      apiKey: process.env.OPENAI_API_KEY || '',
    },
    mistral: {
      apiKey: process.env.MISTRAL_API_KEY || '',
    },
    gemini: {
      apiKey: process.env.GEMINI_API_KEY || '',
    },
  },
});
