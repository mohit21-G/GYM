import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from ..database import get_db
from ..schemas.food_log import CreateFoodLogDto, UpdateFoodLogDto
from ..services.auth_service import get_current_user
from ..services.food_service import FoodService
from ..services.time_service import TimeService

router = APIRouter(prefix="/food-logs", tags=["Food Logs"])

@router.get("/today")
async def get_today_food_logs(
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    user_id = current_user.get("id") or str(current_user.get("_id"))
    today_str = TimeService.get_current_local_date_str()
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
    target_date = date or TimeService.get_current_local_date_str()
    return await FoodService.get_daily_grouped_food_cards(user_id, target_date)

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_food_log(
    dto: CreateFoodLogDto,
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    user_id = current_user.get("id") or str(current_user.get("_id"))
    now = TimeService.get_current_local_datetime()
    target_date = TimeService.get_current_local_date_str()
    if dto.loggedAt:
        try:
            target_date = dto.loggedAt.split("T")[0]
        except Exception:
            pass

    # Auto-resolve nutrition if not provided
    calories = dto.calories
    protein_g = dto.proteinG
    carbs_g = dto.carbsG
    fat_g = dto.fatG
    fiber_g = dto.fiberG
    food_id = dto.foodId

    if not calories or calories == 0.0:
        resolved = await FoodService.resolve_food(dto.foodName)
        food_id = food_id or resolved.get("food_id") or f"custom_{uuid.uuid4().hex[:8]}"
        multiplier = FoodService.calculate_portion_multiplier(
            base_unit=resolved.get("unit", "serving"),
            requested_unit=dto.unit or resolved.get("unit", "serving"),
            quantity=dto.quantity or 1.0,
            food_name=resolved.get("food_name", dto.foodName),
        )
        calories = round(resolved.get("calories", 0.0) * multiplier, 1)
        protein_g = round(resolved.get("protein_g", 0.0) * multiplier, 1)
        carbs_g = round(resolved.get("carbs_g", 0.0) * multiplier, 1)
        fat_g = round(resolved.get("fat_g", 0.0) * multiplier, 1)
        fiber_g = round(resolved.get("fiber_g", 0.0) * multiplier, 1)

    log_id = str(uuid.uuid4())
    doc = {
        "id": log_id,
        "user_id": user_id,
        "food_id": food_id or f"custom_{uuid.uuid4().hex[:8]}",
        "food_name": dto.foodName,
        "meal_type": dto.mealType or "—",
        "quantity_amount": dto.quantity,
        "quantity_unit": dto.unit,
        "calories": calories or 0.0,
        "protein_g": protein_g or 0.0,
        "carbs_g": carbs_g or 0.0,
        "fat_g": fat_g or 0.0,
        "fiber_g": fiber_g or 0.0,
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
    query: Dict[str, Any] = {"user_id": user_id}
    from bson import ObjectId
    if ObjectId.is_valid(id):
        query["$or"] = [{"id": id}, {"_id": ObjectId(id)}]
    else:
        query["id"] = id

    doc = await db.daily_food_logs.find_one(query)
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
    query: Dict[str, Any] = {"user_id": user_id}
    from bson import ObjectId
    if ObjectId.is_valid(id):
        query["$or"] = [{"id": id}, {"_id": ObjectId(id)}]
    else:
        query["id"] = id
    
    existing = await db.daily_food_logs.find_one(query)
    if not existing:
        raise HTTPException(status_code=404, detail="Food log not found")

    target_food_name = dto.foodName if dto.foodName is not None else existing.get("food_name", "Food")
    target_quantity = float(dto.quantity) if dto.quantity is not None else float(existing.get("quantity_amount", 1.0))
    target_unit = dto.unit if dto.unit is not None else existing.get("quantity_unit", "serving")

    # Recalculate nutrition automatically from food database & portion multiplier
    resolved = await FoodService.resolve_food(target_food_name)
    multiplier = FoodService.calculate_portion_multiplier(
        base_unit=resolved.get("unit", "serving"),
        requested_unit=target_unit,
        quantity=target_quantity,
        food_name=resolved.get("food_name", target_food_name),
    )

    recalculated_cal = round(resolved["calories"] * multiplier, 1)
    recalculated_p = round(resolved["protein_g"] * multiplier, 1)
    recalculated_c = round(resolved["carbs_g"] * multiplier, 1)
    recalculated_f = round(resolved["fat_g"] * multiplier, 1)
    recalculated_fib = round(resolved["fiber_g"] * multiplier, 1)

    update_data: Dict[str, Any] = {
        "food_name": resolved.get("food_name", target_food_name),
        "food_id": resolved.get("food_id"),
        "quantity_amount": target_quantity,
        "quantity_unit": target_unit,
        "calories": dto.calories if dto.calories is not None else recalculated_cal,
        "protein_g": dto.proteinG if dto.proteinG is not None else recalculated_p,
        "carbs_g": dto.carbsG if dto.carbsG is not None else recalculated_c,
        "fat_g": dto.fatG if dto.fatG is not None else recalculated_f,
        "fiber_g": dto.fiberG if dto.fiberG is not None else recalculated_fib,
        "updated_at": datetime.now(timezone.utc),
    }

    if dto.mealType is not None:
        update_data["meal_type"] = dto.mealType
    if dto.notes is not None:
        update_data["notes"] = dto.notes

    if dto.loggedAt is not None:
        try:
            update_data["logged_at"] = datetime.fromisoformat(dto.loggedAt.replace("Z", "+00:00"))
            update_data["has_explicit_time"] = True
        except Exception:
            try:
                local_now = TimeService.get_current_local_datetime()
                parsed_dt, has_t = TimeService.extract_time_from_text(dto.loggedAt, reference_time=local_now)
                if has_t:
                    update_data["logged_at"] = parsed_dt
                    update_data["has_explicit_time"] = True
            except Exception:
                pass

    await db.daily_food_logs.update_one(query, {"$set": update_data})
    
    updated = await db.daily_food_logs.find_one(query)
    updated.pop("_id", None)

    # Sync conversation messages in MongoDB so session history never reverts on refresh
    stable_log_id = updated.get("id") or str(id)
    await FoodService.sync_food_log_to_conversation_messages(
        user_id=user_id,
        log_id=stable_log_id,
        updated_entry=updated,
        is_deleted=False,
    )

    log_date = updated.get("log_date") or TimeService.get_current_local_date_str()
    summary_result = await FoodService.get_daily_grouped_food_cards(user_id, log_date)
    from ..services.dashboard_service import DashboardService
    dashboard_data = await DashboardService.get_today_dashboard(user_id, log_date)

    # Format return response to conform to FoodLogEntrySummary
    dt = updated.get("logged_at") or updated.get("created_at") or datetime.now(timezone.utc)
    has_exp_time = updated.get("has_explicit_time", False)
    time_formatted = FoodService.format_time(dt) if has_exp_time else ""

    entry_data = {
        **updated,
        "id": stable_log_id,
        "foodMasterId": updated.get("food_id"),
        "foodName": updated.get("food_name"),
        "quantity": updated.get("quantity_amount"),
        "unit": updated.get("quantity_unit"),
        "calories": updated.get("calories"),
        "loggedAt": dt.isoformat() if hasattr(dt, "isoformat") else str(dt),
        "timeFormatted": time_formatted,
        "hasExplicitTime": bool(has_exp_time),
        "mealType": updated.get("meal_type", "—"),
        "macros": {
            "proteinG": updated.get("protein_g", 0.0),
            "carbsG": updated.get("carbs_g", 0.0),
            "fatG": updated.get("fat_g", 0.0),
            "fiberG": updated.get("fiber_g", 0.0),
        },
    }

    return {
        "success": True,
        "entry": entry_data,
        "dailyNutritionSummary": summary_result["dailyNutritionSummary"].model_dump(),
        "groupedFoodCards": [c.model_dump() for c in summary_result["groupedFoodCards"]],
        "dashboard": dashboard_data,
        **entry_data,
    }

@router.delete("/{id}")
async def delete_food_log(
    id: str,
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    user_id = current_user.get("id") or str(current_user.get("_id"))
    query: Dict[str, Any] = {"user_id": user_id}
    from bson import ObjectId
    if ObjectId.is_valid(id):
        query["$or"] = [{"id": id}, {"_id": ObjectId(id)}]
    else:
        query["id"] = id

    existing = await db.daily_food_logs.find_one(query)
    if not existing:
        raise HTTPException(status_code=404, detail="Food log not found")

    target_log_id = existing.get("id") or str(existing.get("_id") or id)
    target_date = existing.get("log_date") or TimeService.get_current_local_date_str()

    res = await db.daily_food_logs.delete_one(query)
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Food log not found")

    # Sync conversation messages in MongoDB
    await FoodService.sync_food_log_to_conversation_messages(
        user_id=user_id,
        log_id=target_log_id,
        is_deleted=True,
    )

    summary_result = await FoodService.get_daily_grouped_food_cards(user_id, target_date)
    from ..services.dashboard_service import DashboardService
    dashboard_data = await DashboardService.get_today_dashboard(user_id, target_date)

    return {
        "success": True,
        "deleted": True,
        "id": id,
        "dailyNutritionSummary": summary_result["dailyNutritionSummary"].model_dump(),
        "groupedFoodCards": [c.model_dump() for c in summary_result["groupedFoodCards"]],
        "dashboard": dashboard_data,
    }
