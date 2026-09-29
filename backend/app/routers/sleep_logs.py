import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from ..database import get_db
from ..schemas.activity_log import CreateSleepLogDto
from ..services.auth_service import get_current_user

router = APIRouter(prefix="/sleep-logs", tags=["Sleep Logs"])

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_sleep_log(
    dto: CreateSleepLogDto,
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    user_id = current_user.get("id") or str(current_user.get("_id"))
    now = datetime.now(timezone.utc)
    log_id = str(uuid.uuid4())

    duration = dto.durationMinutes or dto.duration or 480
    date_str = dto.startDate or now.strftime("%Y-%m-%d")

    doc = {
        "id": log_id,
        "user_id": user_id,
        "duration_minutes": duration,
        "quality": dto.quality or "GOOD",
        "log_date": date_str,
        "start_time": dto.startTime or now.isoformat(),
        "end_time": dto.endTime or now.isoformat(),
        "source": dto.source or "MANUAL",
        "notes": dto.notes,
        "created_at": now,
        "updated_at": now,
    }

    await db.sleep_logs.insert_one(doc)

    return {
        "id": log_id,
        "userId": user_id,
        "durationMinutes": duration,
        "quality": doc["quality"],
        "startTime": doc["start_time"],
        "endTime": doc["end_time"],
        "source": doc["source"],
        "notes": doc["notes"],
        "createdAt": now.isoformat(),
        "updatedAt": now.isoformat(),
    }

@router.get("")
async def list_sleep_logs(
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
    total = await db.sleep_logs.count_documents(query)
    cursor = db.sleep_logs.find(query).sort("created_at", -1).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)

    items = []
    for d in docs:
        dt = d.get("created_at") or datetime.now(timezone.utc)
        items.append({
            "id": d.get("id") or str(d.get("_id")),
            "durationMinutes": d.get("duration_minutes", 480),
            "quality": d.get("quality", "GOOD"),
            "startTime": d.get("start_time"),
            "endTime": d.get("end_time"),
            "source": d.get("source", "MANUAL"),
            "notes": d.get("notes"),
            "createdAt": dt.isoformat() if hasattr(dt, "isoformat") else str(dt),
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "totalPages": (total + limit - 1) // limit if limit > 0 else 1,
    }

@router.get("/{id}")
async def get_sleep_log(
    id: str,
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    user_id = current_user.get("id") or str(current_user.get("_id"))
    doc = await db.sleep_logs.find_one({"id": id, "user_id": user_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Sleep log not found")
    return {
        "id": doc.get("id") or str(doc.get("_id")),
        "durationMinutes": doc.get("duration_minutes", 480),
        "quality": doc.get("quality", "GOOD"),
        "startTime": doc.get("start_time"),
        "endTime": doc.get("end_time"),
        "source": doc.get("source", "MANUAL"),
        "notes": doc.get("notes"),
    }

@router.delete("/{id}")
async def delete_sleep_log(
    id: str,
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    user_id = current_user.get("id") or str(current_user.get("_id"))
    res = await db.sleep_logs.delete_one({"id": id, "user_id": user_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Sleep log not found")
    return {"deleted": True, "id": id}
