import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from ..database import get_db
from ..schemas.activity_log import CreateWeightLogDto
from ..services.auth_service import get_current_user

router = APIRouter(prefix="/weight-logs", tags=["Weight Logs"])

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_weight_log(
    dto: CreateWeightLogDto,
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    user_id = current_user.get("id") or str(current_user.get("_id"))
    now = datetime.now(timezone.utc)
    target_date = dto.loggedAt.split("T")[0] if dto.loggedAt else now.strftime("%Y-%m-%d")

    log_id = str(uuid.uuid4())
    doc = {
        "id": log_id,
        "user_id": user_id,
        "weight_kg": dto.weightKg,
        "notes": dto.notes,
        "source": dto.source or "MANUAL",
        "log_date": target_date,
        "created_at": now,
        "logged_at": now,
    }
    await db.weight_logs.insert_one(doc)
    await db.users.update_one({"id": user_id}, {"$set": {"profile.currentWeightKg": dto.weightKg}})
    doc.pop("_id", None)
    return doc

@router.get("")
async def list_weight_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(15, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    user_id = current_user.get("id") or str(current_user.get("_id"))
    skip = (page - 1) * limit
    total = await db.weight_logs.count_documents({"user_id": user_id})
    cursor = db.weight_logs.find({"user_id": user_id}).sort("created_at", -1).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)

    items = []
    for d in docs:
        dt = d.get("logged_at") or d.get("created_at") or datetime.now(timezone.utc)
        items.append({
            "id": d.get("id") or str(d.get("_id")),
            "weightKg": d.get("weight_kg"),
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
