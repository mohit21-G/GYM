import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from ..database import get_db
from ..schemas.activity_log import CreateHydrationLogDto, UpdateHydrationLogDto
from ..services.auth_service import get_current_user
from ..services.hydration_service import HydrationService
from ..services.dashboard_service import DashboardService
from ..services.time_service import TimeService

router = APIRouter(prefix="/hydration-logs", tags=["Hydration Logs"])


def _ownership_query(id: str, user_id: str) -> Dict[str, Any]:
    """Build a query matching either the custom 'id' field or a valid Mongo
    ObjectId for '_id', mirroring the pattern used in food_logs.py so legacy
    documents without a custom id are still editable/deletable."""
    from bson import ObjectId
    query: Dict[str, Any] = {"user_id": user_id}
    if ObjectId.is_valid(id):
        query["$or"] = [{"id": id}, {"_id": ObjectId(id)}]
    else:
        query["id"] = id
    return query

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_hydration_log(
    dto: CreateHydrationLogDto,
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    user_id = current_user.get("id") or str(current_user.get("_id"))
    now = datetime.now(timezone.utc)
    log_id = str(uuid.uuid4())
    
    amount = dto.amountMl or dto.amount or 250
    logged_at_dt = datetime.fromisoformat(dto.loggedAt.replace("Z", "+00:00")) if dto.loggedAt else now
    date_str = logged_at_dt.strftime("%Y-%m-%d")

    doc = {
        "id": log_id,
        "user_id": user_id,
        "amount_ml": amount,
        "log_date": date_str,
        "logged_at": logged_at_dt,
        "source": dto.source or "MANUAL",
        "notes": dto.notes,
        "created_at": now,
        "updated_at": now,
    }

    await db.hydration_logs.insert_one(doc)

    return {
        "id": log_id,
        "userId": user_id,
        "amountMl": amount,
        "loggedAt": logged_at_dt.isoformat(),
        "source": doc["source"],
        "notes": doc["notes"],
        "createdAt": now.isoformat(),
        "updatedAt": now.isoformat(),
    }

@router.get("")
async def list_hydration_logs(
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
        if startDate: query["log_date"]["$gte"] = startDate
        if endDate: query["log_date"]["$lte"] = endDate

    skip = (page - 1) * limit
    total = await db.hydration_logs.count_documents(query)
    cursor = db.hydration_logs.find(query).sort("logged_at", -1).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)

    items = []
    for d in docs:
        dt = d.get("logged_at") or d.get("created_at") or datetime.now(timezone.utc)
        h_cal = float(d.get("calories") or 0.0)
        items.append({
            "id": d.get("id") or str(d.get("_id")),
            "amountMl": d.get("amount_ml", 0),
            "beverageName": d.get("beverage_name") or d.get("notes") or "Water",
            "loggedAt": dt.isoformat() if hasattr(dt, "isoformat") else str(dt),
            "source": d.get("source", "MANUAL"),
            "notes": d.get("notes"),
            "quantity": d.get("quantity"),
            "calories": h_cal if h_cal > 0 else None,
            "proteinG": float(d.get("protein_g") or 0.0) if h_cal > 0 else None,
            "carbsG": float(d.get("carbs_g") or 0.0) if h_cal > 0 else None,
            "fatG": float(d.get("fat_g") or 0.0) if h_cal > 0 else None,
            "fiberG": float(d.get("fiber_g") or 0.0) if h_cal > 0 else None,
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "totalPages": (total + limit - 1) // limit if limit > 0 else 1,
    }

@router.get("/{id}")
async def get_hydration_log(
    id: str,
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    user_id = current_user.get("id") or str(current_user.get("_id"))
    doc = await db.hydration_logs.find_one(_ownership_query(id, user_id))
    if not doc:
        raise HTTPException(status_code=404, detail="Hydration log not found")
    dt = doc.get("logged_at") or doc.get("created_at")
    h_cal = float(doc.get("calories") or 0.0)
    return {
        "id": doc.get("id") or str(doc.get("_id")),
        "amountMl": doc.get("amount_ml", 0),
        "beverageName": doc.get("beverage_name") or doc.get("notes") or "Water",
        "loggedAt": dt.isoformat() if hasattr(dt, "isoformat") else str(dt),
        "source": doc.get("source", "MANUAL"),
        "notes": doc.get("notes"),
        "quantity": doc.get("quantity"),
        "calories": h_cal if h_cal > 0 else None,
        "proteinG": float(doc.get("protein_g") or 0.0) if h_cal > 0 else None,
        "carbsG": float(doc.get("carbs_g") or 0.0) if h_cal > 0 else None,
        "fatG": float(doc.get("fat_g") or 0.0) if h_cal > 0 else None,
        "fiberG": float(doc.get("fiber_g") or 0.0) if h_cal > 0 else None,
    }

@router.patch("/{id}")
async def update_hydration_log(
    id: str,
    dto: UpdateHydrationLogDto,
    current_user: dict = Depends(get_current_user),
):
    """Edit an existing hydration entry (amount, beverage name, or time).
    Mirrors PATCH /food-logs/{id}: recomputes the daily hydration summary and
    keeps persisted chat history in sync via HydrationService."""
    db = get_db()
    user_id = current_user.get("id") or str(current_user.get("_id"))
    query = _ownership_query(id, user_id)

    existing = await db.hydration_logs.find_one(query)
    if not existing:
        raise HTTPException(status_code=404, detail="Hydration log not found")

    update_data: Dict[str, Any] = {"updated_at": datetime.now(timezone.utc)}
    if dto.amountMl is not None:
        if dto.amountMl <= 0:
            raise HTTPException(status_code=422, detail="amountMl must be greater than 0")
        update_data["amount_ml"] = float(dto.amountMl)
    if dto.beverageName is not None:
        update_data["beverage_name"] = dto.beverageName
        update_data["notes"] = dto.beverageName
    if dto.notes is not None:
        update_data["notes"] = dto.notes

    # Recalculate supplement nutrition when the quantity (scoop count) or the
    # beverage name changes to/from a known supplement, mirroring how
    # PATCH /food-logs/{id} recalculates nutrition from the canonical profile.
    target_beverage = dto.beverageName if dto.beverageName is not None else (
        existing.get("beverage_name") or existing.get("notes") or "Water"
    )
    SUPPLEMENT_PROFILES = {"Pre Workout", "Whey Protein Powder"}
    if target_beverage in SUPPLEMENT_PROFILES:
        from ..services.food_service import CANONICAL_INDIAN_FOOD_PROFILES
        target_qty = dto.quantity if dto.quantity is not None else float(existing.get("quantity") or 1.0)
        profile = CANONICAL_INDIAN_FOOD_PROFILES.get(target_beverage, {})
        update_data["quantity"] = target_qty
        update_data["calories"] = round(float(profile.get("calories", 0.0)) * target_qty, 1)
        update_data["protein_g"] = round(float(profile.get("protein_g", 0.0)) * target_qty, 1)
        update_data["carbs_g"] = round(float(profile.get("carbs_g", 0.0)) * target_qty, 1)
        update_data["fat_g"] = round(float(profile.get("fat_g", 0.0)) * target_qty, 1)
        update_data["fiber_g"] = round(float(profile.get("fiber_g", 0.0)) * target_qty, 1)
    elif dto.beverageName is not None:
        # Switched away from a supplement to a plain beverage: clear nutrition
        # so it no longer counts toward daily calorie/macro totals.
        update_data["quantity"] = None
        update_data["calories"] = 0.0
        update_data["protein_g"] = 0.0
        update_data["carbs_g"] = 0.0
        update_data["fat_g"] = 0.0
        update_data["fiber_g"] = 0.0
    elif dto.quantity is not None:
        update_data["quantity"] = dto.quantity

    if dto.loggedAt is not None:
        try:
            new_dt = datetime.fromisoformat(dto.loggedAt.replace("Z", "+00:00"))
        except Exception:
            local_now = TimeService.get_current_local_datetime()
            new_dt, has_t = TimeService.extract_time_from_text(dto.loggedAt, reference_time=local_now)
            if not has_t:
                new_dt = None
        if new_dt is not None:
            update_data["logged_at"] = new_dt
            update_data["log_date"] = new_dt.strftime("%Y-%m-%d")

    await db.hydration_logs.update_one(query, {"$set": update_data})
    updated = await db.hydration_logs.find_one(query)

    stable_log_id = updated.get("id") or str(id)
    await HydrationService.sync_hydration_log_to_conversation_messages(
        user_id=user_id,
        log_id=stable_log_id,
        updated_entry=updated,
        is_deleted=False,
    )

    log_date = updated.get("log_date") or TimeService.get_current_local_date_str()
    dashboard_data = await DashboardService.get_today_dashboard(user_id, log_date)

    dt = updated.get("logged_at") or updated.get("created_at") or datetime.now(timezone.utc)
    h_cal = float(updated.get("calories") or 0.0)
    entry_data = {
        "id": stable_log_id,
        "amountMl": updated.get("amount_ml", 0),
        "beverageName": updated.get("beverage_name") or updated.get("notes") or "Water",
        "loggedAt": dt.isoformat() if hasattr(dt, "isoformat") else str(dt),
        "timeFormatted": TimeService.format_time(dt) if hasattr(dt, "isoformat") else "",
        "notes": updated.get("notes"),
        "quantity": updated.get("quantity"),
        "calories": h_cal if h_cal > 0 else None,
        "proteinG": float(updated.get("protein_g") or 0.0) if h_cal > 0 else None,
        "carbsG": float(updated.get("carbs_g") or 0.0) if h_cal > 0 else None,
        "fatG": float(updated.get("fat_g") or 0.0) if h_cal > 0 else None,
        "fiberG": float(updated.get("fiber_g") or 0.0) if h_cal > 0 else None,
    }

    return {
        "success": True,
        "entry": entry_data,
        "dashboard": dashboard_data,
        "hydration": dashboard_data.get("hydration"),
        **entry_data,
    }

@router.delete("/{id}")
async def delete_hydration_log(
    id: str,
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    user_id = current_user.get("id") or str(current_user.get("_id"))
    query = _ownership_query(id, user_id)

    existing = await db.hydration_logs.find_one(query)
    if not existing:
        raise HTTPException(status_code=404, detail="Hydration log not found")

    target_log_id = existing.get("id") or str(existing.get("_id") or id)
    target_date = existing.get("log_date") or TimeService.get_current_local_date_str()

    res = await db.hydration_logs.delete_one(query)
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Hydration log not found")

    await HydrationService.sync_hydration_log_to_conversation_messages(
        user_id=user_id,
        log_id=target_log_id,
        is_deleted=True,
    )

    dashboard_data = await DashboardService.get_today_dashboard(user_id, target_date)

    return {
        "success": True,
        "deleted": True,
        "id": id,
        "dashboard": dashboard_data,
        "hydration": dashboard_data.get("hydration"),
    }
