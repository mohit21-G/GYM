import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath("."))
import uuid
from backend.app.database import connect_to_mongo, close_mongo_connection, db_instance
from backend.app.services.chat_service import ChatService
from backend.app.schemas.food_log import CreateFoodLogDto, UpdateFoodLogDto
from backend.app.routers.food_logs import create_food_log, update_food_log, delete_food_log, get_single_food_log

async def verify_real_mongo():
    await connect_to_mongo()
    db = db_instance.db
    assert db is not None, "db is None"
    print("Testing on real MongoDB Atlas database:", db.name)

    user_id = f"test_live_{uuid.uuid4().hex[:6]}"
    session_id = f"session_live_{uuid.uuid4().hex[:6]}"
    current_user = {"id": user_id}

    # 1. CREATE Bhakri via API route
    dto_create = CreateFoodLogDto(foodName="Bhakri", quantity=1.0, unit="piece", mealType="—")
    create_res = await create_food_log(dto=dto_create, current_user=current_user)
    log_id = create_res["id"]
    print(f"1. Created Bhakri via POST with id: {log_id}")

    # Verify directly in real Mongo collection
    doc1 = await db.daily_food_logs.find_one({"id": log_id})
    assert doc1 is not None, "Document not found in real Mongo"
    assert doc1["food_name"] == "Bhakri", f"Expected Bhakri, got {doc1['food_name']}"
    assert doc1["calories"] == 130.0, f"Expected 130.0 kcal, got {doc1['calories']}"
    print(f"   -> Verified persisted in MongoDB: {doc1['food_name']} ({doc1['calories']} kcal)")

    # 2. EDIT: Bhakri -> Roti 2 pieces via PATCH /food-logs/{id}
    dto_patch = UpdateFoodLogDto(foodName="Roti", quantity=2.0, unit="piece", mealType="—")
    patch_res = await update_food_log(id=log_id, dto=dto_patch, current_user=current_user)
    assert patch_res["success"] is True
    print("2. Patched to Roti (2 pieces)")

    # Verify in real Mongo collection
    doc2 = await db.daily_food_logs.find_one({"id": log_id})
    assert doc2 is not None
    assert doc2["food_name"] == "Roti", f"Expected Roti in DB, got {doc2['food_name']}"
    assert doc2["quantity_amount"] == 2.0, f"Expected 2.0 qty in DB, got {doc2['quantity_amount']}"
    assert doc2["calories"] == 208.0, f"Expected 208.0 kcal in DB, got {doc2['calories']}"
    print(f"   -> Verified persisted in MongoDB: {doc2['food_name']} ({doc2['calories']} kcal)")

    # 3. GET food log
    get_res = await get_single_food_log(id=log_id, current_user=current_user)
    assert get_res["food_name"] == "Roti"
    assert get_res["quantity_amount"] == 2.0
    assert get_res["calories"] == 208.0
    print("3. GET verified from MongoDB: still Roti (208.0 kcal)")

    # 4. DELETE
    del_res = await delete_food_log(id=log_id, current_user=current_user)
    assert del_res["deleted"] is True
    print("4. Deleted food log via DELETE")

    # Verify deleted in real Mongo collection
    doc3 = await db.daily_food_logs.find_one({"id": log_id})
    assert doc3 is None, f"Expected None after delete in DB, got {doc3}"
    print("   -> Verified deleted from MongoDB (document is None)")

    # 5. MULTIPLE CREATE via ChatService: "me 2 rotli ane 1 bowl dal khai"
    chat_res = await ChatService.handle_user_message(
        user_id=user_id,
        message="me 2 rotli ane 1 bowl dal khai",
        session_id_input=session_id
    )
    cards = chat_res["ui"]["groupedFoodCards"]
    print("5. Created multiple items via chat:", [c["foodName"] for c in cards])
    assert len(cards) == 2

    # Verify both records in real MongoDB
    all_multi = await db.daily_food_logs.find({"user_id": user_id}).to_list(10)
    assert len(all_multi) == 2, f"Expected 2 documents in real Mongo, got {len(all_multi)}"
    names = {d["food_name"] for d in all_multi}
    assert "Roti" in names and any("Dal" in n for n in names)
    assert all_multi[0]["id"] != all_multi[1]["id"]
    print(f"   -> Verified 2 separate records in MongoDB with unique IDs: {[d['id'] for d in all_multi]}")

    # Verify conversation_messages sync on real Mongo
    msg_doc = await db.conversation_messages.find_one({"session_id": session_id, "sender": "ASSISTANT"})
    assert msg_doc is not None
    import json
    raw = msg_doc["raw_entities"]
    parsed_cards = (json.loads(raw) if isinstance(raw, str) else raw)["groupedFoodCards"]
    assert len(parsed_cards) == 2

    # Cleanup test records
    await db.daily_food_logs.delete_many({"user_id": user_id})
    await db.conversation_messages.delete_many({"session_id": session_id})
    await db.chat_sessions.delete_many({"user_id": user_id})
    print("\n>>> ALL REAL MONGODB CRUD AND PERSISTENCE ASSERTIONS PASSED! <<<")
    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(verify_real_mongo())
