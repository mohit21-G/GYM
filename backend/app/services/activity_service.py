import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from ..database import get_db

class ActivityService:
    @staticmethod
    def get_met_value(activity_name: str) -> float:
        lower = activity_name.lower()
        if "run" in lower:
            return 8.0
        if "walk" in lower:
            return 3.5
        if "cycling" in lower or "cycle" in lower:
            return 6.0
        if "swim" in lower:
            return 7.0
        if "gym" in lower or "weight" in lower or "workout" in lower:
            return 5.0
        if "yoga" in lower:
            return 3.0
        if "badminton" in lower:
            return 5.5
        return 4.0

    @staticmethod
    async def process_and_log_activity(
        user_id: str,
        activity_data: Dict[str, Any],
        log_date_str: Optional[str] = None,
    ) -> Dict[str, Any]:
        db = get_db()
        now = datetime.now(timezone.utc)
        target_date_str = log_date_str or now.strftime("%Y-%m-%d")

        name = activity_data.get("activity") or activity_data.get("name") or "Workout"
        duration = float(activity_data.get("durationMinutes") or activity_data.get("duration") or 30.0)
        
        # User weight lookup
        user = await db.users.find_one({"id": user_id}) or await db.users.find_one({"user_id": user_id}) or {}
        profile = user.get("profile") or {}
        weight_kg = float(profile.get("currentWeightKg") or 70.0)

        met = ActivityService.get_met_value(name)
        burned = round(met * weight_kg * (duration / 60.0), 1)

        log_id = str(uuid.uuid4())
        doc = {
            "id": log_id,
            "user_id": user_id,
            "exercise_name": name.title(),
            "duration_minutes": duration,
            "calories_burned": burned,
            "met_value": met,
            "intensity": activity_data.get("intensity", "MEDIUM"),
            "log_date": target_date_str,
            "created_at": now,
            "logged_at": now,
        }
        await db.daily_exercise_logs.insert_one(doc)
        doc.pop("_id", None)

        return {
            "success": True,
            "log": doc,
            "calculation": {
                "activityName": name.title(),
                "durationMinutes": duration,
                "caloriesBurned": burned,
                "metValue": met,
            },
            "replyText": f"Logged {int(duration)} mins {name.title()} ({int(burned)} kcal burned). Great job!",
        }
