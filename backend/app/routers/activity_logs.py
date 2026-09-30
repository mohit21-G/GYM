import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from ..database import get_db
from ..schemas.activity_log import CreateActivityLogDto
from ..services.auth_service import get_current_user
from ..services.activity_service import ActivityService

router = APIRouter(prefix="/activity-logs", tags=["Activity Logs"])

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_activity_log(
    dto: CreateActivityLogDto,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user.get("id") or str(current_user.get("_id"))
    data = {
        "activity": dto.activity or dto.activityName or "Workout",
        "durationMinutes": dto.durationMinutes or dto.duration or 30.0,
        "intensity": dto.intensity or "MEDIUM",
        "distanceKm": dto.distanceKm,
    }
    date_str = dto.loggedAt.split("T")[0] if dto.loggedAt else TimeService.get_current_local_date_str()
    res = await ActivityService.process_and_log_activity(user_id, data, date_str)
    return res["log"]

@router.get("")
async def list_activity_logs(
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
    total = await db.daily_exercise_logs.count_documents(query)
    cursor = db.daily_exercise_logs.find(query).sort("created_at", -1).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)

    items = []
    for d in docs:
        dt = d.get("logged_at") or d.get("created_at") or datetime.now(timezone.utc)
        items.append({
            "id": d.get("id") or str(d.get("_id")),
            "name": d.get("exercise_name"),
            "activityName": d.get("exercise_name"),
            "durationMinutes": d.get("duration_minutes", 30),
            "caloriesBurned": d.get("calories_burned", 0),
            "intensity": d.get("intensity", "MEDIUM"),
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

@router.delete("/{id}")
async def delete_activity_log(
    id: str,
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    user_id = current_user.get("id") or str(current_user.get("_id"))
    res = await db.daily_exercise_logs.delete_one({"id": id, "user_id": user_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Activity log not found")
    return {"deleted": True, "id": id}
