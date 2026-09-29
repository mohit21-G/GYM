import re
import uuid
import difflib
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from ..database import get_db
from .agent_nlp import AgentNLP, INDIAN_FOOD_SYNONYMS
from ..schemas.food_log import (
    FoodItemInput,
    GroupedFoodCard,
    FoodLogEntrySummary,
    DailyNutritionSummaryData,
    FoodLoggingResult,
)

class FoodTermsCache:
    terms: List[str] = []
    term_to_food_id: Dict[str, str] = {}
    is_loaded: bool = False

class FoodService:
    @staticmethod
    def resolve_food_icon(food_name: str, category: Optional[str] = None) -> str:
        lower = food_name.lower()
        if any(w in lower for w in ["roti", "rotli", "rotlo", "thepla", "bhakhri", "bread", "paratha", "wheat", "rice", "oats"]):
            return "wheat"
        if any(w in lower for w in ["milk", "doodh", "curd", "dahi", "paneer", "yogurt", "cheese", "chaas", "buttermilk"]):
            return "milk"
        if any(w in lower for w in ["banana", "kela", "apple", "safarjan", "fruit", "mango", "orange", "papaya"]):
            return "apple"
        if any(w in lower for w in ["egg", "anda", "chicken", "meat", "fish", "whey", "protein"]):
            return "egg"
        if any(w in lower for w in ["dal", "khichdi", "chana", "sprout", "moong", "rajma", "chole"]):
            return "bean"
        if any(w in lower for w in ["sabzi", "shaak", "shak", "salad", "vegetable", "bhindi", "palak", "aloo"]):
            return "carrot"
        if any(w in lower for w in ["khakhra", "snack", "nuts", "cookie", "biscuit", "farsan", "samosa", "dhokla"]):
            return "cookie"
        if any(w in lower for w in ["water", "pani", "juice", "tea", "chai", "coffee"]):
            return "cup-soda"
        return "utensils"

    @staticmethod
    def format_time(dt: datetime) -> str:
        try:
            return dt.strftime("%I:%M %p").lstrip("0")
        except Exception:
            return "12:00 PM"

    @staticmethod
    async def _ensure_terms_cache():
        if FoodTermsCache.is_loaded and FoodTermsCache.terms:
            return
        db = get_db()
        try:
            food_cursor = db.foods.find({}, {"food_id": 1, "food_name": 1, "food_name_display": 1}).limit(3000)
            food_docs = await food_cursor.to_list(length=3000)
            
            alias_cursor = db.food_aliases.find({}, {"food_id": 1, "alias": 1}).limit(4000)
            alias_docs = await alias_cursor.to_list(length=4000)

            terms_map = {}
            for f in food_docs:
                fid = f.get("food_id") or str(f.get("_id"))
                if f.get("food_name"):
                    terms_map[f["food_name"].lower().strip()] = fid
                if f.get("food_name_display"):
                    terms_map[f["food_name_display"].lower().strip()] = fid

            for a in alias_docs:
                if a.get("alias") and a.get("food_id"):
                    terms_map[a["alias"].lower().strip()] = a["food_id"]

            FoodTermsCache.terms = list(terms_map.keys())
            FoodTermsCache.term_to_food_id = terms_map
            FoodTermsCache.is_loaded = True
        except Exception:
            pass

    @staticmethod
    async def resolve_food(food_query: str) -> Dict[str, Any]:
        db = get_db()
        q = food_query.lower().strip()
        # Clean verbal baggage, time markers, postpositions and leading quantities
        clean_q = re.sub(
            r"\b(?:morning|afternoon|evening|night|breakfast|lunch|dinner|snack|savare|bapore|sanju|saanje|raate|subah|dopahar|shaam|sham|raat)\b"
            r"|\b(?:ma|maa|me|mein|ko|ne|nu|na|ni|no|thi|par|pe|se)\b"
            r"|\b(?:i|my|mine|me|maine|hamne|aaj|aaje|today)\b"
            r"|\b(?:and|ane|aur|with|sathe|sath|along with)\b"
            r"|\b(?:ate|had|eaten|have|drank|drink|drinking|khadha|khadhi|khadhu|khaye|khaya|khayi|khalo|pidhi|pidhu|pidha|piya|piyi|peeli|peena|lidhi|lidhu|lidho|leedhi|leedhu|liya|li)\b"
            r"|\b(?:che|tha|thi|the|hata|hati|chho|chhe)\b"
            r"|(?:મેં|ખાધી|ખાધું|ખાધા|લીધી|લીધું|પીધું|પીધી|છે|હતી|હતો|આજે|બપોરે|સવારે|રાત્રે|સાથે|નાસ્તો|વાળુ)"
            r"|(?:मैंने|खाया|खाई|खाए|पिया|पी|लिया|ली|है|था|थी|आज|सुबह|दोपहर|रात|साथ|नाश्ता)",
            " ",
            q,
            flags=re.I
        ).strip()
        clean_q = re.sub(r"^\d+(\.\d+)?\s*", "", clean_q).strip()
        clean_q = re.sub(r"\b(?:pieces?|piece|plate|cup|bowl|katori|vatki|glass|serving|slice|g|ml|kg)\b", "", clean_q, flags=re.I).strip()
        clean_q = re.sub(r"[^\w\s\u0A80-\u0AFF\u0900-\u097F]", " ", clean_q).strip()
        clean_q = re.sub(r"\s+", " ", clean_q)
        if not clean_q:
            clean_q = q

        # Step 1: Check known Indian dialect synonyms & slang map
        synonym_target = INDIAN_FOOD_SYNONYMS.get(clean_q) or INDIAN_FOOD_SYNONYMS.get(q)
        if not synonym_target:
            tokens = clean_q.split()
            for t in tokens:
                if t in INDIAN_FOOD_SYNONYMS:
                    synonym_target = INDIAN_FOOD_SYNONYMS[t]
                    break
        if not synonym_target:
            for food_key in sorted(INDIAN_FOOD_SYNONYMS.keys(), key=len, reverse=True):
                if len(food_key) >= 3 and food_key in clean_q:
                    synonym_target = INDIAN_FOOD_SYNONYMS[food_key]
                    break

        search_term = synonym_target.lower() if synonym_target else clean_q

        escaped_term = re.escape(search_term)
        escaped_clean = re.escape(clean_q)

        # Step 2: Exact database match on food_name or food_name_display
        doc = await db.foods.find_one({"food_name": search_term})
        if not doc:
            doc = await db.foods.find_one({"food_name": clean_q})
        if not doc:
            doc = await db.foods.find_one({"food_name_display": {"$regex": f"^{escaped_term}$", "$options": "i"}})
        if not doc:
            doc = await db.foods.find_one({"food_name_display": {"$regex": f"^{escaped_clean}$", "$options": "i"}})

        # Step 3: Check food_aliases collection
        if not doc:
            alias_doc = await db.food_aliases.find_one({"alias": clean_q})
            if not alias_doc and clean_q != search_term:
                alias_doc = await db.food_aliases.find_one({"alias": search_term})
            if alias_doc and "food_id" in alias_doc:
                doc = await db.foods.find_one({"food_id": alias_doc["food_id"]})

        # Step 4: Substring / regex search
        if not doc and len(clean_q) >= 3:
            doc = await db.foods.find_one({"food_name": {"$regex": escaped_clean, "$options": "i"}})
        if not doc and len(clean_q) >= 3:
            doc = await db.foods.find_one({"food_name_display": {"$regex": escaped_clean, "$options": "i"}})

        # Step 5: High-speed in-memory Fuzzy Search (Levenshtein / difflib with strict 0.72 cutoff)
        if not doc:
            await FoodService._ensure_terms_cache()
            if FoodTermsCache.terms:
                matches = difflib.get_close_matches(search_term, FoodTermsCache.terms, n=1, cutoff=0.72)
                if not matches and q != search_term:
                    matches = difflib.get_close_matches(clean_q, FoodTermsCache.terms, n=1, cutoff=0.72)
                
                if matches:
                    best_match = matches[0]
                    fid = FoodTermsCache.term_to_food_id.get(best_match)
                    if fid:
                        doc = await db.foods.find_one({"food_id": fid})

        # Step 6: Smart Heuristic Nutrition Profiling for Unmatched/Exotic Foods
        if not doc:
            # Bhakri
            if any(w in search_term for w in ["bhakri", "bhakhri"]):
                return {
                    "food_id": "smart_bhakri",
                    "food_name": "Whole Wheat Bhakri",
                    "calories": 130.0,
                    "protein_g": 3.8,
                    "carbs_g": 24.0,
                    "fat_g": 2.2,
                    "fiber_g": 3.0,
                    "unit": "piece",
                }
            # Chai / Tea / Coffee
            if any(w in search_term for w in ["chai", "chay", "tea", "coffee"]):
                return {
                    "food_id": "smart_chai",
                    "food_name": "Tea With Milk",
                    "calories": 65.0,
                    "protein_g": 2.0,
                    "carbs_g": 9.0,
                    "fat_g": 2.5,
                    "fiber_g": 0.0,
                    "unit": "cup",
                }
            # Roti / Breads
            if any(w in search_term for w in ["roti", "rotli", "rotlo", "chapati", "khapli", "phulka"]):
                return {
                    "food_id": "smart_khapli_roti",
                    "food_name": "Khapli Wheat Rotli",
                    "calories": 85.0,
                    "protein_g": 3.5,
                    "carbs_g": 16.5,
                    "fat_g": 0.8,
                    "fiber_g": 3.2,
                    "unit": "piece",
                }
            # Bananas / Fruits
            if any(w in search_term for w in ["banana", "kela", "keda", "kelu"]):
                return {
                    "food_id": "smart_banana",
                    "food_name": "Banana",
                    "calories": 105.0,
                    "protein_g": 1.3,
                    "carbs_g": 27.0,
                    "fat_g": 0.3,
                    "fiber_g": 3.1,
                    "unit": "piece",
                }
            # Milk / Dairy
            if any(w in search_term for w in ["milk", "doodh", "dudh"]):
                return {
                    "food_id": "smart_milk",
                    "food_name": "Cow Milk (Toned)",
                    "calories": 145.0,
                    "protein_g": 8.0,
                    "carbs_g": 12.0,
                    "fat_g": 7.5,
                    "fiber_g": 0.0,
                    "unit": "cup",
                }
            # Buttermilk / Chaas
            if any(w in search_term for w in ["chaas", "chhas", "chach", "buttermilk"]):
                return {
                    "food_id": "smart_chaas",
                    "food_name": "Spiced Buttermilk (Chaas)",
                    "calories": 40.0,
                    "protein_g": 2.2,
                    "carbs_g": 3.5,
                    "fat_g": 1.5,
                    "fiber_g": 0.0,
                    "unit": "glass",
                }
            # Rice / Chawal / Bhaat
            if any(w in search_term for w in ["rice", "chawal", "bhaat", "pulao", "khichdi"]):
                return {
                    "food_id": "smart_rice",
                    "food_name": "Cooked White Rice",
                    "calories": 130.0,
                    "protein_g": 2.7,
                    "carbs_g": 28.0,
                    "fat_g": 0.3,
                    "fiber_g": 0.4,
                    "unit": "bowl",
                }
            # Dal / Lentils
            if any(w in search_term for w in ["dal", "daal", "toor", "moong", "sambhar", "kadhi"]):
                return {
                    "food_id": "smart_dal",
                    "food_name": "Yellow Toor Dal",
                    "calories": 120.0,
                    "protein_g": 7.0,
                    "carbs_g": 18.0,
                    "fat_g": 2.5,
                    "fiber_g": 4.0,
                    "unit": "bowl",
                }
            # Sabzi / Vegetables
            if any(w in search_term for w in ["sabzi", "shaak", "shak", "bhindi", "aloo", "palak"]):
                return {
                    "food_id": "smart_sabzi",
                    "food_name": "Mixed Vegetable Sabzi",
                    "calories": 110.0,
                    "protein_g": 2.5,
                    "carbs_g": 12.0,
                    "fat_g": 6.0,
                    "fiber_g": 3.5,
                    "unit": "bowl",
                }
            # Eggs / Poultry
            if any(w in search_term for w in ["egg", "anda", "ande", "omelette"]):
                return {
                    "food_id": "smart_egg",
                    "food_name": "Whole Boiled Egg",
                    "calories": 78.0,
                    "protein_g": 6.3,
                    "carbs_g": 0.6,
                    "fat_g": 5.3,
                    "fiber_g": 0.0,
                    "unit": "piece",
                }
            # Generic fallback
            return {
                "food_id": f"custom_{uuid.uuid4().hex[:8]}",
                "food_name": food_query.title(),
                "calories": 150.0,
                "protein_g": 4.0,
                "carbs_g": 20.0,
                "fat_g": 5.0,
                "fiber_g": 2.0,
                "unit": "serving",
            }

        calories = float(doc.get("calories_kcal") or doc.get("calories") or (doc.get("calories_per_100g", 100)))
        return {
            "food_id": doc.get("food_id") or str(doc.get("_id")),
            "food_name": doc.get("food_name_display") or doc.get("food_name", food_query.title()),
            "calories": calories,
            "protein_g": float(doc.get("protein_g", 0.0)),
            "carbs_g": float(doc.get("carbs_g", 0.0)),
            "fat_g": float(doc.get("fat_g", 0.0)),
            "fiber_g": float(doc.get("fiber_g", 0.0)),
            "category": doc.get("category"),
            "unit": doc.get("serving_unit", "serving"),
        }

    @staticmethod
    async def process_and_log_food(
        user_id: str,
        items: List[FoodItemInput],
        meal_type_override: Optional[str] = None,
        log_date_str: Optional[str] = None,
    ) -> FoodLoggingResult:
        db = get_db()
        now = datetime.now(timezone.utc)
        target_date_str = log_date_str or now.strftime("%Y-%m-%d")
        meal_type = meal_type_override or "LUNCH"

        logged_items = []
        total_meal_cal = 0.0
        total_meal_p = 0.0
        total_meal_c = 0.0
        total_meal_f = 0.0
        total_meal_fib = 0.0

        for item in items:
            resolved = await FoodService.resolve_food(item.food)
            qty = item.quantity if item.quantity and item.quantity > 0 else 1.0
            unit = item.unit or resolved.get("unit", "serving")

            item_cal = round(resolved["calories"] * qty, 1)
            item_p = round(resolved["protein_g"] * qty, 1)
            item_c = round(resolved["carbs_g"] * qty, 1)
            item_f = round(resolved["fat_g"] * qty, 1)
            item_fib = round(resolved["fiber_g"] * qty, 1)

            # Idempotency check: prevent duplicate entry within 5 seconds
            five_sec_ago = datetime.fromtimestamp(now.timestamp() - 5, timezone.utc)
            duplicate = await db.daily_food_logs.find_one({
                "user_id": user_id,
                "food_id": resolved["food_id"],
                "quantity_amount": qty,
                "created_at": {"$gte": five_sec_ago},
            })

            if duplicate:
                log_doc = duplicate
            else:
                log_id = str(uuid.uuid4())
                log_doc = {
                    "id": log_id,
                    "user_id": user_id,
                    "food_id": resolved["food_id"],
                    "food_name": resolved["food_name"],
                    "meal_type": meal_type,
                    "quantity_amount": qty,
                    "quantity_unit": unit,
                    "calories": item_cal,
                    "protein_g": item_p,
                    "carbs_g": item_c,
                    "fat_g": item_f,
                    "fiber_g": item_fib,
                    "log_date": target_date_str,
                    "created_at": now,
                    "logged_at": now,
                }
                await db.daily_food_logs.insert_one(log_doc)

            clean_log = {**log_doc, "id": str(log_doc.get("id") or log_doc.get("_id"))}
            clean_log.pop("_id", None)
            if hasattr(clean_log.get("created_at"), "isoformat"):
                clean_log["created_at"] = clean_log["created_at"].isoformat()
            if hasattr(clean_log.get("logged_at"), "isoformat"):
                clean_log["logged_at"] = clean_log["logged_at"].isoformat()
            logged_items.append(clean_log)

            total_meal_cal += item_cal
            total_meal_p += item_p
            total_meal_c += item_c
            total_meal_f += item_f
            total_meal_fib += item_fib

        summary_result = await FoodService.get_daily_grouped_food_cards(user_id, target_date_str)

        items_parts = []
        for inp_item, l in zip(items, logged_items):
            qty_val = int(l['quantity_amount']) if l['quantity_amount'].is_integer() else l['quantity_amount']
            raw_q = (inp_item.food or "").strip()
            if raw_q and raw_q.lower() != l['food_name'].lower() and raw_q.lower() not in l['food_name'].lower():
                items_parts.append(f"{qty_val} {l['quantity_unit']} {l['food_name']} ({raw_q}) ({int(l['calories'])} kcal)")
            else:
                items_parts.append(f"{qty_val} {l['quantity_unit']} {l['food_name']} ({int(l['calories'])} kcal)")
        items_summary = ", ".join(items_parts)
        reply_text = f"Logged {items_summary} for {meal_type.lower()}. Meal total: {int(total_meal_cal)} kcal (P: {int(total_meal_p)}g, C: {int(total_meal_c)}g, F: {int(total_meal_f)}g). Today's total: {int(summary_result['dailyNutritionSummary'].totalCalories)} / {int(summary_result['dailyNutritionSummary'].targetCalories)} kcal."

        return FoodLoggingResult(
            success=True,
            requiresClarification=False,
            loggedItems=logged_items,
            groupedFoodCards=summary_result["groupedFoodCards"],
            dailyNutritionSummary=summary_result["dailyNutritionSummary"],
            mealTotals={
                "calories": round(total_meal_cal, 1),
                "proteinG": round(total_meal_p, 1),
                "carbsG": round(total_meal_c, 1),
                "fatG": round(total_meal_f, 1),
                "fiberG": round(total_meal_fib, 1),
            },
            dailyProgress={
                "totalCaloriesLoggedToday": summary_result["dailyNutritionSummary"].totalCalories,
                "dailyCalorieTarget": summary_result["dailyNutritionSummary"].targetCalories,
                "remainingCalories": summary_result["dailyNutritionSummary"].remainingCalories,
            },
            replyText=reply_text,
        )

    @staticmethod
    async def update_food_log(
        user_id: str,
        target_food: str,
        new_quantity: float,
        unit: Optional[str] = None,
        log_date_str: Optional[str] = None,
    ) -> FoodLoggingResult:
        """Modifies the user's latest logged food for the given day."""
        db = get_db()
        now = datetime.now(timezone.utc)
        target_date_str = log_date_str or now.strftime("%Y-%m-%d")

        resolved = await FoodService.resolve_food(target_food)
        target_food_name = resolved["food_name"]

        # Find existing log for today matching food_id or food_name
        existing = await db.daily_food_logs.find_one({
            "user_id": user_id,
            "log_date": target_date_str,
            "$or": [
                {"food_id": resolved["food_id"]},
                {"food_name": {"$regex": target_food, "$options": "i"}},
                {"food_name": {"$regex": target_food_name, "$options": "i"}},
            ]
        }, sort=[("created_at", -1)])

        qty = max(0.25, float(new_quantity))
        item_cal = round(resolved["calories"] * qty, 1)
        item_p = round(resolved["protein_g"] * qty, 1)
        item_c = round(resolved["carbs_g"] * qty, 1)
        item_f = round(resolved["fat_g"] * qty, 1)
        item_fib = round(resolved["fiber_g"] * qty, 1)

        if existing:
            await db.daily_food_logs.update_one(
                {"id": existing["id"]},
                {"$set": {
                    "quantity_amount": qty,
                    "calories": item_cal,
                    "protein_g": item_p,
                    "carbs_g": item_c,
                    "fat_g": item_f,
                    "fiber_g": item_fib,
                    "updated_at": now,
                }}
            )
            reply = f"Updated {target_food_name} to {int(qty) if qty.is_integer() else qty} {existing.get('quantity_unit', 'serving')} ({int(item_cal)} kcal)."
        else:
            # If not found, log it afresh
            return await FoodService.process_and_log_food(
                user_id,
                [FoodItemInput(food=target_food, quantity=qty, unit=unit or resolved.get("unit", "serving"))],
                log_date_str=target_date_str,
            )

        summary_result = await FoodService.get_daily_grouped_food_cards(user_id, target_date_str)
        return FoodLoggingResult(
            success=True,
            requiresClarification=False,
            loggedItems=[],
            groupedFoodCards=summary_result["groupedFoodCards"],
            dailyNutritionSummary=summary_result["dailyNutritionSummary"],
            mealTotals={"calories": item_cal},
            dailyProgress={
                "totalCaloriesLoggedToday": summary_result["dailyNutritionSummary"].totalCalories,
                "dailyCalorieTarget": summary_result["dailyNutritionSummary"].targetCalories,
                "remainingCalories": summary_result["dailyNutritionSummary"].remainingCalories,
            },
            replyText=reply,
        )

    @staticmethod
    async def delete_food_log(
        user_id: str,
        target_food: str,
        log_date_str: Optional[str] = None,
    ) -> FoodLoggingResult:
        """Deletes the user's logged food matching target_food for the day."""
        db = get_db()
        now = datetime.now(timezone.utc)
        target_date_str = log_date_str or now.strftime("%Y-%m-%d")

        resolved = await FoodService.resolve_food(target_food)
        target_name = resolved["food_name"]

        del_res = await db.daily_food_logs.delete_one({
            "user_id": user_id,
            "log_date": target_date_str,
            "$or": [
                {"food_id": resolved["food_id"]},
                {"food_name": {"$regex": target_food, "$options": "i"}},
                {"food_name": {"$regex": target_name, "$options": "i"}},
            ]
        })

        if del_res.deleted_count > 0:
            reply = f"Successfully removed {target_name} from today's logs."
        else:
            reply = f"Could not find {target_food} in today's food logs."

        summary_result = await FoodService.get_daily_grouped_food_cards(user_id, target_date_str)
        return FoodLoggingResult(
            success=True,
            requiresClarification=False,
            loggedItems=[],
            groupedFoodCards=summary_result["groupedFoodCards"],
            dailyNutritionSummary=summary_result["dailyNutritionSummary"],
            mealTotals={"calories": 0.0},
            dailyProgress={
                "totalCaloriesLoggedToday": summary_result["dailyNutritionSummary"].totalCalories,
                "dailyCalorieTarget": summary_result["dailyNutritionSummary"].targetCalories,
                "remainingCalories": summary_result["dailyNutritionSummary"].remainingCalories,
            },
            replyText=reply,
        )

    @staticmethod
    async def get_daily_grouped_food_cards(user_id: str, date_str: str) -> Dict[str, Any]:
        db = get_db()
        cursor = db.daily_food_logs.find({"user_id": user_id, "log_date": date_str}).sort("created_at", 1)
        logs = await cursor.to_list(length=500)

        # Fetch user target calories
        user = await db.users.find_one({"id": user_id}) or await db.users.find_one({"user_id": user_id}) or {}
        profile = user.get("profile") or {}
        target_calories = profile.get("dailyCalorieTarget", 2000)

        groups: Dict[str, Dict[str, Any]] = {}
        total_cal = 0.0
        total_p = 0.0
        total_c = 0.0
        total_f = 0.0
        total_fib = 0.0

        for log in logs:
            food_key = log.get("food_id") or log.get("food_name", "").lower().strip()
            if food_key not in groups:
                groups[food_key] = {
                    "foodKey": f"food_{food_key}",
                    "foodMasterId": log.get("food_id"),
                    "foodName": log.get("food_name"),
                    "icon": FoodService.resolve_food_icon(log.get("food_name", "")),
                    "unit": log.get("quantity_unit", "serving"),
                    "totalQuantity": 0.0,
                    "totalCalories": 0.0,
                    "entryCount": 0,
                    "macros": {"proteinG": 0.0, "carbsG": 0.0, "fatG": 0.0, "fiberG": 0.0},
                    "entries": [],
                }

            g = groups[food_key]
            qty = float(log.get("quantity_amount", 1.0))
            cal = float(log.get("calories", 0.0))
            p = float(log.get("protein_g", 0.0))
            c = float(log.get("carbs_g", 0.0))
            f = float(log.get("fat_g", 0.0))
            fib = float(log.get("fiber_g", 0.0))

            g["totalQuantity"] += qty
            g["totalCalories"] += cal
            g["entryCount"] += 1
            g["macros"]["proteinG"] += p
            g["macros"]["carbsG"] += c
            g["macros"]["fatG"] += f
            g["macros"]["fiberG"] += fib

            total_cal += cal
            total_p += p
            total_c += c
            total_f += f
            total_fib += fib

            dt = log.get("logged_at") or log.get("created_at") or datetime.now(timezone.utc)
            g["entries"].append(
                FoodLogEntrySummary(
                    id=str(log.get("id") or log.get("_id")),
                    foodMasterId=log.get("food_id"),
                    foodName=log.get("food_name"),
                    quantity=qty,
                    unit=log.get("quantity_unit", "serving"),
                    calories=round(cal, 1),
                    loggedAt=dt.isoformat() if hasattr(dt, "isoformat") else str(dt),
                    timeFormatted=FoodService.format_time(dt),
                    mealType=log.get("meal_type", "LUNCH"),
                    macros={
                        "proteinG": round(p, 1),
                        "carbsG": round(c, 1),
                        "fatG": round(f, 1),
                        "fiberG": round(fib, 1),
                    },
                )
            )

        grouped_cards = []
        for g in groups.values():
            qty_val = g["totalQuantity"]
            grouped_cards.append(
                GroupedFoodCard(
                    foodKey=g["foodKey"],
                    foodMasterId=g["foodMasterId"],
                    foodName=g["foodName"],
                    icon=g["icon"],
                    unit=g["unit"] + ("s" if qty_val > 1 and not g["unit"].endswith("s") else ""),
                    totalQuantity=int(qty_val) if qty_val.is_integer() else round(qty_val, 1),
                    totalCalories=round(g["totalCalories"]),
                    entryCount=g["entryCount"],
                    macros={k: round(v, 1) for k, v in g["macros"].items()},
                    entries=g["entries"],
                )
            )

        remaining_calories = max(0.0, float(target_calories) - total_cal)
        percent_target = min(100, int((total_cal / target_calories) * 100)) if target_calories > 0 else 0

        daily_summary = DailyNutritionSummaryData(
            date=date_str,
            totalCalories=round(total_cal),
            targetCalories=round(float(target_calories)),
            remainingCalories=round(remaining_calories),
            percentOfTarget=percent_target,
            macros={
                "protein": round(total_p, 1),
                "carbs": round(total_c, 1),
                "fat": round(total_f, 1),
                "fiber": round(total_fib, 1),
            },
            totalProteinG=round(total_p, 1),
            totalCarbsG=round(total_c, 1),
            totalFatG=round(total_f, 1),
            totalFiberG=round(total_fib, 1),
            distinctFoodsCount=len(grouped_cards),
            totalEntries=len(logs),
            totalEntriesCount=len(logs),
        )

        return {
            "groupedFoodCards": grouped_cards,
            "dailyNutritionSummary": daily_summary,
        }
