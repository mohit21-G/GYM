import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from .config import settings

logger = logging.getLogger("database")

class MockCursor:
    def __init__(self, data=None):
        self._data = list(data or [])
    def sort(self, key_or_list=None, direction=1):
        if not key_or_list:
            return self
        if isinstance(key_or_list, list) and key_or_list:
            key, direction = key_or_list[0]
        elif isinstance(key_or_list, str):
            key = key_or_list
        else:
            return self
        reverse = (direction == -1)
        try:
            self._data.sort(key=lambda d: (d.get(key) is None, d.get(key)), reverse=reverse)
        except Exception:
            pass
        return self
    def skip(self, n=0):
        self._data = self._data[n:]
        return self
    def limit(self, n=100):
        self._data = self._data[:n]
        return self 
    async def to_list(self, length=100):
        return list(self._data[:length])

class MockCollection:
    def __init__(self, name="col"):
        self.name = name
        self.docs = []
    def _matches(self, doc, query):
        if not query:
            return True
        for k, v in query.items():
            if k == "$or" and isinstance(v, list):
                if not any(self._matches(doc, cond) for cond in v):
                    return False
                continue
            if isinstance(v, dict):
                doc_val = doc.get(k)
                for op, op_val in v.items():
                    if op == "$gte":
                        if doc_val is None or doc_val < op_val:
                            return False
                    elif op == "$lte":
                        if doc_val is None or doc_val > op_val:
                            return False
                    elif op == "$gt":
                        if doc_val is None or doc_val <= op_val:
                            return False
                    elif op == "$lt":
                        if doc_val is None or doc_val >= op_val:
                            return False
                    elif op == "$ne":
                        if doc_val == op_val:
                            return False
                    elif op == "$in":
                        if doc_val not in op_val:
                            return False
                continue
            if doc.get(k) != v:
                return False
        return True
    async def find_one(self, query=None, sort=None):
        filtered = [d for d in self.docs if self._matches(d, query)]
        if sort:
            c = MockCursor(filtered)
            c.sort(sort)
            filtered = c._data
        if filtered:
            return dict(filtered[0])
        return None
    def find(self, query=None):
        filtered = [dict(d) for d in self.docs if self._matches(d, query)]
        return MockCursor(filtered)
    async def count_documents(self, query=None):
        return len([d for d in self.docs if self._matches(d, query)])
    async def insert_one(self, doc):
        self.docs.append(dict(doc))
        return type("InsertResult", (), {"inserted_id": doc.get("id") or doc.get("_id")})
    async def update_one(self, query, update, upsert=False):
        for i, d in enumerate(self.docs):
            if self._matches(d, query):
                if "$set" in update:
                    self.docs[i].update(update["$set"])
                return type("UpdateResult", (), {"matched_count": 1, "modified_count": 1})
        if upsert and "$set" in update:
            new_doc = {**query, **update["$set"]}
            self.docs.append(new_doc)
            return type("UpdateResult", (), {"matched_count": 0, "modified_count": 1, "upserted_id": new_doc.get("id")})
        return type("UpdateResult", (), {"matched_count": 0, "modified_count": 0})

    async def delete_one(self, query):
        for i, d in enumerate(self.docs):
            if self._matches(d, query):
                del self.docs[i]
                return type("DeleteResult", (), {"deleted_count": 1})
        return type("DeleteResult", (), {"deleted_count": 0})

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
