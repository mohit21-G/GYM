import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from .config import settings

logger = logging.getLogger("database")

class MockCursor:
    def __init__(self, data=None):
        self._data = list(data or [])
    def sort(self, *args, **kwargs):
        return self
    def limit(self, *args, **kwargs):
        return self
    async def to_list(self, length=100):
        return list(self._data[:length])

class MockCollection:
    def __init__(self, name="col"):
        self.name = name
        self.docs = []
    async def find_one(self, query=None, sort=None):
        for d in self.docs:
            match = True
            for k, v in (query or {}).items():
                if d.get(k) != v:
                    match = False
                    break
            if match:
                return dict(d)
        return None
    def find(self, query=None):
        filtered = []
        for d in self.docs:
            match = True
            for k, v in (query or {}).items():
                if k.startswith("$"):
                    continue
                if d.get(k) != v:
                    match = False
                    break
            if match:
                filtered.append(dict(d))
        return MockCursor(filtered)
    async def insert_one(self, doc):
        self.docs.append(dict(doc))
        return type("InsertResult", (), {"inserted_id": doc.get("id") or doc.get("_id")})
    async def update_one(self, query, update, upsert=False):
        doc = await self.find_one(query)
        if doc and "$set" in update:
            doc.update(update["$set"])
        return type("UpdateResult", (), {"modified_count": 1 if doc else 0})
    async def create_index(self, *args, **kwargs):
        pass

class MockDatabase:
    def __init__(self):
        self._collections = {}
    def __getattr__(self, name):
        if name not in self._collections:
            self._collections[name] = MockCollection(name)
        return self._collections[name]
    def __getitem__(self, name):
        return getattr(self, name)

class Database:
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None
    fallback_db: MockDatabase = MockDatabase()

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
    if db_instance.db is None:
        return db_instance.fallback_db
    return db_instance.db
