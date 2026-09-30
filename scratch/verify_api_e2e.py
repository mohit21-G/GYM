import sys
import os
from zoneinfo import ZoneInfo
from datetime import datetime

sys.path.insert(0, os.path.abspath("."))

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.auth_service import create_access_token
from backend.app.services.time_service import TimeService

import uuid

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

IST = ZoneInfo("Asia/Kolkata")

def main():
    print("=" * 60)
    print("STARTING REAL FASTAPI END-TO-END VERIFICATION")
    print("=" * 60)

    client = TestClient(app)

    # Health check
    res = client.get("/api/v1/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print("[PASS] /api/v1/health endpoint status:", res.json())

    # Create test auth token and seed user
    import asyncio
    from backend.app.database import get_db

    test_user_id = f"test_user_prod_{uuid.uuid4().hex[:8]}"
    token = create_access_token({"sub": test_user_id})
    headers = {"Authorization": f"Bearer {token}"}

    async def seed():
        db = get_db()
        await db.users.insert_one({
            "id": test_user_id,
            "email": f"{test_user_id}@fit.com",
            "username": "e2e_tester",
            "role": "USER"
        })
    asyncio.run(seed())

    def get_data(resp):
        assert resp.status_code == 200, f"Call failed ({resp.status_code}): {resp.text}"
        j = resp.json()
        if isinstance(j, dict) and "data" in j and "statusCode" in j:
            return j["data"]
        return j

    # Frozen clock check for omitted time
    mock_now = datetime(2026, 9, 30, 10, 8, 35, tzinfo=IST)
    TimeService.set_mock_now(mock_now)
    try:
        # 1. Test omitted time
        r1 = client.post("/api/v1/chat/message", json={"message": "Aaje protein shake lidho"}, headers=headers)
        data1 = get_data(r1)
        msg1 = data1.get("message") or str(data1)
        print("[PASS] 1. Aaje protein shake lidho ->", msg1[:60] + "...")
        assert data1.get("success") is True

        # 2. Test explicit time 4:27 PM
        r2 = client.post("/api/v1/chat/message", json={"message": "At 4:27 PM protein shake lidho"}, headers=headers)
        data2 = get_data(r2)
        msg2 = data2.get("message") or str(data2)
        print("[PASS] 2. At 4:27 PM protein shake lidho ->", msg2[:60] + "...")
        assert data2.get("success") is True

        # 3. Test Gujarati script explicit time
        r3 = client.post("/api/v1/chat/message", json={"message": "સાંજે 4:27 પ્રોટીન શેક પીધો"}, headers=headers)
        data3 = get_data(r3)
        msg3 = data3.get("message") or str(data3)
        print("[PASS] 3. સાંજે 4:27 પ્રોટીન શેક પીધો ->", msg3[:60] + "...")
        assert data3.get("success") is True

        # 4. Test Hindi script explicit time
        r4 = client.post("/api/v1/chat/message", json={"message": "शाम 4:27 बजे प्रोटीन शेक लिया"}, headers=headers)
        data4 = get_data(r4)
        msg4 = data4.get("message") or str(data4)
        print("[PASS] 4. शाम 4:27 बजे प्रोटीन शेक लिया ->", msg4[:60] + "...")
        assert data4.get("success") is True

        # 5. Morning meal
        r5 = client.post("/api/v1/chat/message", json={"message": "Savare 8:30 poha khadha"}, headers=headers)
        data5 = get_data(r5)
        msg5 = data5.get("message") or str(data5)
        print("[PASS] 5. Savare 8:30 poha khadha ->", msg5[:60] + "...")
        assert data5.get("success") is True

        # 6. Afternoon lunch
        r6 = client.post("/api/v1/chat/message", json={"message": "Bapore 1:15 dal rice khadha"}, headers=headers)
        data6 = get_data(r6)
        msg6 = data6.get("message") or str(data6)
        print("[PASS] 6. Bapore 1:15 dal rice khadha ->", msg6[:60] + "...")
        assert data6.get("success") is True

        # 7. Night dinner
        r7 = client.post("/api/v1/chat/message", json={"message": "Ratre 9:00 dal roti khai"}, headers=headers)
        data7 = get_data(r7)
        msg7 = data7.get("message") or str(data7)
        print("[PASS] 7. Ratre 9:00 dal roti khai ->", msg7[:60] + "...")
        assert data7.get("success") is True

        # 8. Date + time combination (Yesterday night)
        r8 = client.post("/api/v1/chat/message", json={"message": "Gai kale ratre 11:30 protein shake lidho"}, headers=headers)
        data8 = get_data(r8)
        msg8 = data8.get("message") or str(data8)
        print("[PASS] 8. Gai kale ratre 11:30 protein shake lidho ->", msg8[:60] + "...")
        assert data8.get("success") is True

        # 9. Relative time
        r9 = client.post("/api/v1/chat/message", json={"message": "2 hours ago 30 min walking kari"}, headers=headers)
        data9 = get_data(r9)
        msg9 = data9.get("message") or str(data9)
        print("[PASS] 9. 2 hours ago 30 min walking kari ->", msg9[:60] + "...")
        assert data9.get("success") is True

        # 10. Multiline message
        multiline_msg = """8:30 AM 2 eggs khadha
1:00 PM dal rice khadhu
6:00 PM 30 min walking kari"""
        r10 = client.post("/api/v1/chat/message", json={"message": multiline_msg}, headers=headers)
        data10 = get_data(r10)
        msg10 = data10.get("message") or str(data10)
        print("[PASS] 10. Multiline 3-action message ->", msg10[:60] + "...")
        assert data10.get("success") is True

        # 11. Dashboard synchronization verification
        r_dash = client.get("/api/v1/dashboard/today", headers=headers)
        dash_data = get_data(r_dash)
        print("[PASS] 11. /dashboard/today returned synchronized data:")
        print(f"       Date: {dash_data['date']}")
        print(f"       Calories consumed: {dash_data['calories']['consumed']} kcal")
        print(f"       Calories burned: {dash_data['calories']['burned']} kcal")
        print(f"       Net calories: {dash_data['calories']['net']} kcal")
        assert dash_data["calories"]["consumed"] > 0
        assert dash_data["calories"]["burned"] > 0

    finally:
        TimeService.reset_mock_now()

    print("=" * 60)
    print("ALL REAL FASTAPI E2E CALLS VERIFIED SUCCESSFULLY")
    print("=" * 60)

if __name__ == "__main__":
    main()
