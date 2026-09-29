import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from ..database import get_db
from ..schemas.food_log import CreateFoodLogDto, UpdateFoodLogDto
from ..services.auth_service import get_current_user
from ..services.food_service import FoodService

router = APIRouter(prefix="/food-logs", tags=["Food Logs"])

@router.get("/today")
async def get_today_food_logs(
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    user_id = current_user.get("id") or str(current_user.get("_id"))
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    cursor = db.daily_food_logs.find({"user_id": user_id, "log_date": today_str}).sort("created_at", -1)
    docs = await cursor.to_list(length=100)
    for d in docs:
        d.pop("_id", None)
    return docs

@router.get("/daily-summary")
async def get_daily_summary(
    date: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user.get("id") or str(current_user.get("_id"))
    target_date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return await FoodService.get_daily_grouped_food_cards(user_id, target_date)

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_food_log(
    dto: CreateFoodLogDto,
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    user_id = current_user.get("id") or str(current_user.get("_id"))
    now = datetime.now(timezone.utc)
    target_date = now.strftime("%Y-%m-%d")
    if dto.loggedAt:
        try:
            target_date = dto.loggedAt.split("T")[0]
        except Exception:
            pass

    log_id = str(uuid.uuid4())
    doc = {
        "id": log_id,
        "user_id": user_id,
        "food_id": dto.foodId or f"custom_{uuid.uuid4().hex[:8]}",
        "food_name": dto.foodName,
        "meal_type": dto.mealType or "SNACK",
        "quantity_amount": dto.quantity,
        "quantity_unit": dto.unit,
        "calories": dto.calories or 0.0,
        "protein_g": dto.proteinG or 0.0,
        "carbs_g": dto.carbsG or 0.0,
        "fat_g": dto.fatG or 0.0,
        "fiber_g": dto.fiberG or 0.0,
        "notes": dto.notes,
        "source": dto.source or "MANUAL",
        "log_date": target_date,
        "created_at": now,
        "logged_at": now,
    }
    await db.daily_food_logs.insert_one(doc)
    doc.pop("_id", None)
    return doc

@router.get("")
async def list_food_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(15, ge=1, le=100),
    startDate: Optional[str] = None,
    endDate: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    user_id = current_user.get("id") or str(current_user.get("_id"))
    
    query: Dict[str, Any] = {"user_id": user_id}
    if startDate or endDate:
        query["log_date"] = {}
        if startDate:
            query["log_date"]["$gte"] = startDate
        if endDate:
            query["log_date"]["$lte"] = endDate

    skip = (page - 1) * limit
    total = await db.daily_food_logs.count_documents(query)
    cursor = db.daily_food_logs.find(query).sort("created_at", -1).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)

    items = []
    for d in docs:
        dt = d.get("logged_at") or d.get("created_at") or datetime.now(timezone.utc)
        items.append({
            "id": d.get("id") or str(d.get("_id")),
            "foodName": d.get("food_name"),
            "mealType": d.get("meal_type", "SNACK"),
            "quantity": d.get("quantity_amount", 1),
            "unit": d.get("quantity_unit", "serving"),
            "calories": d.get("calories", 0),
            "proteinG": d.get("protein_g", 0),
            "carbsG": d.get("carbs_g", 0),
            "fatG": d.get("fat_g", 0),
            "fiberG": d.get("fiber_g", 0),
            "loggedAt": dt.isoformat() if hasattr(dt, "isoformat") else str(dt),
            "source": d.get("source", "MANUAL"),
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "totalPages": (total + limit - 1) // limit if limit > 0 else 1,
    }

@router.get("/{id}")
async def get_single_food_log(
    id: str,
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    user_id = current_user.get("id") or str(current_user.get("_id"))
    doc = await db.daily_food_logs.find_one({"id": id, "user_id": user_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Food log not found")
    doc.pop("_id", None)
    return doc

@router.patch("/{id}")
async def update_food_log(
    id: str,
    dto: UpdateFoodLogDto,
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    user_id = current_user.get("id") or str(current_user.get("_id"))
    
    update_data = {}
    if dto.foodName is not None: update_data["food_name"] = dto.foodName
    if dto.mealType is not None: update_data["meal_type"] = dto.mealType
    if dto.quantity is not None: update_data["quantity_amount"] = dto.quantity
    if dto.unit is not None: update_data["quantity_unit"] = dto.unit
    if dto.calories is not None: update_data["calories"] = dto.calories
    if dto.proteinG is not None: update_data["protein_g"] = dto.proteinG
    if dto.carbsG is not None: update_data["carbs_g"] = dto.carbsG
    if dto.fatG is not None: update_data["fat_g"] = dto.fatG
    if dto.fiberG is not None: update_data["fiber_g"] = dto.fiberG
    if dto.notes is not None: update_data["notes"] = dto.notes

    res = await db.daily_food_logs.update_one({"id": id, "user_id": user_id}, {"$set": update_data})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Food log not found")
    
    updated = await db.daily_food_logs.find_one({"id": id})
    updated.pop("_id", None)
    return updated

@router.delete("/{id}")
async def delete_food_log(
    id: str,
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    user_id = current_user.get("id") or str(current_user.get("_id"))
    res = await db.daily_food_logs.delete_one({"id": id, "user_id": user_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Food log not found")
    return {"deleted": True, "id": id}
