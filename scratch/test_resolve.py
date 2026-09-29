import asyncio
import os
import sys

# Ensure backend can be imported
sys.path.insert(0, os.path.abspath("."))

from backend.app.database import connect_to_mongo, get_db
from backend.app.services.food_service import FoodService

async def main():
    await connect_to_mongo()
    db = get_db()
    queries = [
        "sev tameta",
        "1 bowl shak savare lidhu",
        "shak",
        "okra sabzi",
        "butter naan",
        "1 બાસુંદી",
        "1.5 ખીચડી",
        "alu dosa",
        "આજે 1 કઢી ખાધું",
        "2 uttapam dinner ma lidhu",
        "pneeeer pleez trac",
        "Sev Tameta Nu Shaak'; DROP TABLE daily_food_logs; --"
    ]
    for q in queries:
        res = await FoodService.resolve_food(q)
        print(f"QUERY: {q!r:35} -> NAME: {res.get('food_name')} | ID: {res.get('food_id')}")

if __name__ == "__main__":
    asyncio.run(main())
