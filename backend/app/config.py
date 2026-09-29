import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv(override=True)

class Settings(BaseSettings):
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "fitness_chatbot")
    
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "3000"))
    API_RELOAD: bool = os.getenv("API_RELOAD", "True").lower() == "true"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    CORS_ORIGINS: str = os.getenv(
        "CORS_ORIGINS",
        os.getenv(
            "CORS_ORIGIN",
            "https://gym-nine-xi-65.vercel.app,https://gym-zeta-five-47.vercel.app,http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000,http://localhost:4173,http://127.0.0.1:4173",
        ),
    )
    
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "default_secret_key_change_in_production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    CF_ACCOUNT_ID: str = os.getenv("CF_ACCOUNT_ID", "")
    CF_API_TOKEN: str = os.getenv("CF_API_TOKEN", "")
    CF_MODEL: str = os.getenv("CF_MODEL", "@cf/meta/llama-3.1-8b-instruct")
    SARVAM_API_KEY: str = os.getenv("SARVAM_API_KEY", "")
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "auto")  # options: auto, groq, cloudflare, rule_based
    
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@Fitness-ai.com")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "Admin@123456")
    ADMIN_NAME: str = os.getenv("ADMIN_NAME", "System Administrator")

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
