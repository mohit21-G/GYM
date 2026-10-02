import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from ..database import get_db
from ..schemas.activity_log import CreateActivityLogDto, UpdateActivityLogDto
from ..services.auth_service import get_current_user
from ..services.activity_service import ActivityService
from ..services.dashboard_service import DashboardService
from ..services.time_service import TimeService

router = APIRouter(prefix="/activity-logs", tags=["Activity Logs"])


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

@router.get("/{id}")
async def get_single_activity_log(
    id: str,
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    user_id = current_user.get("id") or str(current_user.get("_id"))
    doc = await db.daily_exercise_logs.find_one(_ownership_query(id, user_id))
    if not doc:
        raise HTTPException(status_code=404, detail="Activity log not found")
    doc.pop("_id", None)
    return doc

@router.patch("/{id}")
async def update_activity_log(
    id: str,
    dto: UpdateActivityLogDto,
    current_user: dict = Depends(get_current_user),
):
    """Edit an existing workout/activity log (exercise name, duration, reps,
    sets, or intensity). Recalculates calories burned from the MET formula,
    the same way PATCH /food-logs/{id} recalculates nutrition."""
    db = get_db()
    user_id = current_user.get("id") or str(current_user.get("_id"))
    query = _ownership_query(id, user_id)

    existing = await db.daily_exercise_logs.find_one(query)
    if not existing:
        raise HTTPException(status_code=404, detail="Activity log not found")

    target_name = dto.activity if dto.activity is not None else existing.get("exercise_name", "Workout")
    target_duration = dto.durationMinutes if dto.durationMinutes is not None else existing.get("duration_minutes", 30.0)
    target_reps = dto.reps if dto.reps is not None else existing.get("reps")
    target_sets = dto.sets if dto.sets is not None else existing.get("sets")
    target_intensity = dto.intensity if dto.intensity is not None else existing.get("intensity", "MEDIUM")

    # Recalculate duration from reps/sets if reps were edited but duration wasn't
    if dto.reps is not None and dto.durationMinutes is None and target_reps:
        target_duration = max(1.0, round(float(target_reps) * (target_sets or 1) * 0.08, 1))

    display_name = ActivityService.format_exercise_name(target_name)
    met = ActivityService.get_met_value(target_name)

    weight_kg = 70.0
    user = await db.users.find_one({"id": user_id}) or {}
    profile = user.get("profile") or {}
    weight_kg = float(profile.get("currentWeightKg") or 70.0)

    recalculated_burned = round(met * weight_kg * (float(target_duration) / 60.0), 1)

    update_data: Dict[str, Any] = {
        "exercise_name": display_name,
        "duration_minutes": float(target_duration),
        "reps": target_reps,
        "sets": target_sets if target_reps else None,
        "calories_burned": recalculated_burned,
        "met_value": met,
        "intensity": target_intensity,
        "updated_at": datetime.now(timezone.utc),
    }

    if dto.loggedAt is not None:
        try:
            new_dt = datetime.fromisoformat(dto.loggedAt.replace("Z", "+00:00"))
        except Exception:
            local_now = TimeService.get_current_local_datetime()
            new_dt, has_t = TimeService.extract_time_from_text(dto.loggedAt, reference_time=local_now)
            if not has_t:
                new_dt = None
        if new_dt is not None:
            update_data["logged_at"] = new_dt.isoformat()
            update_data["log_date"] = new_dt.strftime("%Y-%m-%d")

    if dto.notes is not None:
        update_data["notes"] = dto.notes

    await db.daily_exercise_logs.update_one(query, {"$set": update_data})
    updated = await db.daily_exercise_logs.find_one(query)

    stable_log_id = updated.get("id") or str(id)
    await ActivityService.sync_activity_log_to_conversation_messages(
        user_id=user_id,
        log_id=stable_log_id,
        updated_entry=updated,
        is_deleted=False,
    )

    log_date = updated.get("log_date") or TimeService.get_current_local_date_str()
    dashboard_data = await DashboardService.get_today_dashboard(user_id, log_date)

    dt = updated.get("logged_at") or updated.get("created_at") or datetime.now(timezone.utc)
    time_formatted = TimeService.format_time(dt) if hasattr(dt, "isoformat") else (
        TimeService.format_time(datetime.fromisoformat(str(dt).replace("Z", "+00:00"))) if isinstance(dt, str) else ""
    )

    entry_data = {
        "id": stable_log_id,
        "activity": updated.get("exercise_name"),
        "activityName": updated.get("exercise_name"),
        "durationMinutes": updated.get("duration_minutes"),
        "reps": updated.get("reps"),
        "sets": updated.get("sets"),
        "caloriesBurned": updated.get("calories_burned"),
        "metValue": updated.get("met_value"),
        "intensity": updated.get("intensity"),
        "loggedAt": dt if isinstance(dt, str) else (dt.isoformat() if hasattr(dt, "isoformat") else str(dt)),
        "timeFormatted": time_formatted,
    }

    return {
        "success": True,
        "entry": entry_data,
        "dashboard": dashboard_data,
        **entry_data,
    }

@router.delete("/{id}")
async def delete_activity_log(
    id: str,
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    user_id = current_user.get("id") or str(current_user.get("_id"))
    query = _ownership_query(id, user_id)

    existing = await db.daily_exercise_logs.find_one(query)
    if not existing:
        raise HTTPException(status_code=404, detail="Activity log not found")

    target_log_id = existing.get("id") or str(existing.get("_id") or id)
    target_date = existing.get("log_date") or TimeService.get_current_local_date_str()

    res = await db.daily_exercise_logs.delete_one(query)
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Activity log not found")

    await ActivityService.sync_activity_log_to_conversation_messages(
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
    }
