import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from ..database import get_db
from ..schemas.activity_log import CreateHydrationLogDto
from ..services.auth_service import get_current_user

router = APIRouter(prefix="/hydration-logs", tags=["Hydration Logs"])

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
        items.append({
            "id": d.get("id") or str(d.get("_id")),
            "amountMl": d.get("amount_ml", 0),
            "beverageName": d.get("beverage_name") or d.get("notes") or "Water",
            "loggedAt": dt.isoformat() if hasattr(dt, "isoformat") else str(dt),
            "source": d.get("source", "MANUAL"),
            "notes": d.get("notes"),
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
    doc = await db.hydration_logs.find_one({"id": id, "user_id": user_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Hydration log not found")
    dt = doc.get("logged_at") or doc.get("created_at")
    return {
        "id": doc.get("id") or str(doc.get("_id")),
        "amountMl": doc.get("amount_ml", 0),
        "loggedAt": dt.isoformat() if hasattr(dt, "isoformat") else str(dt),
        "source": doc.get("source", "MANUAL"),
        "notes": doc.get("notes"),
    }

@router.delete("/{id}")
async def delete_hydration_log(
    id: str,
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    user_id = current_user.get("id") or str(current_user.get("_id"))
    res = await db.hydration_logs.delete_one({"id": id, "user_id": user_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Hydration log not found")
    return {"deleted": True, "id": id}
