import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from ..database import get_db
from .time_service import TimeService

class ActivityService:
    @staticmethod
    def get_met_value(activity_name: str) -> float:
        lower = activity_name.lower()
        if "strength" in lower or "weight" in lower or "lift" in lower:
            return 5.5
        if "squat" in lower:
            return 5.0
        if "pushup" in lower or "push-up" in lower or "push up" in lower:
            return 4.5
        if "pullup" in lower or "pull-up" in lower or "pull up" in lower:
            return 5.0
        if "lunge" in lower:
            return 4.5
        if "crunch" in lower or "situp" in lower:
            return 3.8
        if "plank" in lower:
            return 3.5
        if "burpee" in lower:
            return 8.0
        if "jumping jack" in lower:
            return 8.0
        if "jump rope" in lower or "skipping" in lower:
            return 10.0
        if "bench press" in lower:
            return 5.5
        if "deadlift" in lower:
            return 6.0
        if "run" in lower:
            return 8.5
        if "walk" in lower:
            return 3.5
        if "cycling" in lower or "cycle" in lower:
            return 6.0
        if "swim" in lower:
            return 7.0
        if "gym" in lower or "workout" in lower or "exercise" in lower or "kasrat" in lower:
            return 5.0
        if "yoga" in lower:
            return 3.0
        if "badminton" in lower:
            return 5.5
        if "cricket" in lower:
            return 5.0
        return 4.5

    @staticmethod
    def format_exercise_name(name: str) -> str:
        n = name.strip()
        lower = n.lower()
        if lower in ["push-ups", "pushups", "push up", "push-up", "push ups"]:
            return "Push-ups"
        if lower in ["pull-ups", "pullups", "pull up", "pull-up", "pull ups"]:
            return "Pull-ups"
        if lower in ["sit-ups", "situps", "sit up", "sit-up"]:
            return "Sit-ups"
        if lower in ["strength training", "strength-training", "strength"]:
            return "Strength Training"
        return n.title()

    @staticmethod
    async def process_and_log_activity(
        user_id: str,
        activity_data: Dict[str, Any],
        log_date_str: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Backward-compatible single activity logger."""
        res = await ActivityService.process_and_log_activities(user_id, [activity_data], log_date_str)
        single_log = res["logs"][0] if res.get("logs") else {}
        single_calc = res["calculations"][0] if res.get("calculations") else {}
        return {
            "success": res.get("success", True),
            "log": single_log,
            "calculation": single_calc,
            "replyText": res.get("replyText", ""),
            "cards": res.get("cards", []),
        }

    @staticmethod
    async def process_and_log_activities(
        user_id: str,
        activities_list: List[Dict[str, Any]],
        log_date_str: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Processes and logs single or multiple activities into daily_exercise_logs.
        Returns markdown bullet-point formatted summary with separate lines.
        """
        db = get_db()
        local_now = TimeService.get_current_local_time()
        now = datetime.now(timezone.utc)
        target_date_str = log_date_str or local_now.strftime("%Y-%m-%d")

        # User weight lookup
        weight_kg = 70.0
        if db is not None:
            try:
                user = await db.users.find_one({"id": user_id}) or await db.users.find_one({"user_id": user_id}) or {}
                profile = user.get("profile") or {}
                weight_kg = float(profile.get("currentWeightKg") or 70.0)
            except Exception:
                weight_kg = 70.0

        inserted_docs = []
        calculations = []
        bullet_lines = []
        cards = []
        total_burned = 0.0

        for act in activities_list:
            raw_name = act.get("activity") or act.get("name") or "Workout"
            display_name = ActivityService.format_exercise_name(raw_name)
            reps = act.get("reps")
            sets = act.get("sets") or 1
            duration = act.get("durationMinutes") or act.get("duration")

            # Duration calculation
            if duration is not None:
                duration_val = float(duration)
            elif reps is not None:
                duration_val = max(1.0, round(float(reps) * sets * 0.08, 1))
            else:
                duration_val = 30.0

            met = act.get("metValue") or ActivityService.get_met_value(raw_name)
            burned = round(met * weight_kg * (duration_val / 60.0), 1)
            total_burned += burned

            # Timestamp resolution
            act_time_input = act.get("logged_at") or act.get("time") or act.get("raw_text")
            if act_time_input:
                if isinstance(act_time_input, datetime):
                    act_logged_at = act_time_input
                else:
                    try:
                        act_logged_at = datetime.fromisoformat(str(act_time_input).replace("Z", "+00:00"))
                    except Exception:
                        act_logged_at, _ = TimeService.extract_time_from_text(str(act_time_input), reference_time=local_now)
            else:
                act_logged_at = local_now

            time_formatted = TimeService.format_time(act_logged_at)

            # Format bullet point text
            if reps is not None and int(reps) > 0:
                if sets and int(sets) > 1:
                    metric_str = f"{sets} sets × {int(reps)} reps"
                else:
                    metric_str = f"{int(reps)} reps"
            else:
                metric_str = f"{int(duration_val)} minutes"

            bullet_lines.append(f"* {display_name} — {metric_str}")

            log_id = str(uuid.uuid4())
            act_date_str = act_logged_at.strftime("%Y-%m-%d") if hasattr(act_logged_at, "strftime") else target_date_str
            act_iso = act_logged_at.isoformat() if hasattr(act_logged_at, "isoformat") else str(act_logged_at)
            doc = {
                "id": log_id,
                "user_id": user_id,
                "exercise_name": display_name,
                "duration_minutes": duration_val,
                "reps": reps,
                "sets": sets if reps else None,
                "calories_burned": burned,
                "met_value": met,
                "intensity": act.get("intensity", "MEDIUM"),
                "log_date": act_date_str,
                "created_at": now,
                "logged_at": act_iso,
            }

            if db is not None:
                await db.daily_exercise_logs.insert_one(doc)
            doc_copy = dict(doc)
            doc_copy.pop("_id", None)
            if hasattr(doc_copy.get("created_at"), "isoformat"):
                doc_copy["created_at"] = doc_copy["created_at"].isoformat()
            if hasattr(doc_copy.get("logged_at"), "isoformat"):
                doc_copy["logged_at"] = doc_copy["logged_at"].isoformat()

            inserted_docs.append(doc_copy)
            calc_data = {
                "activityName": display_name,
                "durationMinutes": duration_val,
                "reps": reps,
                "sets": sets,
                "caloriesBurned": burned,
                "metValue": met,
                "loggedAt": doc_copy["logged_at"],
                "timeFormatted": time_formatted,
            }
            calculations.append(calc_data)

            cards.append({
                "id": log_id,
                "type": "ACTIVITY",
                "title": display_name,
                "subtitle": f"{metric_str} · MET {met}",
                "metric": f"{int(burned)} kcal burned",
                "durationMinutes": duration_val,
                "reps": reps,
                "sets": sets if reps else None,
                "caloriesBurned": burned,
                "metValue": met,
                "intensity": act.get("intensity", "MEDIUM"),
                "loggedAt": act_iso,
                "timeFormatted": time_formatted,
            })

        bullets_text = "\n".join(bullet_lines)
        total_burned_int = int(round(total_burned))
        
        if len(activities_list) > 1:
            reply_text = (
                f"🏋️ **Workout Logged**\n\n"
                f"{bullets_text}\n\n"
                f"Total workout: {total_burned_int} kcal burned across {len(activities_list)} exercises. Great job!"
            )
        else:
            reply_text = (
                f"🏋️ **Workout Logged**\n\n"
                f"{bullets_text}\n\n"
                f"Total workout: {total_burned_int} kcal burned. Great job!"
            )

        return {
            "success": True,
            "logs": inserted_docs,
            "calculations": calculations,
            "totalCaloriesBurned": total_burned_int,
            "cards": cards,
            "replyText": reply_text,
        }

    @staticmethod
    async def sync_activity_log_to_conversation_messages(
        user_id: str,
        log_id: str,
        updated_entry: Optional[Dict[str, Any]] = None,
        is_deleted: bool = False,
    ) -> None:
        """Update or remove an activity card inside any persisted chat message
        that embedded it, so session reload reflects the current DB state.

        Activity cards are embedded either as a single dict (data.type ==
        "ACTIVITY") or inside a list at raw_ent["cards"] (multi-log shape).
        """
        db = get_db()
        cursor = db.conversation_messages.find({"raw_entities": {"$ne": None}})
        messages = await cursor.to_list(length=500)

        for m in messages:
            raw_ent = m.get("raw_entities")
            if not isinstance(raw_ent, dict):
                continue

            modified = False

            def _rebuild_card(card: Dict[str, Any]) -> Optional[Dict[str, Any]]:
                nonlocal modified
                if str(card.get("id") or "") != str(log_id):
                    return card
                modified = True
                if is_deleted:
                    return None
                if not updated_entry:
                    return card
                duration_val = updated_entry.get("duration_minutes", card.get("durationMinutes"))
                reps = updated_entry.get("reps", card.get("reps"))
                sets = updated_entry.get("sets", card.get("sets"))
                burned = updated_entry.get("calories_burned", card.get("caloriesBurned"))
                met = updated_entry.get("met_value", card.get("metValue"))
                name = updated_entry.get("exercise_name", card.get("title"))
                if reps:
                    metric_str = f"{sets} sets × {int(reps)} reps" if sets and int(sets) > 1 else f"{int(reps)} reps"
                else:
                    metric_str = f"{int(duration_val or 0)} minutes"
                return {
                    **card,
                    "title": name,
                    "subtitle": f"{metric_str} · MET {met}",
                    "metric": f"{int(burned or 0)} kcal burned",
                    "durationMinutes": duration_val,
                    "reps": reps,
                    "sets": sets,
                    "caloriesBurned": burned,
                    "metValue": met,
                }

            cards = raw_ent.get("cards")
            if isinstance(cards, list):
                new_cards = []
                for card in cards:
                    if not isinstance(card, dict) or card.get("type") != "ACTIVITY":
                        new_cards.append(card)
                        continue
                    rebuilt = _rebuild_card(card)
                    if rebuilt is not None:
                        new_cards.append(rebuilt)
                if modified:
                    raw_ent["cards"] = new_cards

            if isinstance(raw_ent.get("data"), dict) and raw_ent["data"].get("type") == "ACTIVITY":
                rebuilt = _rebuild_card(raw_ent["data"])
                if rebuilt is not None:
                    raw_ent["data"] = rebuilt

            if modified:
                await db.conversation_messages.update_one(
                    {"id": m["id"]},
                    {"$set": {"raw_entities": raw_ent}},
                )
