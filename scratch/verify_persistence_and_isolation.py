import asyncio
import os
import sys
import time
import json
import urllib.request
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from app.database import connect_to_mongo, get_db

sys.stdout.reconfigure(encoding="utf-8")

API_BASE = "http://localhost:3000/api/v1"

def api_request(endpoint, method="GET", data=None, token=None):
    url = f"{API_BASE}{endpoint}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8")
            res = json.loads(raw)
            return resp.status, res.get("data") if res.get("data") is not None else res
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"error": raw}

async def run_verification():
    print("================================================================================")
    print("       VERIFYING DATABASE PERSISTENCE, USER ISOLATION & AGGREGATION             ")
    print("================================================================================\n")

    await connect_to_mongo()
    db = get_db()

    # 1. Setup User A and User B
    ts = int(time.time())
    email_a = f"verify_user_a_{ts}@example.com"
    email_b = f"verify_user_b_{ts}@example.com"

    print(f"1. Registering User A ({email_a}) & User B ({email_b})...")
    _, reg_a = api_request("/auth/register", method="POST", data={"name": "User A", "email": email_a, "password": "Password@123"})
    token_a = (reg_a.get("tokens") or {}).get("accessToken") or reg_a.get("accessToken")
    user_a_id = reg_a.get("user", {}).get("id") or (reg_a.get("user") or {}).get("_id")

    _, reg_b = api_request("/auth/register", method="POST", data={"name": "User B", "email": email_b, "password": "Password@123"})
    token_b = (reg_b.get("tokens") or {}).get("accessToken") or reg_b.get("accessToken")
    user_b_id = reg_b.get("user", {}).get("id") or (reg_b.get("user") or {}).get("_id")
    print("   ✓ Both users registered successfully.")

    # 2. Test Food Logging & DB Persistence for User A
    print("\n2. Testing Food Logging & Real MongoDB Persistence...")
    # Log 2 rotis
    code1, resp1 = api_request("/chat/message", method="POST", data={"message": "I ate 2 rotis"}, token=token_a)
    print(f"   Logged 2 rotis: HTTP {code1} -> {resp1.get('message')}")

    # Check MongoDB directly for User A's logs
    docs_a = await db.daily_food_logs.find({"user_id": user_a_id}).to_list(length=10)
    print(f"   Direct MongoDB Query: Found {len(docs_a)} document(s) in 'daily_food_logs' for User A.")
    assert len(docs_a) == 1, f"Expected 1 doc in MongoDB, found {len(docs_a)}"
    doc = docs_a[0]
    print(f"   MongoDB Document Verified: food='{doc.get('food_name')}', qty={doc.get('quantity_amount')} {doc.get('quantity_unit')}, cals={doc.get('calories')}")
    assert doc.get("calories") > 0, "Calories must be > 0"
    print("   ✓ Database Persistence: VERIFIED in MongoDB Atlas.")

    # 3. Test Food Card Aggregation & Calorie Calculations
    print("\n3. Testing Fitbit-style Card Aggregation & Calorie Totals...")
    # Log 3 more rotis for User A
    code2, resp2 = api_request("/chat/message", method="POST", data={"message": "I ate 3 rotis"}, token=token_a)
    print(f"   Logged 3 more rotis: HTTP {code2} -> {resp2.get('message')}")

    # Check MongoDB count
    docs_a_after = await db.daily_food_logs.find({"user_id": user_a_id}).to_list(length=10)
    print(f"   Direct MongoDB Query: Found {len(docs_a_after)} individual documents in DB.")
    assert len(docs_a_after) == 2, f"Expected 2 docs in MongoDB, found {len(docs_a_after)}"

    # Check Grouped Cards in UI response
    cards = (resp2.get("ui") or {}).get("groupedFoodCards") or []
    print(f"   Grouped Food Cards in Response: {len(cards)} card(s)")
    assert len(cards) == 1, f"Expected exactly 1 aggregated Roti card, got {len(cards)}"
    roti_card = cards[0]
    print(f"   Card Details: '{roti_card.get('foodName')}' | Total Qty: {roti_card.get('totalQuantity')} {roti_card.get('unit')} | Total Cals: {roti_card.get('totalCalories')} kcal | Entries: {roti_card.get('entryCount')}")
    assert roti_card.get("totalQuantity") == 5.0, f"Expected total qty 5.0, got {roti_card.get('totalQuantity')}"
    assert roti_card.get("entryCount") == 2, f"Expected entryCount 2, got {roti_card.get('entryCount')}"
    assert roti_card.get("totalCalories") == docs_a_after[0].get("calories") + docs_a_after[1].get("calories"), "Total calories must equal sum of entries"
    print("   ✓ Food Card Aggregation & Calorie Calculation: VERIFIED.")

    # 4. Test Strict User Isolation
    print("\n4. Testing Multi-Tenant User Isolation...")
    # User B checks their food logs
    code_b, resp_b = api_request("/food-logs/today", method="GET", token=token_b)
    print(f"   User B /food-logs/today status: {code_b}, count: {len(resp_b)}")
    assert len(resp_b) == 0, f"User B should have 0 logs, but got {len(resp_b)}"

    # User B checks daily summary
    code_bsum, resp_bsum = api_request("/food-logs/daily-summary", method="GET", token=token_b)
    b_cards = resp_bsum.get("groupedFoodCards") or []
    print(f"   User B /food-logs/daily-summary cards: {len(b_cards)}")
    assert len(b_cards) == 0, f"User B should have 0 cards, got {len(b_cards)}"
    print("   ✓ User Isolation: VERIFIED (User B has zero access to User A's data).")

    # 5. Test False-Positive Logging Prevention on Questions
    print("\n5. Testing False-Positive Logging Prevention...")
    count_before = await db.daily_food_logs.count_documents({"user_id": user_a_id})

    # Question 1: How many calories in 1 bowl dal?
    q1 = "How many calories are in 1 bowl dal?"
    _, r_q1 = api_request("/chat/message", method="POST", data={"message": q1}, token=token_a)
    print(f"   Question: '{q1}' -> Reply: {r_q1.get('message')}")
    assert len((r_q1.get("ui") or {}).get("groupedFoodCards") or []) == 0, "No food cards should be returned"

    # Question 2: Hypothetical
    q2 = "If I eat 2 rotis, how many calories will it have?"
    _, r_q2 = api_request("/chat/message", method="POST", data={"message": q2}, token=token_a)
    print(f"   Question: '{q2}' -> Reply: {r_q2.get('message')}")
    assert len((r_q2.get("ui") or {}).get("groupedFoodCards") or []) == 0, "No food cards should be returned"

    count_after = await db.daily_food_logs.count_documents({"user_id": user_a_id})
    print(f"   MongoDB Log Count before questions: {count_before}, after questions: {count_after}")
    assert count_before == count_after, f"Expected count {count_before}, got {count_after} (False positive log created!)"
    print("   ✓ False-Positive Prevention: VERIFIED (Zero logs created for questions/hypotheticals).")

    print("\n================================================================================")
    print("     ALL 5 CORE VERIFICATION REQUIREMENTS CONFIRMED WITH REAL EVIDENCE          ")
    print("================================================================================\n")

if __name__ == "__main__":
    asyncio.run(run_verification())
