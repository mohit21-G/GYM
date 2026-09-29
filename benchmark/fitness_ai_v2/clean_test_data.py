import pymongo

MONGO_URI = "mongodb+srv://mohit_db:Mohit2107@mohitai.ljuscm2.mongodb.net/?appName=mohitAI"
DB_NAME = "fitness_chatbot"

SAFE_EMAILS = {
    "admin@fitness-ai.com",
    "admin@fitness-ai.com".lower(),
    "fitbit_demo@example.com",
    "dhoni@gmail.com"
}

def clean():
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DB_NAME]
    
    print("Identifying test users to delete while protecting production users...")
    all_users = list(db.users.find({}, {"email": 1}))
    test_uids = []
    test_emails = []
    
    for u in all_users:
        em = u.get("email", "").lower()
        if em not in SAFE_EMAILS:
            test_uids.append(u["_id"])
            test_emails.append(u.get("email"))
            
    print(f"Preserving production users: {SAFE_EMAILS}")
    print(f"Targeting test users for removal: {test_emails} (Total: {len(test_uids)})")
    
    # 1. Delete conversation messages for test users or test sessions
    res_m = db.conversation_messages.delete_many({
        "$or": [
            {"userId": {"$in": test_uids}},
            {"userId": {"$in": [str(uid) for uid in test_uids]}},
            {"sessionId": {"$regex": r"^bench_"}},
            {"sessionId": {"$regex": r"^load_"}}
        ]
    })
    print(f"Deleted {res_m.deleted_count} conversation messages")
    
    # Also delete orphan conversation messages if any without safe userId
    safe_uids = [u["_id"] for u in all_users if u.get("email", "").lower() in SAFE_EMAILS]
    safe_uid_strs = [str(uid) for uid in safe_uids]
    res_orphan = db.conversation_messages.delete_many({
        "userId": {"$nin": safe_uids + safe_uid_strs}
    })
    print(f"Deleted {res_orphan.deleted_count} orphan/unlinked test messages")
    
    # 2. Delete daily_food_logs
    res_f = db.daily_food_logs.delete_many({
        "userId": {"$nin": safe_uids + safe_uid_strs}
    })
    print(f"Deleted {res_f.deleted_count} benchmark food logs")
    
    # 3. Delete exercise logs
    res_e = db.daily_exercise_logs.delete_many({
        "userId": {"$nin": safe_uids + safe_uid_strs}
    })
    print(f"Deleted {res_e.deleted_count} benchmark exercise logs")
    
    # 4. Delete hydration, sleep, weight
    res_h = db.hydration_logs.delete_many({"userId": {"$nin": safe_uids + safe_uid_strs}})
    print(f"Deleted {res_h.deleted_count} benchmark hydration logs")
    
    res_s = db.sleep_logs.delete_many({"userId": {"$nin": safe_uids + safe_uid_strs}})
    print(f"Deleted {res_s.deleted_count} benchmark sleep logs")
    
    res_w = db.weight_logs.delete_many({"userId": {"$nin": safe_uids + safe_uid_strs}})
    print(f"Deleted {res_w.deleted_count} benchmark weight logs")
    
    # 5. Delete test users
    if test_uids:
        res_u = db.users.delete_many({"_id": {"$in": test_uids}})
        print(f"Deleted {res_u.deleted_count} test users")
        
    print("\nVerifying remaining document counts in MongoDB Atlas:")
    for col_name in db.list_collection_names():
        count = db[col_name].count_documents({})
        print(f"  {col_name}: {count} documents")
        
    print("\nDatabase cleanup complete. Storage quota safely restored!")

if __name__ == "__main__":
    clean()
