from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from ..database import get_db

class DashboardService:
    @staticmethod
    async def get_today_dashboard(user_id: str, date_str: str) -> Dict[str, Any]:
        db = get_db()
        
        # User & profile targets
        user = await db.users.find_one({"id": user_id}) or await db.users.find_one({"user_id": user_id}) or {}
        profile = user.get("profile") or {}
        target_cal = float(profile.get("dailyCalorieTarget") or 2000.0)
        
        explicit_water_target = profile.get("dailyWaterMlTarget")
        has_water_target = bool(explicit_water_target is not None and float(explicit_water_target) > 0)
        target_water = float(explicit_water_target) if has_water_target else None

        target_sleep = float(profile.get("dailySleepMinutesTarget") or 480.0)

        # 1. Food logs
        cursor = db.daily_food_logs.find({"user_id": user_id, "log_date": date_str})
        food_logs = await cursor.to_list(length=200)

        cal_consumed_food = sum(float(l.get("calories", 0.0)) for l in food_logs)
        p_total_food = sum(float(l.get("protein_g", 0.0)) for l in food_logs)
        c_total_food = sum(float(l.get("carbs_g", 0.0)) for l in food_logs)
        f_total_food = sum(float(l.get("fat_g", 0.0)) for l in food_logs)
        fib_total_food = sum(float(l.get("fiber_g", 0.0)) for l in food_logs)

        # 2. Activity logs
        cursor = db.daily_exercise_logs.find({"user_id": user_id, "log_date": date_str})
        act_logs = await cursor.to_list(length=200)
        cal_burned = sum(float(l.get("calories_burned", 0.0)) for l in act_logs)

        # 3. Hydration logs
        cursor = db.hydration_logs.find({"user_id": user_id, "log_date": date_str})
        water_logs = await cursor.to_list(length=100)
        water_total = sum(float(l.get("amount_ml", 0.0)) for l in water_logs)
        # Supplement entries (Pre Workout / Whey Protein Powder mixed into
        # water) carry nutrition that must still count toward daily totals,
        # even though they live in hydration_logs rather than daily_food_logs.
        hyd_cal_total = sum(float(l.get("calories", 0.0)) for l in water_logs)
        hyd_p_total = sum(float(l.get("protein_g", 0.0)) for l in water_logs)
        hyd_c_total = sum(float(l.get("carbs_g", 0.0)) for l in water_logs)
        hyd_f_total = sum(float(l.get("fat_g", 0.0)) for l in water_logs)
        hyd_fib_total = sum(float(l.get("fiber_g", 0.0)) for l in water_logs)

        # 4. Sleep logs
        cursor = db.sleep_logs.find({"user_id": user_id, "log_date": date_str})
        sleep_logs = await cursor.to_list(length=50)
        sleep_total = sum(float(l.get("duration_minutes", 0.0)) for l in sleep_logs)
        sleep_quality = sleep_logs[-1].get("quality", "GOOD") if sleep_logs else "GOOD"

        # 5. Weight logs
        cursor = db.weight_logs.find({"user_id": user_id}).sort("created_at", -1).limit(2)
        weight_docs = await cursor.to_list(length=2)
        current_wt = weight_docs[0].get("weight_kg", profile.get("currentWeightKg", 70.0)) if weight_docs else profile.get("currentWeightKg", 70.0)
        delta_wt = (current_wt - weight_docs[1].get("weight_kg", current_wt)) if len(weight_docs) > 1 else 0.0

        # Combine food-log nutrition with supplement nutrition logged via
        # hydration entries (Pre Workout / Whey Protein Powder + water).
        cal_consumed = cal_consumed_food + hyd_cal_total
        p_total = p_total_food + hyd_p_total
        c_total = c_total_food + hyd_c_total
        f_total = f_total_food + hyd_f_total
        fib_total = fib_total_food + hyd_fib_total

        net_cal = round(cal_consumed - cal_burned)
        remaining_cal = max(0.0, target_cal - cal_consumed)

        return {
            "date": date_str,
            "calories": {
                "consumed": round(cal_consumed),
                "burned": round(cal_burned),
                "net": net_cal,
                "target": target_cal,
                "remaining": round(remaining_cal),
                "percentTarget": min(100, int((cal_consumed / target_cal) * 100)) if target_cal > 0 else 0,
            },
            "activity": {
                "caloriesBurned": round(cal_burned),
                "durationMinutes": round(sum(float(l.get("duration_minutes", 0.0)) for l in act_logs)),
                "exercisesCount": len(act_logs),
            },
            "macros": {
                "proteinG": round(p_total, 1),
                "carbsG": round(c_total, 1),
                "fatG": round(f_total, 1),
                "fiberG": round(fib_total, 1),
            },
            "hydration": {
                "amountMl": round(water_total),
                "consumedMl": round(water_total),
                "targetMl": round(target_water) if target_water else None,
                "hasTarget": has_water_target,
                "percent": min(100, int((water_total / target_water) * 100)) if (target_water and target_water > 0) else None,
                "percentTarget": min(100, int((water_total / target_water) * 100)) if (target_water and target_water > 0) else None,
                "remainingMl": max(0, round(target_water - water_total)) if target_water else None,
                "targetMet": (water_total >= target_water) if target_water else False,
            },
            "sleep": {
                "totalMinutes": round(sleep_total),
                "targetMinutes": target_sleep,
                "quality": sleep_quality,
            },
            "weight": {
                "currentKg": current_wt,
                "targetKg": profile.get("targetWeightKg"),
                "deltaKg": round(delta_wt, 1),
                "trend": "DOWN" if delta_wt < 0 else "UP" if delta_wt > 0 else "STABLE",
            },
            "recentLogs": [
                *[{
                    "id": str(l.get("id") or l.get("_id")),
                    "type": "FOOD",
                    "title": l.get("food_name"),
                    "subtitle": f"{l.get('quantity_amount')} {l.get('quantity_unit')}",
                    "metric": f"{int(l.get('calories', 0))} kcal",
                    "loggedAt": l.get("created_at").isoformat() if hasattr(l.get("created_at"), "isoformat") else str(l.get("created_at")),
                } for l in food_logs[-5:]],
                *[{
                    "id": str(l.get("id") or l.get("_id")),
                    "type": "ACTIVITY",
                    "title": l.get("exercise_name"),
                    "subtitle": f"{int(l.get('duration_minutes', 0))} mins",
                    "metric": f"{int(l.get('calories_burned', 0))} kcal",
                    "loggedAt": l.get("created_at").isoformat() if hasattr(l.get("created_at"), "isoformat") else str(l.get("created_at")),
                } for l in act_logs[-5:]],
            ]
        }

    @staticmethod
    async def get_trend_history(user_id: str, days: int = 7) -> Dict[str, Any]:
        db = get_db()
        now = datetime.now(timezone.utc)
        history = []

        for i in range(days - 1, -1, -1):
            d = (now - timedelta(days=i)).strftime("%Y-%m-%d")
            food_cursor = db.daily_food_logs.find({"user_id": user_id, "log_date": d})
            foods = await food_cursor.to_list(length=100)
            cal_in = sum(float(l.get("calories", 0.0)) for l in foods)

            act_cursor = db.daily_exercise_logs.find({"user_id": user_id, "log_date": d})
            acts = await act_cursor.to_list(length=100)
            cal_out = sum(float(l.get("calories_burned", 0.0)) for l in acts)

            water_cursor = db.hydration_logs.find({"user_id": user_id, "log_date": d})
            waters = await water_cursor.to_list(length=50)
            water_ml = sum(float(l.get("amount_ml", 0.0)) for l in waters)

            history.append({
                "date": d,
                "caloriesConsumed": round(cal_in),
                "caloriesBurned": round(cal_out),
                "waterMl": round(water_ml),
            })

        return {"days": days, "history": history}
