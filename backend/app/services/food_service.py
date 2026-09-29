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

CANONICAL_INDIAN_FOOD_PROFILES: Dict[str, Dict[str, Any]] = {
    "Roti": {"food_id": "canon_roti", "food_name": "Roti", "calories": 104.0, "protein_g": 3.1, "carbs_g": 20.0, "fat_g": 1.2, "fiber_g": 2.8, "unit": "piece"},
    "Bhakri": {"food_id": "canon_bhakri", "food_name": "Bhakri", "calories": 130.0, "protein_g": 3.8, "carbs_g": 24.0, "fat_g": 2.2, "fiber_g": 3.0, "unit": "piece"},
    "Whole Wheat Bhakri": {"food_id": "canon_bhakri", "food_name": "Bhakri", "calories": 130.0, "protein_g": 3.8, "carbs_g": 24.0, "fat_g": 2.2, "fiber_g": 3.0, "unit": "piece"},
    "Rotlo": {"food_id": "canon_bajra_roti", "food_name": "Rotlo (Bajra Roti)", "calories": 116.0, "protein_g": 3.2, "carbs_g": 22.0, "fat_g": 1.5, "fiber_g": 3.5, "unit": "piece"},
    "Rotla": {"food_id": "canon_bajra_roti", "food_name": "Rotlo (Bajra Roti)", "calories": 116.0, "protein_g": 3.2, "carbs_g": 22.0, "fat_g": 1.5, "fiber_g": 3.5, "unit": "piece"},
    "Bajra Roti": {"food_id": "canon_bajra_roti", "food_name": "Rotlo (Bajra Roti)", "calories": 116.0, "protein_g": 3.2, "carbs_g": 22.0, "fat_g": 1.5, "fiber_g": 3.5, "unit": "piece"},
    "Bajri Rotla": {"food_id": "canon_bajra_roti", "food_name": "Rotlo (Bajra Roti)", "calories": 116.0, "protein_g": 3.2, "carbs_g": 22.0, "fat_g": 1.5, "fiber_g": 3.5, "unit": "piece"},
    "Baingan Bharta": {"food_id": "canon_bharta", "food_name": "Baingan Bharta", "calories": 120.0, "protein_g": 2.5, "carbs_g": 14.0, "fat_g": 6.0, "fiber_g": 4.5, "unit": "bowl"},
    "Bhadthu": {"food_id": "canon_bharta", "food_name": "Baingan Bharta", "calories": 120.0, "protein_g": 2.5, "carbs_g": 14.0, "fat_g": 6.0, "fiber_g": 4.5, "unit": "bowl"},
    "Methi Thepla": {"food_id": "canon_thepla", "food_name": "Methi Thepla", "calories": 115.0, "protein_g": 3.0, "carbs_g": 18.0, "fat_g": 3.5, "fiber_g": 2.5, "unit": "piece"},
    "Plain Paratha": {"food_id": "canon_paratha", "food_name": "Plain Paratha", "calories": 180.0, "protein_g": 4.0, "carbs_g": 28.0, "fat_g": 6.0, "fiber_g": 2.0, "unit": "piece"},
    "Aloo Paratha": {"food_id": "canon_aloo_paratha", "food_name": "Aloo Paratha", "calories": 240.0, "protein_g": 5.0, "carbs_g": 36.0, "fat_g": 8.5, "fiber_g": 3.5, "unit": "piece"},
    "Paneer Paratha": {"food_id": "canon_paneer_paratha", "food_name": "Paneer Paratha", "calories": 280.0, "protein_g": 11.0, "carbs_g": 32.0, "fat_g": 12.0, "fiber_g": 2.5, "unit": "piece"},
    "Poori": {"food_id": "canon_poori", "food_name": "Poori", "calories": 125.0, "protein_g": 2.0, "carbs_g": 16.0, "fat_g": 6.0, "fiber_g": 1.0, "unit": "piece"},
    "Butter Naan": {"food_id": "canon_butter_naan", "food_name": "Butter Naan", "calories": 260.0, "protein_g": 6.0, "carbs_g": 40.0, "fat_g": 8.0, "fiber_g": 2.0, "unit": "piece"},
    "Cooked White Rice": {"food_id": "canon_rice", "food_name": "Cooked White Rice", "calories": 130.0, "protein_g": 2.7, "carbs_g": 28.0, "fat_g": 0.3, "fiber_g": 0.4, "unit": "bowl"},
    "Moong Dal Khichdi": {"food_id": "canon_khichdi", "food_name": "Moong Dal Khichdi", "calories": 175.0, "protein_g": 6.0, "carbs_g": 32.0, "fat_g": 2.5, "fiber_g": 3.5, "unit": "bowl"},
    "Poha": {"food_id": "canon_poha", "food_name": "Poha", "calories": 180.0, "protein_g": 3.5, "carbs_g": 33.0, "fat_g": 4.5, "fiber_g": 2.5, "unit": "plate"},
    "Upma": {"food_id": "canon_upma", "food_name": "Upma", "calories": 190.0, "protein_g": 4.0, "carbs_g": 34.0, "fat_g": 4.5, "fiber_g": 2.5, "unit": "bowl"},
    "Idli": {"food_id": "canon_idli", "food_name": "Idli", "calories": 58.0, "protein_g": 2.0, "carbs_g": 12.0, "fat_g": 0.2, "fiber_g": 1.0, "unit": "piece"},
    "Plain Dosa": {"food_id": "canon_plain_dosa", "food_name": "Plain Dosa", "calories": 168.0, "protein_g": 3.8, "carbs_g": 29.0, "fat_g": 3.7, "fiber_g": 1.5, "unit": "piece"},
    "Masala Dosa": {"food_id": "canon_masala_dosa", "food_name": "Masala Dosa", "calories": 250.0, "protein_g": 4.5, "carbs_g": 38.0, "fat_g": 9.0, "fiber_g": 2.5, "unit": "piece"},
    "Onion Tomato Uttapam": {"food_id": "canon_uttapam", "food_name": "Onion Tomato Uttapam", "calories": 220.0, "protein_g": 5.0, "carbs_g": 35.0, "fat_g": 6.0, "fiber_g": 2.8, "unit": "piece"},
    "Toor Dal": {"food_id": "canon_toor_dal", "food_name": "Toor Dal", "calories": 120.0, "protein_g": 7.0, "carbs_g": 18.0, "fat_g": 2.5, "fiber_g": 4.0, "unit": "bowl"},
    "Yellow Moong Dal": {"food_id": "canon_moong_dal", "food_name": "Yellow Moong Dal", "calories": 115.0, "protein_g": 7.5, "carbs_g": 17.5, "fat_g": 2.0, "fiber_g": 4.2, "unit": "bowl"},
    "Gujarati Kadhi": {"food_id": "canon_kadhi", "food_name": "Gujarati Kadhi", "calories": 120.0, "protein_g": 3.5, "carbs_g": 14.0, "fat_g": 5.5, "fiber_g": 1.0, "unit": "bowl"},
    "Sambar": {"food_id": "canon_sambar", "food_name": "Sambar", "calories": 110.0, "protein_g": 4.5, "carbs_g": 17.0, "fat_g": 2.5, "fiber_g": 3.5, "unit": "bowl"},
    "Chole Chana Masala": {"food_id": "canon_chole", "food_name": "Chole Chana Masala", "calories": 170.0, "protein_g": 7.0, "carbs_g": 25.0, "fat_g": 5.0, "fiber_g": 6.0, "unit": "bowl"},
    "Rajma": {"food_id": "canon_rajma", "food_name": "Rajma", "calories": 140.0, "protein_g": 8.0, "carbs_g": 23.0, "fat_g": 2.5, "fiber_g": 6.5, "unit": "bowl"},
    "Mixed Sprouts": {"food_id": "canon_sprouts", "food_name": "Mixed Sprouts", "calories": 110.0, "protein_g": 8.5, "carbs_g": 18.0, "fat_g": 1.0, "fiber_g": 5.0, "unit": "bowl"},
    "Mixed Vegetable Sabzi": {"food_id": "canon_sabzi", "food_name": "Mixed Vegetable Sabzi", "calories": 110.0, "protein_g": 2.5, "carbs_g": 12.0, "fat_g": 6.0, "fiber_g": 3.5, "unit": "bowl"},
    "Aloo Sabzi": {"food_id": "canon_aloo_sabzi", "food_name": "Aloo Sabzi", "calories": 135.0, "protein_g": 2.0, "carbs_g": 20.0, "fat_g": 5.5, "fiber_g": 2.5, "unit": "bowl"},
    "Bhindi Masala": {"food_id": "canon_bhindi", "food_name": "Bhindi Masala", "calories": 130.0, "protein_g": 3.0, "carbs_g": 11.0, "fat_g": 8.0, "fiber_g": 4.0, "unit": "bowl"},
    "Sev Tameta Nu Shaak": {"food_id": "canon_sev_tameta", "food_name": "Sev Tameta Nu Shaak", "calories": 180.0, "protein_g": 4.5, "carbs_g": 22.0, "fat_g": 8.5, "fiber_g": 3.0, "unit": "bowl"},
    "Surti Undhiyu": {"food_id": "canon_undhiyu", "food_name": "Surti Undhiyu", "calories": 240.0, "protein_g": 6.0, "carbs_g": 28.0, "fat_g": 12.0, "fiber_g": 5.5, "unit": "bowl"},
    "Gujarati Dal Dhokli": {"food_id": "canon_dal_dhokli", "food_name": "Gujarati Dal Dhokli", "calories": 220.0, "protein_g": 7.5, "carbs_g": 36.0, "fat_g": 5.5, "fiber_g": 4.5, "unit": "bowl"},
    "Gujarati Handvo": {"food_id": "canon_handvo", "food_name": "Gujarati Handvo", "calories": 185.0, "protein_g": 5.5, "carbs_g": 26.0, "fat_g": 6.5, "fiber_g": 3.5, "unit": "piece"},
    "Khaman Dhokla": {"food_id": "canon_khaman", "food_name": "Khaman Dhokla", "calories": 150.0, "protein_g": 5.0, "carbs_g": 24.0, "fat_g": 3.5, "fiber_g": 2.0, "unit": "piece"},
    "Muthiya": {"food_id": "canon_muthiya", "food_name": "Muthiya", "calories": 150.0, "protein_g": 4.0, "carbs_g": 25.0, "fat_g": 4.0, "fiber_g": 3.0, "unit": "piece"},
    "Patra": {"food_id": "canon_patra", "food_name": "Patra", "calories": 140.0, "protein_g": 3.5, "carbs_g": 22.0, "fat_g": 4.0, "fiber_g": 2.5, "unit": "piece"},
    "Methi Khakhra": {"food_id": "canon_khakhra", "food_name": "Methi Khakhra", "calories": 95.0, "protein_g": 2.8, "carbs_g": 16.0, "fat_g": 2.2, "fiber_g": 2.5, "unit": "piece"},
    "Fafda": {"food_id": "canon_fafda", "food_name": "Fafda", "calories": 175.0, "protein_g": 4.0, "carbs_g": 22.0, "fat_g": 8.0, "fiber_g": 2.0, "unit": "piece"},
    "Jalebi": {"food_id": "canon_jalebi", "food_name": "Jalebi", "calories": 150.0, "protein_g": 1.0, "carbs_g": 35.0, "fat_g": 2.0, "fiber_g": 0.2, "unit": "piece"},
    "Mohanthal": {"food_id": "canon_mohanthal", "food_name": "Mohanthal", "calories": 220.0, "protein_g": 4.0, "carbs_g": 28.0, "fat_g": 11.0, "fiber_g": 1.5, "unit": "piece"},
    "Sukhdi": {"food_id": "canon_sukhdi", "food_name": "Sukhdi", "calories": 200.0, "protein_g": 3.0, "carbs_g": 26.0, "fat_g": 10.0, "fiber_g": 1.5, "unit": "piece"},
    "Puran Poli": {"food_id": "canon_puran_poli", "food_name": "Puran Poli", "calories": 210.0, "protein_g": 4.5, "carbs_g": 38.0, "fat_g": 5.0, "fiber_g": 2.5, "unit": "piece"},
    "Basundi": {"food_id": "canon_basundi", "food_name": "Basundi", "calories": 220.0, "protein_g": 5.5, "carbs_g": 26.0, "fat_g": 10.5, "fiber_g": 0.0, "unit": "bowl"},
    "Shrikhand": {"food_id": "canon_shrikhand", "food_name": "Shrikhand", "calories": 230.0, "protein_g": 6.0, "carbs_g": 32.0, "fat_g": 9.0, "fiber_g": 0.0, "unit": "bowl"},
    "Pav Bhaji": {"food_id": "canon_pav_bhaji", "food_name": "Pav Bhaji", "calories": 350.0, "protein_g": 8.0, "carbs_g": 50.0, "fat_g": 13.0, "fiber_g": 4.5, "unit": "plate"},
    "Samosa": {"food_id": "canon_samosa", "food_name": "Samosa", "calories": 210.0, "protein_g": 3.5, "carbs_g": 25.0, "fat_g": 11.0, "fiber_g": 2.0, "unit": "piece"},
    "Green Salad": {"food_id": "canon_salad", "food_name": "Green Salad", "calories": 35.0, "protein_g": 1.5, "carbs_g": 6.5, "fat_g": 0.5, "fiber_g": 2.5, "unit": "bowl"},
    "Apple": {"food_id": "canon_apple", "food_name": "Apple", "calories": 95.0, "protein_g": 0.5, "carbs_g": 25.0, "fat_g": 0.3, "fiber_g": 4.4, "unit": "piece"},
    "Banana": {"food_id": "canon_banana", "food_name": "Banana", "calories": 105.0, "protein_g": 1.3, "carbs_g": 27.0, "fat_g": 0.3, "fiber_g": 3.1, "unit": "piece"},
    "Boiled Egg": {"food_id": "canon_boiled_egg", "food_name": "Boiled Egg", "calories": 78.0, "protein_g": 6.3, "carbs_g": 0.6, "fat_g": 5.3, "fiber_g": 0.0, "unit": "piece"},
    "Egg Omelette": {"food_id": "canon_omelette", "food_name": "Egg Omelette", "calories": 154.0, "protein_g": 12.0, "carbs_g": 1.5, "fat_g": 11.0, "fiber_g": 0.0, "unit": "piece"},
    "Chicken Breast": {"food_id": "canon_chicken_breast", "food_name": "Chicken Breast", "calories": 165.0, "protein_g": 31.0, "carbs_g": 0.0, "fat_g": 3.6, "fiber_g": 0.0, "unit": "piece"},
    "Chicken Tikka": {"food_id": "canon_chicken_tikka", "food_name": "Chicken Tikka", "calories": 220.0, "protein_g": 28.0, "carbs_g": 4.0, "fat_g": 10.0, "fiber_g": 1.0, "unit": "serving"},
    "Whey Protein Powder": {"food_id": "canon_whey", "food_name": "Whey Protein Powder", "calories": 120.0, "protein_g": 24.0, "carbs_g": 2.0, "fat_g": 1.5, "fiber_g": 0.0, "unit": "scoop"},
    "Paneer": {"food_id": "canon_paneer", "food_name": "Paneer", "calories": 265.0, "protein_g": 18.0, "carbs_g": 3.5, "fat_g": 20.0, "fiber_g": 0.0, "unit": "serving"},
    "Paneer Bhurji": {"food_id": "canon_paneer_bhurji", "food_name": "Paneer Bhurji", "calories": 220.0, "protein_g": 14.0, "carbs_g": 6.0, "fat_g": 16.0, "fiber_g": 1.5, "unit": "bowl"},
    "Curd (Dahi)": {"food_id": "canon_curd", "food_name": "Curd (Dahi)", "calories": 98.0, "protein_g": 4.5, "carbs_g": 6.0, "fat_g": 6.5, "fiber_g": 0.0, "unit": "bowl"},
    "Cow Milk (Toned)": {"food_id": "canon_milk", "food_name": "Cow Milk (Toned)", "calories": 120.0, "protein_g": 6.5, "carbs_g": 9.5, "fat_g": 6.0, "fiber_g": 0.0, "unit": "glass"},
    "Spiced Buttermilk (Chaas)": {"food_id": "canon_chaas", "food_name": "Spiced Buttermilk (Chaas)", "calories": 40.0, "protein_g": 2.2, "carbs_g": 3.5, "fat_g": 1.5, "fiber_g": 0.0, "unit": "glass"},
    "Tea With Milk": {"food_id": "canon_tea", "food_name": "Tea With Milk", "calories": 65.0, "protein_g": 2.0, "carbs_g": 9.0, "fat_g": 2.5, "fiber_g": 0.0, "unit": "cup"},
    "Coffee With Milk": {"food_id": "canon_coffee", "food_name": "Coffee With Milk", "calories": 75.0, "protein_g": 2.2, "carbs_g": 10.0, "fat_g": 2.8, "fiber_g": 0.0, "unit": "cup"},
    "Water": {"food_id": "canon_water", "food_name": "Water", "calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0, "fiber_g": 0.0, "unit": "glass"},
}

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
            r"\b(?:morning|afternoon|evening|night|breakfast|lunch|dinner|snack|savar|savare|saware|sawar|savaar|bapor|bapore|sanj|sanje|saanj|saanje|sanju|raat|raate|subah|subha|dopahar|shaam|sham|shami)\b"
            r"|\b(?:ma|maa|me|mein|ko|ne|nu|na|ni|no|thi|par|pe|se|of|for|in|at|on|with)\b"
            r"|\b(?:i|my|mine|me|maine|hamne|aaj|aaje|today)\b"
            r"|\b(?:and|ane|aur|sathe|sath|along with)\b"
            r"|\b(?:ate|had|eaten|have|drank|drink|drinking|khadha|khadhi|khadhu|khadho|khado|khaye|khaya|khayi|khalo|pidhi|pidhu|pidha|pidho|pido|piya|piyi|peeli|peena|lidhi|lidhu|lidho|lido|leedhi|leedhu|liya|li)\b"
            r"|\b(?:che|tha|thi|the|hata|hati|chho|chhe)\b"
            r"|(?:મેં|ખાધો|ખાધી|ખાધું|ખાધા|લીધો|લીધી|લીધું|લીધા|પીધો|પીધું|પીધી|પીધા|છે|હતી|હતો|હતા|આજે|બપોરે|બપોર|સવાર|સવારે|સાંજ|સાંજે|રાત્રે|રાત|સાથે|નાસ્તો|વાળુ|વાળું|માં|ના|ની|નો|નું|ને|થી|પર|માટે)"
            r"|(?:मैंने|खाया|खाई|खाए|पिया|पी|लिया|ली|है|था|थी|आज|सुबह|दोपहर|रात|साथ|नाश्ता|में|का|की|के|को|से|पर|पे|ने|लिए)",
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

        # Step 0: Check CANONICAL_INDIAN_FOOD_PROFILES directly first (exact match on clean_q or q)
        for c_name, c_prof in CANONICAL_INDIAN_FOOD_PROFILES.items():
            if c_name.lower() == clean_q or c_name.lower() == q:
                return c_prof

        # Step 1: Check known Indian dialect synonyms & slang map
        synonym_target = INDIAN_FOOD_SYNONYMS.get(clean_q) or INDIAN_FOOD_SYNONYMS.get(q)

        # Multi-word phrase matching with word boundaries before single tokens
        if not synonym_target:
            for food_key in sorted(INDIAN_FOOD_SYNONYMS.keys(), key=len, reverse=True):
                if " " in food_key or any(ord(c) > 127 for c in food_key):
                    if len(food_key) >= 3 and (food_key in clean_q or re.search(rf"\b{re.escape(food_key)}\b", clean_q, flags=re.I)):
                        synonym_target = INDIAN_FOOD_SYNONYMS[food_key]
                        break

        # Check if synonym_target matches a canonical profile before token splitting
        if synonym_target and synonym_target in CANONICAL_INDIAN_FOOD_PROFILES:
            return CANONICAL_INDIAN_FOOD_PROFILES[synonym_target]

        # Single tokens
        if not synonym_target:
            tokens = clean_q.split()
            for t in tokens:
                if t in INDIAN_FOOD_SYNONYMS:
                    synonym_target = INDIAN_FOOD_SYNONYMS[t]
                    break

        # Fallback substring
        if not synonym_target:
            for food_key in sorted(INDIAN_FOOD_SYNONYMS.keys(), key=len, reverse=True):
                if len(food_key) >= 3 and food_key in clean_q:
                    synonym_target = INDIAN_FOOD_SYNONYMS[food_key]
                    break

        # If canonical profile matches, return immediately with accurate macros and food name
        if synonym_target and synonym_target in CANONICAL_INDIAN_FOOD_PROFILES:
            return CANONICAL_INDIAN_FOOD_PROFILES[synonym_target]
        for c_name, c_prof in CANONICAL_INDIAN_FOOD_PROFILES.items():
            if c_name.lower() == clean_q or c_name.lower() == q:
                return c_prof

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

        # Step 4: Substring / regex search with word boundaries
        if not doc and len(clean_q) >= 3:
            doc = await db.foods.find_one({"food_name": {"$regex": rf"\b{escaped_clean}\b", "$options": "i"}})
        if not doc and len(clean_q) >= 3:
            doc = await db.foods.find_one({"food_name_display": {"$regex": rf"\b{escaped_clean}\b", "$options": "i"}})

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
        
        detected_meal = None
        for it in items:
            m = getattr(it, "mealType", None)
            if m and m != "LUNCH":
                detected_meal = m
                break
        if not detected_meal and items:
            detected_meal = getattr(items[0], "mealType", None)

        meal_type = meal_type_override or detected_meal or "LUNCH"

        logged_items = []
        total_meal_cal = 0.0
        total_meal_p = 0.0
        total_meal_c = 0.0
        total_meal_f = 0.0
        total_meal_fib = 0.0

        for item in items:
            if not item.quantity or item.quantity <= 0:
                continue
            resolved = await FoodService.resolve_food(item.food)
            qty = float(item.quantity)
            unit = item.unit or resolved.get("unit", "serving")
            item_meal_type = getattr(item, "mealType", None) or meal_type

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
                    "meal_type": item_meal_type,
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

        if not logged_items:
            return FoodLoggingResult(
                success=True,
                requiresClarification=False,
                replyText="No food items were logged because quantity was zero or missing.",
                loggedItems=[],
                groupedFoodCards=summary_result["groupedFoodCards"],
                dailyNutritionSummary=summary_result["dailyNutritionSummary"],
                mealTotals={"calories": 0.0, "proteinG": 0.0, "carbsG": 0.0, "fatG": 0.0, "fiberG": 0.0},
                dailyProgress={
                    "totalCaloriesLoggedToday": summary_result["dailyNutritionSummary"].totalCalories,
                    "dailyCalorieTarget": summary_result["dailyNutritionSummary"].targetCalories,
                    "remainingCalories": summary_result["dailyNutritionSummary"].remainingCalories,
                },
            )

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
                "proteinG": round(total_p, 1),
                "carbsG": round(total_c, 1),
                "fatG": round(total_f, 1),
                "fiberG": round(total_fib, 1),
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
