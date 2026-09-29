import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from .config import settings

logger = logging.getLogger("database")

class Database:
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None

db_instance = Database()

async def connect_to_mongo():
    logger.info("Connecting to MongoDB Atlas...")
    db_instance.client = AsyncIOMotorClient(
        settings.MONGODB_URL,
        serverSelectionTimeoutMS=10000,
        connectTimeoutMS=10000,
    )
    db_instance.db = db_instance.client[settings.MONGODB_DB_NAME]
    logger.info(f"Connected to MongoDB database: {settings.MONGODB_DB_NAME}")
    
    # Ensure indexes for performance and query uniqueness
    try:
        await db_instance.db.users.create_index("email", unique=True, sparse=True)
        await db_instance.db.users.create_index("username", sparse=True)
        await db_instance.db.daily_food_logs.create_index([("user_id", 1), ("log_date", 1)])
        await db_instance.db.daily_food_logs.create_index([("user_id", 1), ("created_at", -1)])
        await db_instance.db.daily_exercise_logs.create_index([("user_id", 1), ("log_date", 1)])
        await db_instance.db.conversation_messages.create_index([("session_id", 1), ("created_at", 1)])
        await db_instance.db.chat_sessions.create_index([("user_id", 1), ("created_at", -1)])
        logger.info("Database indexes verified.")
    except Exception as e:
        logger.warning(f"Index creation note: {e}")

async def close_mongo_connection():
    if db_instance.client:
        logger.info("Closing MongoDB connection...")
        db_instance.client.close()
        logger.info("MongoDB connection closed.")

def get_db() -> AsyncIOMotorDatabase:
    return db_instance.db
