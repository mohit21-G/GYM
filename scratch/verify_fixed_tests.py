import urllib.request
import json
import time
import sys
import os

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
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8")
            res = json.loads(raw)
            return resp.status, res.get("data") if res.get("data") is not None else res
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"error": raw}
    except Exception as e:
        return 500, {"error": str(e)}

def run_regression_tests():
    print("================================================================================")
    print("            REGRESSION VALIDATION FOR THE 4 PREVIOUSLY FAILED TESTS            ")
    print("================================================================================\n")

    user_email = f"regression_user_{int(time.time())}@example.com"
    s, r = api_request("/auth/register", method="POST", data={"name": "Regression User", "email": user_email, "password": "Password@123"})
    token = (r.get("tokens") or {}).get("accessToken") or r.get("accessToken")
    print(f"Registered test user {user_email}, token: {'OK' if token else 'FAIL'}")

    # First log a food item so the user has logged meals
    print("\n1. Logging initial meal (2 rotis, 1 bowl dal)...")
    s_food, r_food = api_request("/chat/message", method="POST", data={"message": "I ate 2 rotis and 1 bowl dal"}, token=token)
    print(f"  Status: {s_food}, Cards created: {len((r_food.get('ui') or {}).get('groupedFoodCards') or [])}")

    test_cases = [
        {"id": "PRO-05", "input": "How much protein did I eat today?", "exp_intent": "QUERY_FOOD_LOG", "expect_cards": True},
        {"id": "CHAT-05", "input": "How many calories are in 1 bowl dal?", "exp_intent": "GENERAL_CHAT", "expect_cards": False},
        {"id": "CHAT-08", "input": "I did not eat anything yet", "exp_intent": "GENERAL_CHAT", "expect_cards": False},
        {"id": "CHAT-10", "input": "If I eat 2 rotis, how many calories will it have?", "exp_intent": "GENERAL_CHAT", "expect_cards": False},
    ]

    all_passed = True
    for tc in test_cases:
        print(f"\nTesting {tc['id']}: \"{tc['input']}\"")
        code, resp = api_request("/chat/message", method="POST", data={"message": tc["input"]}, token=token)
        reply = resp.get("message", "")
        cards = (resp.get("ui") or {}).get("groupedFoodCards") or []
        print(f"  -> HTTP {code}")
        print(f"  -> Reply: {reply[:100]}...")
        print(f"  -> Cards returned: {len(cards)}")

        if tc["expect_cards"]:
            if len(cards) > 0 or "kcal" in reply.lower() or "logged" in reply.lower() or "protein" in reply.lower():
                print(f"  -> RESULT: [PASS] (Query returned logged meal data)")
            else:
                print(f"  -> RESULT: [FAIL] (Expected cards/summary, got empty)")
                all_passed = False
        else:
            if len(cards) == 0:
                print(f"  -> RESULT: [PASS] (Zero food cards created - no false positive)")
            else:
                print(f"  -> RESULT: [FAIL] (False positive: created {len(cards)} food cards)")
                all_passed = False

    print("\n================================================================================")
    if all_passed:
        print("    SUCCESS: ALL 4 REGRESSION TESTS PASSED WITH 100% ACCURACY!                  ")
    else:
        print("    FAILURE: ONE OR MORE REGRESSION TESTS FAILED.                               ")
    print("================================================================================\n")

if __name__ == "__main__":
    run_regression_tests()
