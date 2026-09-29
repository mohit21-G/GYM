"""
Safe Cleanup Script for 10,000-Case Benchmark Suite
Preserves all production accounts and permanently deletes ephemeral test artifacts.
"""

import asyncio
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from pymongo import MongoClient
from dotenv import load_dotenv

# Load backend environment variables
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
load_dotenv(os.path.join(BACKEND_DIR, ".env"))

MONGO_URI = os.getenv("MONGODB_URL") or os.getenv("MONGO_URI") or os.getenv("MONGODB_URI")
DB_NAME = os.getenv("MONGODB_DB_NAME", "fitness_chatbot")

PROTECTED_EMAILS = {
    "admin@fitness-ai.com",
    "admin@Fitness-ai.com",
    "dhoni@gmail.com",
    "fitbit_demo@example.com"
}

def cleanup():
    if not MONGO_URI:
        print("MONGO_URI not configured.")
        return

    print("Connecting to MongoDB Atlas for safe benchmark data cleanup...")
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]

    # Find test users
    all_users = list(db.users.find({}, {"email": 1, "id": 1, "_id": 1}))
    test_user_ids = []
    test_user_emails = []

    for u in all_users:
        email = u.get("email", "").lower()
        uid = str(u.get("id") or u.get("_id"))
        if email not in [pe.lower() for pe in PROTECTED_EMAILS]:
            if "bench" in email or "test" in email or "example.com" in email:
                test_user_ids.append(uid)
                test_user_emails.append(email)

    print(f"Preserving {len(PROTECTED_EMAILS)} production users.")
    print(f"Targeting {len(test_user_ids)} benchmark test users for cleanup: {test_user_emails}")

    if test_user_ids:
        # Delete related test logs
        fl_del = db.daily_food_logs.delete_many({"user_id": {"$in": test_user_ids}})
        ex_del = db.daily_exercise_logs.delete_many({"user_id": {"$in": test_user_ids}})
        hy_del = db.hydration_logs.delete_many({"user_id": {"$in": test_user_ids}})
        sl_del = db.sleep_logs.delete_many({"user_id": {"$in": test_user_ids}})
        wt_del = db.weight_logs.delete_many({"user_id": {"$in": test_user_ids}})
        msg_del = db.conversation_messages.delete_many({"user_id": {"$in": test_user_ids}})
        sess_del = db.chat_sessions.delete_many({"user_id": {"$in": test_user_ids}})
        u_del = db.users.delete_many({"id": {"$in": test_user_ids}})

        print(f"  ✓ Deleted {fl_del.deleted_count} benchmark food logs")
        print(f"  ✓ Deleted {ex_del.deleted_count} benchmark exercise logs")
        print(f"  ✓ Deleted {hy_del.deleted_count} benchmark hydration logs")
        print(f"  ✓ Deleted {sl_del.deleted_count} benchmark sleep logs")
        print(f"  ✓ Deleted {wt_del.deleted_count} benchmark weight logs")
        print(f"  ✓ Deleted {msg_del.deleted_count} benchmark conversation messages")
        print(f"  ✓ Deleted {sess_del.deleted_count} benchmark chat sessions")
        print(f"  ✓ Deleted {u_del.deleted_count} benchmark test users")

    # Also clean unlinked conversation messages and chat sessions if orphaned
    orphan_msg = db.conversation_messages.delete_many({"user_id": None})
    print(f"  ✓ Cleaned {orphan_msg.deleted_count} orphan conversation messages")

    print("\nVerifying remaining production user counts:")
    rem_users = list(db.users.find({}, {"email": 1}))
    for u in rem_users:
        print(f"  - Active user: {u.get('email')}")

    print("\nDatabase cleanup complete. Storage quota safely restored!")

if __name__ == "__main__":
    cleanup()
