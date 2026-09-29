import asyncio
import aiohttp
import time
import json
import os
import numpy as np

API_BASE = "http://127.0.0.1:3000/api/v1"
BENCHMARK_DIR = os.path.dirname(os.path.abspath(__file__))

async def run_load_test():
    print("Starting Concurrency Load Test (1, 5, 10, 25 users)...")
    connector = aiohttp.TCPConnector(force_close=True, enable_cleanup_closed=True)
    async with aiohttp.ClientSession(connector=connector) as session:
        # Register or login bench_load_user@example.com
        test_email = "bench_load_user@example.com"
        test_pwd = "TestPassword123!"
        
        reg_payload = {"name": "Load Test User", "email": test_email, "password": test_pwd}
        token = None
        async with session.post(f"{API_BASE}/auth/register", json=reg_payload) as r:
            if r.status in (200, 201):
                data = await r.json()
                token = data["data"]["accessToken"]
                print("[OK] Registered fresh test user")
            else:
                # Login
                async with session.post(f"{API_BASE}/auth/login", json={"email": test_email, "password": test_pwd}) as lr:
                    if lr.status == 200:
                        data = await lr.json()
                        token = data["data"]["accessToken"]
                        print("[OK] Logged in existing test user")
                    else:
                        print(f"Auth failed: {lr.status}")
                        return

        sample_queries = [
            "I ate 2 rotis and 1 bowl dal",
            "Had 1 masala dosa with sambar",
            "I drank 500 ml water",
            "Walked for 30 minutes",
            "How many calories are in 1 plate idli?",
        ]

        concurrency_results = {}
        for c in [1, 5, 10, 25]:
            print(f"Testing Concurrency Level: {c} concurrent clients...")
            t0 = time.time()
            lats = []
            errors = 0

            async def worker(idx, q):
                nonlocal errors
                try:
                    w_t0 = time.time()
                    async with session.post(
                        f"{API_BASE}/chat/message",
                        json={"message": q, "sessionId": f"load_sess_{c}_{idx}"},
                        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                        timeout=30
                    ) as r:
                        lat = time.time() - w_t0
                        lats.append(lat)
                        if r.status != 200:
                            errors += 1
                        else:
                            resp = await r.json()
                            if not resp.get("success"):
                                errors += 1
                except Exception as e:
                    errors += 1

            num_requests = max(c * 2, 4)
            tasks = [worker(i, sample_queries[i % len(sample_queries)]) for i in range(num_requests)]
            await asyncio.gather(*tasks)
            total_duration = time.time() - t0

            concurrency_results[f"{c}_users"] = {
                "concurrent_users": c,
                "total_requests": len(tasks),
                "total_duration_sec": round(total_duration, 2),
                "throughput_req_per_sec": round(len(tasks) / total_duration, 2) if total_duration > 0 else 0,
                "mean_latency_sec": round(float(np.mean(lats)), 3) if lats else 0,
                "p95_latency_sec": round(float(np.percentile(lats, 95)), 3) if lats else 0,
                "error_count": errors,
                "error_rate_pct": round((errors / len(tasks)) * 100, 2) if tasks else 0,
            }
            print(f"  -> Concurrency {c}: {round(len(tasks)/total_duration, 1)} req/s, mean latency {round(float(np.mean(lats)), 3)}s, errors: {errors}/{len(tasks)}")

        out_path = os.path.join(BENCHMARK_DIR, "concurrency_load_test.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(concurrency_results, f, indent=2)
        print(f"[OK] Saved updated concurrency results to {out_path}")

if __name__ == "__main__":
    asyncio.run(run_load_test())
