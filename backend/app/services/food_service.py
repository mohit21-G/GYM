import re
import uuid
import difflib
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from ..database import get_db
from .agent_nlp import AgentNLP, INDIAN_FOOD_SYNONYMS
from .time_service import TimeService
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
    "Chapati": {"food_id": "canon_chapati", "food_name": "Chapati", "calories": 85.0, "protein_g": 3.0, "carbs_g": 17.0, "fat_g": 0.8, "fiber_g": 2.5, "unit": "piece"},
    "Phulka": {"food_id": "canon_phulka", "food_name": "Phulka", "calories": 70.0, "protein_g": 2.8, "carbs_g": 15.0, "fat_g": 0.4, "fiber_g": 2.4, "unit": "piece"},
    "Bhakri": {"food_id": "canon_bhakri", "food_name": "Bhakri", "calories": 130.0, "protein_g": 3.8, "carbs_g": 24.0, "fat_g": 2.2, "fiber_g": 3.0, "unit": "piece"},
    "Whole Wheat Bhakri": {"food_id": "canon_bhakri", "food_name": "Bhakri", "calories": 130.0, "protein_g": 3.8, "carbs_g": 24.0, "fat_g": 2.2, "fiber_g": 3.0, "unit": "piece"},
    "Rotlo": {"food_id": "canon_bajra_roti", "food_name": "Rotlo", "calories": 116.0, "protein_g": 3.2, "carbs_g": 22.0, "fat_g": 1.5, "fiber_g": 3.5, "unit": "piece"},
    "Rotla": {"food_id": "canon_bajra_roti", "food_name": "Rotlo", "calories": 116.0, "protein_g": 3.2, "carbs_g": 22.0, "fat_g": 1.5, "fiber_g": 3.5, "unit": "piece"},
    "Rotlo (Bajra Roti)": {"food_id": "canon_bajra_roti", "food_name": "Rotlo", "calories": 116.0, "protein_g": 3.2, "carbs_g": 22.0, "fat_g": 1.5, "fiber_g": 3.5, "unit": "piece"},
    "Bajra Roti": {"food_id": "canon_bajra_roti", "food_name": "Rotlo", "calories": 116.0, "protein_g": 3.2, "carbs_g": 22.0, "fat_g": 1.5, "fiber_g": 3.5, "unit": "piece"},
    "Bajri Rotla": {"food_id": "canon_bajra_roti", "food_name": "Rotlo", "calories": 116.0, "protein_g": 3.2, "carbs_g": 22.0, "fat_g": 1.5, "fiber_g": 3.5, "unit": "piece"},
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
    "Whey Protein Powder": {"food_id": "canon_whey", "food_name": "Whey Protein Powder", "calories": 120.0, "protein_g": 24.0, "carbs_g": 2.0, "fat_g": 1.5, "fiber_g": 0.0, "unit": "scoop"},
    "Protein Powder": {"food_id": "canon_whey", "food_name": "Whey Protein Powder", "calories": 120.0, "protein_g": 24.0, "carbs_g": 2.0, "fat_g": 1.5, "fiber_g": 0.0, "unit": "scoop"},
    "Protein Shake": {"food_id": "canon_protein_shake", "food_name": "Protein Shake", "calories": 160.0, "protein_g": 25.0, "carbs_g": 8.0, "fat_g": 3.0, "fiber_g": 1.0, "unit": "glass"},
    "Whey Protein Shake": {"food_id": "canon_protein_shake", "food_name": "Protein Shake", "calories": 160.0, "protein_g": 25.0, "carbs_g": 8.0, "fat_g": 3.0, "fiber_g": 1.0, "unit": "glass"},
    "Plant Protein Powder": {"food_id": "canon_plant_protein", "food_name": "Plant Protein Powder", "calories": 115.0, "protein_g": 22.0, "carbs_g": 3.0, "fat_g": 1.5, "fiber_g": 1.5, "unit": "scoop"},
    "Chicken Tikka": {"food_id": "canon_chicken_tikka", "food_name": "Chicken Tikka", "calories": 220.0, "protein_g": 28.0, "carbs_g": 4.0, "fat_g": 10.0, "fiber_g": 1.0, "unit": "serving"},
    "Paneer": {"food_id": "canon_paneer", "food_name": "Paneer", "calories": 265.0, "protein_g": 18.0, "carbs_g": 3.5, "fat_g": 20.0, "fiber_g": 0.0, "unit": "serving"},
    "Paneer Bhurji": {"food_id": "canon_paneer_bhurji", "food_name": "Paneer Bhurji", "calories": 220.0, "protein_g": 14.0, "carbs_g": 6.0, "fat_g": 16.0, "fiber_g": 1.5, "unit": "bowl"},
    "Curd (Dahi)": {"food_id": "canon_curd", "food_name": "Curd (Dahi)", "calories": 98.0, "protein_g": 4.5, "carbs_g": 6.0, "fat_g": 6.5, "fiber_g": 0.0, "unit": "bowl"},
    "Cow Milk (Toned)": {"food_id": "canon_milk", "food_name": "Cow Milk (Toned)", "calories": 120.0, "protein_g": 6.5, "carbs_g": 9.5, "fat_g": 6.0, "fiber_g": 0.0, "unit": "glass"},
    "Milk": {"food_id": "canon_milk", "food_name": "Cow Milk (Toned)", "calories": 120.0, "protein_g": 6.5, "carbs_g": 9.5, "fat_g": 6.0, "fiber_g": 0.0, "unit": "cup"},
    "Khapli Roti": {"food_id": "canon_khapli_roti", "food_name": "Khapli Wheat Rotli", "calories": 95.0, "protein_g": 3.2, "carbs_g": 18.0, "fat_g": 1.2, "fiber_g": 2.5, "unit": "piece"},
    "Khapli Wheat Rotli": {"food_id": "canon_khapli_roti", "food_name": "Khapli Wheat Rotli", "calories": 95.0, "protein_g": 3.2, "carbs_g": 18.0, "fat_g": 1.2, "fiber_g": 2.5, "unit": "piece"},
    "Spiced Buttermilk (Chaas)": {"food_id": "canon_chaas", "food_name": "Spiced Buttermilk (Chaas)", "calories": 40.0, "protein_g": 2.2, "carbs_g": 3.5, "fat_g": 1.5, "fiber_g": 0.0, "unit": "glass"},
    "Tea With Milk": {"food_id": "canon_tea", "food_name": "Tea With Milk", "calories": 65.0, "protein_g": 2.0, "carbs_g": 9.0, "fat_g": 2.5, "fiber_g": 0.0, "unit": "cup"},
    "Green Tea": {"food_id": "canon_green_tea", "food_name": "Green Tea", "calories": 2.0, "protein_g": 0.2, "carbs_g": 0.4, "fat_g": 0.0, "fiber_g": 0.0, "unit": "cup"},
    "Black Coffee": {"food_id": "canon_black_coffee", "food_name": "Black Coffee", "calories": 5.0, "protein_g": 0.3, "carbs_g": 0.5, "fat_g": 0.0, "fiber_g": 0.0, "unit": "cup"},
    "Lemon Water": {"food_id": "canon_lemon_water", "food_name": "Lemon Water", "calories": 15.0, "protein_g": 0.2, "carbs_g": 3.5, "fat_g": 0.1, "fiber_g": 0.2, "unit": "glass"},
    "Pre Workout": {"food_id": "canon_pre_workout", "food_name": "Pre Workout", "calories": 10.0, "protein_g": 0.0, "carbs_g": 2.0, "fat_g": 0.0, "fiber_g": 0.0, "unit": "scoop"},
    "Oats": {"food_id": "canon_oats", "food_name": "Oats", "calories": 150.0, "protein_g": 5.0, "carbs_g": 27.0, "fat_g": 2.5, "fiber_g": 4.0, "unit": "bowl"},
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
    def format_time(dt: Any) -> str:
        return TimeService.format_time(dt)

    @staticmethod
    def get_quantity_clarification_question(food_name: str, lang: str = "en") -> str:
        """
        Generates food-specific quantity clarification questions matching user requirements.
        Supports English, Gujarati, and Hindi with tailored serving units.
        """
        fn_lower = food_name.lower().strip()

        # Water
        if "water" in fn_lower or "pani" in fn_lower or "પાણી" in fn_lower or "पानी" in fn_lower:
            if lang in ["gu", "gu-Latn"]:
                return "તમે કેટલું પાણી પીધું? (દા.ત. 1 ગ્લાસ, 2 ગ્લાસ, 1 બોટલ)"
            elif lang in ["hi", "hi-Latn"]:
                return "आपने कितना पानी पिया? (जैसे 1 ग्लास, 2 ग्लास, 1 बोतल)"
            return "How much water did you drink? (e.g. 1 glass, 2 glasses, 1 bottle)"

        # Tea / Green Tea / Chai / Coffee
        if any(w in fn_lower for w in ["green tea", "tea", "chai", "coffee", "chay", "ટી"]):
            display_name = "green tea" if "green tea" in fn_lower else ("tea" if "tea" in fn_lower or "chai" in fn_lower else "coffee")
            if lang in ["gu", "gu-Latn"]:
                return f"તમે કેટલી {display_name} પીધી? (દા.ત. 1 કપ, 2 કપ)"
            elif lang in ["hi", "hi-Latn"]:
                return f"आपने कितनी {display_name} पी? (जैसे 1 कप, 2 कप)"
            return f"How much {display_name} did you have? (e.g. 1 cup, 2 cups)"

        # Milk / Chaas / Buttermilk
        if any(w in fn_lower for w in ["milk", "doodh", "dudh", "chaas", "chhas", "buttermilk", "lassi", "juice"]):
            display_name = "milk" if any(w in fn_lower for w in ["milk", "doodh", "dudh"]) else ("chaas" if "chaas" in fn_lower or "chhas" in fn_lower else fn_lower)
            if lang in ["gu", "gu-Latn"]:
                return f"તમે કેટલું {display_name} પીધું? (દા.ત. 1 ગ્લાસ, 2 ગ્લાસ)"
            elif lang in ["hi", "hi-Latn"]:
                return f"आपने कितना {display_name} पिया? (जैसे 1 ग्लास, 2 ग्लास)"
            return f"How much {display_name} did you have? (e.g. 1 glass, 2 glasses)"

        # Protein Shake
        if "shake" in fn_lower or "smoothie" in fn_lower:
            if lang in ["gu", "gu-Latn"]:
                return "તમે કેટલો પ્રોટીન શેક લીધો? (દા.ત. 1 સ્કૂપ, 2 સ્કૂપ, 1 ગ્લાસ)"
            elif lang in ["hi", "hi-Latn"]:
                return "आपने कितना प्रोटीन शेक लिया? (जैसे 1 स्कूप, 2 स्कूप, 1 ग्लास)"
            return "How much protein shake did you have? (e.g. 1 scoop, 2 scoops, 1 glass)"

        # Protein Powder / Whey
        if "powder" in fn_lower or "whey" in fn_lower or fn_lower == "protein":
            if lang in ["gu", "gu-Latn"]:
                return "તમે કેટલો પ્રોટીન પાવડર લીધો? (દા.ત. 1 સ્કૂપ, 2 સ્કૂપ)"
            elif lang in ["hi", "hi-Latn"]:
                return "आपने कितना प्रोटीन पाउडर लिया? (जैसे 1 स्कूप, 2 स्कूप)"
            return "How much protein powder did you have? (e.g. 1 scoop, 2 scoops)"

        # Flatbreads / Pieces (Roti, Chapati, Rotli, Thepla, Bhakri, Paratha, Naan, Puri)
        if any(w in fn_lower for w in ["roti", "rotli", "chapati", "phulka", "thepla", "bhakri", "bhakhri", "paratha", "naan", "puri", "poori", "રોટલી", "ભાખરી", "થેપલા"]):
            if "bhakri" in fn_lower or "bhakhri" in fn_lower or "ભાખરી" in fn_lower:
                singular, plural = "bhakri", "bhakris"
            elif "thepla" in fn_lower or "થેપલા" in fn_lower:
                singular, plural = "thepla", "theplas"
            elif "paratha" in fn_lower:
                singular, plural = "paratha", "parathas"
            elif "naan" in fn_lower:
                singular, plural = "naan", "naans"
            elif "chapati" in fn_lower:
                singular, plural = "chapati", "chapatis"
            else:
                singular, plural = "roti", "rotis"

            if lang in ["gu", "gu-Latn"]:
                return f"તમે કેટલી {plural} ખાધી? (દા.ત. 1 {singular}, 2 {plural})"
            elif lang in ["hi", "hi-Latn"]:
                return f"आपने कितनी {plural} खाईं? (जैसे 1 {singular}, 2 {plural})"
            return f"How many {plural} did you have? (e.g. 1 {singular}, 2 {plural})"

        # Countable fruits & items (Egg, Banana, Apple, Samosa, Idli, Dhokla, etc.)
        if any(w in fn_lower for w in ["egg", "anda", "banana", "kela", "apple", "safarjan", "samosa", "idli", "dhokla", "khaman", "cookie", "biscuit", "ઈંડા", "કેળા", "સફરજન"]):
            if "egg" in fn_lower or "anda" in fn_lower or "ઈંડા" in fn_lower:
                singular, plural = "egg", "eggs"
            elif "banana" in fn_lower or "kela" in fn_lower or "કેળા" in fn_lower:
                singular, plural = "banana", "bananas"
            elif "apple" in fn_lower or "safarjan" in fn_lower or "સફરજન" in fn_lower:
                singular, plural = "apple", "apples"
            elif "samosa" in fn_lower:
                singular, plural = "samosa", "samosas"
            elif "idli" in fn_lower:
                singular, plural = "idli", "idlis"
            else:
                singular, plural = fn_lower, f"{fn_lower}s"

            if lang in ["gu", "gu-Latn"]:
                return f"તમે કેટલા {plural} ખાધા? (દા.ત. 1 {singular}, 2 {plural})"
            elif lang in ["hi", "hi-Latn"]:
                return f"आपने कितने {plural} खाए? (जैसे 1 {singular}, 2 {plural})"
            return f"How many {plural} did you have? (e.g. 1 {singular}, 2 {plural})"

        # Bowls: Rice, Dal, Poha, Upma, Oats, Khichdi, Sabzi, Salad, Curry, Paneer, Chana, Rajma
        if any(w in fn_lower for w in ["rice", "chawal", "dal", "daal", "poha", "upma", "oats", "khichdi", "sabzi", "shaak", "curry", "paneer", "chana", "rajma", "salad", "curd", "dahi", "sprouts", "દાળ", "ભાત", "ખીચડી", "શાક", "પોહા"]):
            if "poha" in fn_lower or "પોહા" in fn_lower:
                display_name = "poha"
            elif "upma" in fn_lower:
                display_name = "upma"
            elif "oats" in fn_lower:
                display_name = "oats"
            elif "rice" in fn_lower or "chawal" in fn_lower or "ભાત" in fn_lower:
                display_name = "rice"
            elif "dal" in fn_lower or "daal" in fn_lower or "દાળ" in fn_lower:
                display_name = "dal"
            else:
                display_name = fn_lower

            if lang in ["gu", "gu-Latn"]:
                return f"તમે કેટલું {display_name} ખાધું? (દા.ત. 1 વાટકી, 2 વાટકી)"
            elif lang in ["hi", "hi-Latn"]:
                return f"आपने कितना {display_name} खाया? (जैसे 1 कटोरी, 2 कटोरी)"
            return f"How much {display_name} did you have? (e.g. 1 bowl, 2 bowls)"

        # Generic fallback
        if lang in ["gu", "gu-Latn"]:
            return f"તમે કેટલું {fn_lower} લીધું? (દા.ત. 1 સર્વિંગ, 2 સર્વિંગ)"
        elif lang in ["hi", "hi-Latn"]:
            return f"आपने कितना {fn_lower} लिया? (जैसे 1 सर्विंग, 2 सर्विंग)"
        return f"How much {fn_lower} did you have? (e.g. 1 serving, 2 servings)"

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
        clean_norm = re.sub(r"[^\w\s]", " ", q).strip()
        clean_norm = re.sub(r"\s+", " ", clean_norm)
        for c_name, c_prof in CANONICAL_INDIAN_FOOD_PROFILES.items():
            c_norm = re.sub(r"[^\w\s]", " ", c_name.lower()).strip()
            c_norm = re.sub(r"\s+", " ", c_norm)
            if c_name.lower() in (clean_q, q) or c_norm in (clean_q, clean_norm):
                return {**c_prof, "is_recognized": True, "requires_clarification": False}

        # Step 1: Check known Indian dialect synonyms & slang map
        synonym_target = INDIAN_FOOD_SYNONYMS.get(clean_q) or INDIAN_FOOD_SYNONYMS.get(q)

        # Multi-word phrase matching with strict word boundaries before single tokens
        if not synonym_target:
            for food_key in sorted(INDIAN_FOOD_SYNONYMS.keys(), key=len, reverse=True):
                if any(ord(c) > 127 for c in food_key):
                    if food_key == clean_q or f" {food_key} " in f" {clean_q} " or food_key in clean_q.split():
                        synonym_target = INDIAN_FOOD_SYNONYMS[food_key]
                        break
                else:
                    if len(food_key) >= 3 and re.search(rf"\b{re.escape(food_key)}\b", clean_q, flags=re.I):
                        synonym_target = INDIAN_FOOD_SYNONYMS[food_key]
                        break

        # Check if synonym_target matches a canonical profile before token splitting
        if synonym_target and synonym_target in CANONICAL_INDIAN_FOOD_PROFILES:
            return {**CANONICAL_INDIAN_FOOD_PROFILES[synonym_target], "is_recognized": True, "requires_clarification": False}

        # Single tokens matching
        if not synonym_target:
            tokens = clean_q.split()
            for t in tokens:
                if t in INDIAN_FOOD_SYNONYMS:
                    synonym_target = INDIAN_FOOD_SYNONYMS[t]
                    break

        # If canonical profile matches, return immediately with accurate macros and food name
        if synonym_target and synonym_target in CANONICAL_INDIAN_FOOD_PROFILES:
            return {**CANONICAL_INDIAN_FOOD_PROFILES[synonym_target], "is_recognized": True, "requires_clarification": False}
        for c_name, c_prof in CANONICAL_INDIAN_FOOD_PROFILES.items():
            if c_name.lower() == clean_q or c_name.lower() == q:
                return {**c_prof, "is_recognized": True, "requires_clarification": False}

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
            # Protein Shake / Smoothie
            if re.search(r"\b(?:protein\s*shake|shake|smoothie)\b", search_term, re.I) or "પ્રોટીન શેક" in search_term or "प्रोटीन शेक" in search_term:
                return {**CANONICAL_INDIAN_FOOD_PROFILES["Protein Shake"], "is_recognized": True, "requires_clarification": False}
            # Protein Powder / Whey
            if re.search(r"\b(?:protein\s*powder|whey|protein)\b", search_term, re.I) or "પ્રોટીન પાવડર" in search_term or "प्रोटीन पाउडर" in search_term:
                return {**CANONICAL_INDIAN_FOOD_PROFILES["Whey Protein Powder"], "is_recognized": True, "requires_clarification": False}

            # Lemon Water
            if re.search(r"\b(?:lemon\s*water|nimbu\s*pani|leembu\s*pani)\b", search_term, re.I) or "લીંબુ પાણી" in search_term or "नींबू पानी" in search_term:
                return {**CANONICAL_INDIAN_FOOD_PROFILES["Lemon Water"], "is_recognized": True, "requires_clarification": False}
            # Pre Workout
            if re.search(r"\b(?:pre\s*workout|pre-workout|preworkout)\b", search_term, re.I):
                return {**CANONICAL_INDIAN_FOOD_PROFILES["Pre Workout"], "is_recognized": True, "requires_clarification": False}
            # Black Coffee
            if re.search(r"\b(?:black\s*coffee|black\s*cofee)\b", search_term, re.I):
                return {**CANONICAL_INDIAN_FOOD_PROFILES["Black Coffee"], "is_recognized": True, "requires_clarification": False}
            # Green Tea
            if re.search(r"\b(?:green\s*tea)\b", search_term, re.I):
                return {**CANONICAL_INDIAN_FOOD_PROFILES["Green Tea"], "is_recognized": True, "requires_clarification": False}
            # Khapli Roti
            if re.search(r"\b(?:khapli\s*roti|khapli\s*rotli|khapli)\b", search_term, re.I):
                return {**CANONICAL_INDIAN_FOOD_PROFILES["Khapli Roti"], "is_recognized": True, "requires_clarification": False}

            # Bhakri
            if any(re.search(rf"\b{re.escape(w)}\b", search_term, re.I) for w in ["bhakri", "bhakhri"]):
                return {**CANONICAL_INDIAN_FOOD_PROFILES["Bhakri"], "is_recognized": True, "requires_clarification": False}
            # Chai / Tea / Coffee
            if any(re.search(rf"\b{re.escape(w)}\b", search_term, re.I) for w in ["chai", "chay", "tea", "coffee"]):
                return {**CANONICAL_INDIAN_FOOD_PROFILES["Tea With Milk"], "is_recognized": True, "requires_clarification": False}
            # Rotlo / Bajra
            if any(re.search(rf"\b{re.escape(w)}\b", search_term, re.I) for w in ["rotlo", "rotla", "rotlu", "bajra", "bajri"]):
                return {**CANONICAL_INDIAN_FOOD_PROFILES["Rotlo"], "is_recognized": True, "requires_clarification": False}
            # Chapati
            if any(re.search(rf"\b{re.escape(w)}\b", search_term, re.I) for w in ["chapati", "chapatis", "chappati"]):
                return {**CANONICAL_INDIAN_FOOD_PROFILES["Chapati"], "is_recognized": True, "requires_clarification": False}
            # Phulka
            if any(re.search(rf"\b{re.escape(w)}\b", search_term, re.I) for w in ["phulka", "phulke", "phulkas"]):
                return {**CANONICAL_INDIAN_FOOD_PROFILES["Phulka"], "is_recognized": True, "requires_clarification": False}
            # Roti / Breads
            if any(re.search(rf"\b{re.escape(w)}\b", search_term, re.I) for w in ["roti", "rotli", "rotis", "rotlis", "khapli"]):
                return {**CANONICAL_INDIAN_FOOD_PROFILES["Roti"], "is_recognized": True, "requires_clarification": False}
            # Thepla
            if any(re.search(rf"\b{re.escape(w)}\b", search_term, re.I) for w in ["thepla", "theplas", "theple"]):
                return {**CANONICAL_INDIAN_FOOD_PROFILES["Methi Thepla"], "is_recognized": True, "requires_clarification": False}
            # Bananas / Fruits
            if any(re.search(rf"\b{re.escape(w)}\b", search_term, re.I) for w in ["banana", "kela", "keda", "kelu"]):
                return {**CANONICAL_INDIAN_FOOD_PROFILES["Banana"], "is_recognized": True, "requires_clarification": False}
            # Milk / Dairy
            if any(re.search(rf"\b{re.escape(w)}\b", search_term, re.I) for w in ["milk", "doodh", "dudh"]):
                return {**CANONICAL_INDIAN_FOOD_PROFILES["Cow Milk (Toned)"], "is_recognized": True, "requires_clarification": False}
            # Buttermilk / Chaas
            if any(re.search(rf"\b{re.escape(w)}\b", search_term, re.I) for w in ["chaas", "chhas", "chach", "buttermilk"]):
                return {**CANONICAL_INDIAN_FOOD_PROFILES["Spiced Buttermilk (Chaas)"], "is_recognized": True, "requires_clarification": False}
            # Rice / Chawal / Bhaat
            if any(re.search(rf"\b{re.escape(w)}\b", search_term, re.I) for w in ["rice", "chawal", "bhaat", "pulao", "khichdi"]):
                return {**CANONICAL_INDIAN_FOOD_PROFILES["Cooked White Rice"], "is_recognized": True, "requires_clarification": False}
            # Dal / Lentils
            if any(re.search(rf"\b{re.escape(w)}\b", search_term, re.I) for w in ["dal", "daal", "toor", "moong", "sambhar", "kadhi"]):
                return {**CANONICAL_INDIAN_FOOD_PROFILES["Toor Dal"], "is_recognized": True, "requires_clarification": False}
            # Sabzi / Vegetables
            if any(re.search(rf"\b{re.escape(w)}\b", search_term, re.I) for w in ["sabzi", "shaak", "shak", "bhindi", "aloo", "palak"]):
                return {**CANONICAL_INDIAN_FOOD_PROFILES["Mixed Vegetable Sabzi"], "is_recognized": True, "requires_clarification": False}
            # Eggs / Poultry
            if any(re.search(rf"\b{re.escape(w)}\b", search_term, re.I) for w in ["egg", "anda", "ande", "omelette"]):
                return {**CANONICAL_INDIAN_FOOD_PROFILES["Boiled Egg"], "is_recognized": True, "requires_clarification": False}

            # Generic fallback: UNKNOWN FOOD -> requires confirmation, do NOT invent fake calories or random food
            return {
                "food_id": f"unknown_{uuid.uuid4().hex[:8]}",
                "food_name": food_query.title().strip(),
                "calories": 0.0,
                "protein_g": 0.0,
                "carbs_g": 0.0,
                "fat_g": 0.0,
                "fiber_g": 0.0,
                "unit": "serving",
                "is_recognized": False,
                "requires_clarification": True,
                "clarification_reason": "UNKNOWN_FOOD",
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
            "is_recognized": True,
            "requires_clarification": False,
        }

    @staticmethod
    def calculate_portion_multiplier(
        base_unit: str,
        requested_unit: str,
        quantity: float,
        food_name: str = "",
    ) -> float:
        b_unit = (base_unit or "serving").lower().strip()
        r_unit = (requested_unit or "serving").lower().strip()
        qty = float(quantity) if quantity else 1.0
        f_lower = (food_name or "").lower().strip()

        # Same unit or default serving
        if r_unit == b_unit or r_unit in ["serving", "servings"]:
            return qty

        # Protein Powders / Supplements (base unit: scoop ~ 30g = ~120 kcal)
        if "scoop" in b_unit or any(w in f_lower for w in ["powder", "whey"]):
            if r_unit in ["tbsp", "tablespoon", "spoon", "chamach", "chamchi", "चम्मच", "ચમચી"]:
                # 1 tablespoon powder is ~10g -> 1/3 of a 30g scoop
                return (10.0 / 30.0) * qty
            if r_unit in ["tsp", "teaspoon"]:
                # 1 teaspoon powder is ~4g
                return (4.0 / 30.0) * qty
            if r_unit in ["g", "gram", "grams"]:
                return (qty / 30.0)
            if r_unit in ["scoop", "scoops"]:
                return qty

        # Protein Shakes / Smoothies / Drinks (base unit: glass ~ 250ml = 160 kcal)
        if any(w in f_lower for w in ["shake", "smoothie"]):
            if r_unit in ["tbsp", "tablespoon", "spoon", "chamach", "chamchi", "चम्मच", "ચમચી"]:
                # 1 spoon of protein shake concentrate (~45 kcal vs 160 kcal full glass)
                return (45.0 / 160.0) * qty
            if r_unit in ["tsp", "teaspoon"]:
                return (15.0 / 160.0) * qty
            if r_unit in ["glass", "glasses"]:
                return qty
            if r_unit in ["cup", "cups"]:
                return (150.0 / 250.0) * qty
            if r_unit in ["ml"]:
                return (qty / 250.0)
            if r_unit in ["l", "liter", "litre"]:
                return (qty * 1000.0 / 250.0)

        # Liquids: Milk, Chaas, Water (base unit: glass or cup)
        if b_unit in ["glass", "cup"] or any(w in f_lower for w in ["milk", "chaas", "doodh", "water", "tea", "coffee"]):
            base_ml = 250.0 if b_unit == "glass" else 150.0
            if r_unit in ["ml"]:
                return (qty / base_ml)
            if r_unit in ["l", "liter", "litre"]:
                return (qty * 1000.0 / base_ml)
            if r_unit in ["cup", "cups"]:
                return (150.0 / base_ml) * qty
            if r_unit in ["glass", "glasses"]:
                return (250.0 / base_ml) * qty
            if r_unit in ["tbsp", "spoon", "tablespoon"]:
                return (15.0 / base_ml) * qty

        # Bowls: Dal, Sabzi, Rice, Khichdi, Kadhi (base unit: bowl ~ 150g)
        if b_unit in ["bowl", "katori", "vatki"]:
            if r_unit in ["bowl", "katori", "vatki"]:
                return qty
            if r_unit in ["plate", "dish"]:
                return 2.0 * qty
            if r_unit in ["tbsp", "spoon", "tablespoon"]:
                return 0.1 * qty
        # Pieces: Roti, Chapati, Thepla, Bhakri, Eggs, Fruits (base unit: piece)
        if b_unit in ["piece", "nag", "slice"]:
            if r_unit in ["piece", "pieces", "nag", "slice", "slices"]:
                return qty
            if r_unit in ["plate"]:
                return 2.0 * qty

        return qty

    @staticmethod
    async def process_and_log_food(
        user_id: str,
        items: List[FoodItemInput],
        meal_type_override: Optional[str] = None,
        log_date_str: Optional[str] = None,
    ) -> FoodLoggingResult:
        db = get_db()
        local_now = TimeService.get_current_local_time()
        now = datetime.now(timezone.utc)
        target_date_str = log_date_str or local_now.strftime("%Y-%m-%d")

        # Pre-resolution and clarification validation
        unrecognized_items = []
        ambiguous_qty_items = []
        validated_items = []

        for item in items:
            # Check heuristic extraction flags
            is_recog = getattr(item, "is_recognized", True)
            has_qty = getattr(item, "has_explicit_quantity", True)
            req_clar = getattr(item, "requires_clarification", False)

            resolved = await FoodService.resolve_food(item.food)
            if not is_recog or not resolved.get("is_recognized", True) or (req_clar and getattr(item, "clarification_reason", "") == "UNKNOWN_FOOD"):
                unrecognized_items.append(item.food)
            elif req_clar and getattr(item, "clarification_reason", "") == "AMBIGUOUS_QUANTITY":
                ambiguous_qty_items.append(resolved.get("food_name", item.food))
            else:
                if not item.quantity or item.quantity <= 0:
                    item.quantity = 1.0
                if not item.unit or item.unit == "serving":
                    item.unit = resolved.get("unit") or "serving"
                validated_items.append((item, resolved))

        # If NO items were validated and there are unrecognized/ambiguous items, return clarification immediately
        if not validated_items and (unrecognized_items or ambiguous_qty_items):
            clarif_parts = []
            if unrecognized_items:
                names = ", ".join(f"'{n}'" for n in unrecognized_items)
                clarif_parts.append(f"I couldn't identify the food {names}. Could you please confirm the exact food name?")
            if ambiguous_qty_items:
                questions = [FoodService.get_quantity_clarification_question(n) for n in ambiguous_qty_items]
                clarif_parts.extend(questions)

            msg = " ".join(clarif_parts)
            summary_result = await FoodService.get_daily_grouped_food_cards(user_id, target_date_str)
            return FoodLoggingResult(
                success=False,
                requiresClarification=True,
                clarificationQuestion=msg,
                replyText=msg,
                loggedItems=[],
                groupedFoodCards=[],
                currentGroupedFoodCards=[],
                dailyNutritionSummary=summary_result["dailyNutritionSummary"],
                mealTotals={"calories": 0.0, "proteinG": 0.0, "carbsG": 0.0, "fatG": 0.0, "fiberG": 0.0},
                dailyProgress={
                    "totalCaloriesLoggedToday": summary_result["dailyNutritionSummary"].totalCalories,
                    "dailyCalorieTarget": summary_result["dailyNutritionSummary"].targetCalories,
                    "remainingCalories": summary_result["dailyNutritionSummary"].remainingCalories,
                },
            )

        logged_items = []
        total_meal_cal = 0.0
        total_meal_p = 0.0
        total_meal_c = 0.0
        total_meal_f = 0.0
        total_meal_fib = 0.0

        for item, resolved in validated_items:
            qty = float(item.quantity)
            unit = item.unit or resolved.get("unit", "serving")

            # Resolve timestamp and whether explicit time was given
            item_logged_at = local_now
            has_explicit_time = bool(getattr(item, "has_explicit_time", False))

            if getattr(item, "raw_text", None):
                ext_dt, has_ext = TimeService.extract_time_from_text(item.raw_text, reference_time=local_now)
                if has_ext:
                    item_logged_at = ext_dt
                    has_explicit_time = True
            elif getattr(item, "logged_at", None):
                if isinstance(item.logged_at, datetime):
                    item_logged_at = item.logged_at
                else:
                    try:
                        item_logged_at = datetime.fromisoformat(str(item.logged_at).replace("Z", "+00:00"))
                    except Exception:
                        ext_dt, has_ext = TimeService.extract_time_from_text(str(item.logged_at), reference_time=local_now)
                        if has_ext:
                            item_logged_at = ext_dt
                            has_explicit_time = True

            # Resolve meal type:
            # A. If user explicitly specified meal type (override or contextual time)
            # B. If absent, strictly "—" (NEVER clock meal)
            raw_text_to_check = getattr(item, "raw_text", None) or item.food or ""
            inferred_m = TimeService.infer_meal_type(raw_text_to_check, dt=item_logged_at if has_explicit_time else None)

            if meal_type_override and meal_type_override != "—":
                item_meal_type = meal_type_override
            elif inferred_m and inferred_m != "—":
                item_meal_type = inferred_m
            else:
                item_meal_type = "—"

            item_date_str = item_logged_at.strftime("%Y-%m-%d") if item_logged_at else target_date_str

            multiplier = FoodService.calculate_portion_multiplier(
                base_unit=resolved.get("unit", "serving"),
                requested_unit=unit,
                quantity=qty,
                food_name=resolved.get("food_name", ""),
            )

            item_cal = round(resolved["calories"] * multiplier, 1)
            item_p = round(resolved["protein_g"] * multiplier, 1)
            item_c = round(resolved["carbs_g"] * multiplier, 1)
            item_f = round(resolved["fat_g"] * multiplier, 1)
            item_fib = round(resolved["fiber_g"] * multiplier, 1)

            # Idempotency check: prevent duplicate entry within 5 seconds for same food, qty, and timestamp
            five_sec_ago = datetime.fromtimestamp(now.timestamp() - 5, timezone.utc)
            dup_query = {
                "user_id": user_id,
                "food_id": resolved["food_id"],
                "quantity_amount": qty,
                "created_at": {"$gte": five_sec_ago},
            }
            if item_logged_at:
                dup_query["logged_at"] = item_logged_at
            duplicate = await db.daily_food_logs.find_one(dup_query)

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
                    "log_date": item_date_str,
                    "created_at": now,
                    "logged_at": item_logged_at,
                    "has_explicit_time": has_explicit_time,
                }
                await db.daily_food_logs.insert_one(log_doc)

            clean_log = {**log_doc, "id": str(log_doc.get("id") or log_doc.get("_id"))}
            clean_log["food"] = clean_log.get("food_name")
            clean_log["has_explicit_time"] = has_explicit_time
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

        # Fetch user target calories
        user = await db.users.find_one({"id": user_id}) or await db.users.find_one({"user_id": user_id}) or {}
        profile = user.get("profile") or {}
        target_calories = profile.get("dailyCalorieTarget", 2000)

        # Current grouped cards (ONLY items logged in this transaction)
        current_cards_res = FoodService.group_food_logs(logged_items, target_calories, target_date_str)
        current_grouped_cards = current_cards_res["groupedFoodCards"]

        # Full day's logs for dashboard/dailyNutritionSummary
        summary_result = await FoodService.get_daily_grouped_food_cards(user_id, target_date_str)

        if not logged_items:
            return FoodLoggingResult(
                success=True,
                requiresClarification=False,
                replyText="No food items were logged because quantity was zero or missing.",
                loggedItems=[],
                groupedFoodCards=[],
                currentGroupedFoodCards=[],
                dailyNutritionSummary=summary_result["dailyNutritionSummary"],
                mealTotals={"calories": 0.0, "proteinG": 0.0, "carbsG": 0.0, "fatG": 0.0, "fiberG": 0.0},
                dailyProgress={
                    "totalCaloriesLoggedToday": summary_result["dailyNutritionSummary"].totalCalories,
                    "dailyCalorieTarget": summary_result["dailyNutritionSummary"].targetCalories,
                    "remainingCalories": summary_result["dailyNutritionSummary"].remainingCalories,
                },
            )

        items_parts = []
        for inp_item, l in zip([it for it, _ in validated_items], logged_items):
            qty_val = int(l['quantity_amount']) if l['quantity_amount'].is_integer() else l['quantity_amount']
            raw_q = (inp_item.food or "").strip()
            unit_str = (l['quantity_unit'] or "").strip()
            food_name = (l['food_name'] or "Food").strip()
            cal_str = f"({int(l['calories'])} kcal)"

            if unit_str.lower() in ["piece", "pieces", "nag", "unit", "serving"]:
                if raw_q and raw_q.lower() != food_name.lower() and raw_q.lower() not in food_name.lower():
                    items_parts.append(f"{qty_val} {food_name} ({raw_q}) {cal_str}")
                else:
                    items_parts.append(f"{qty_val} {food_name} {cal_str}")
            else:
                if raw_q and raw_q.lower() != food_name.lower() and raw_q.lower() not in food_name.lower():
                    items_parts.append(f"{qty_val} {unit_str} {food_name} ({raw_q}) {cal_str}")
                else:
                    items_parts.append(f"{qty_val} {unit_str} {food_name} {cal_str}")

        bullet_items = "\n".join(f"* {part}" for part in items_parts)
        m_type = logged_items[0].get("meal_type") or "—"
        effective_meal_title = m_type if m_type == "—" else m_type.title()
        reply_text = (
            f"🍽️ **Food Logged**\n\n"
            f"{bullet_items}\n\n"
            f"Meal total ({effective_meal_title}): {int(total_meal_cal)} kcal (P: {int(total_meal_p)}g, C: {int(total_meal_c)}g, F: {int(total_meal_f)}g)\n"
            f"Today's total: {int(summary_result['dailyNutritionSummary'].totalCalories)} / {int(summary_result['dailyNutritionSummary'].targetCalories)} kcal"
        )

        # Append clarification question for partial items if any
        has_partial_issues = bool(unrecognized_items or ambiguous_qty_items)
        clarification_msg = None
        if has_partial_issues:
            issues = []
            if unrecognized_items:
                u_names = ", ".join(f"'{n}'" for n in unrecognized_items)
                issues.append(f"I couldn't identify {u_names}. Could you please confirm the exact food name?")
            if ambiguous_qty_items:
                questions = [FoodService.get_quantity_clarification_question(n) for n in ambiguous_qty_items]
                issues.extend(questions)
            clarification_msg = "\n\n" + "\n".join(issues)
            reply_text += f"\n\n⚠️ {clarification_msg.strip()}"

        return FoodLoggingResult(
            success=True,
            requiresClarification=has_partial_issues,
            clarificationQuestion=clarification_msg,
            loggedItems=logged_items,
            groupedFoodCards=current_grouped_cards,
            currentGroupedFoodCards=current_grouped_cards,
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
        target_unit = unit or (existing.get("quantity_unit") if existing else resolved.get("unit", "serving"))

        multiplier = FoodService.calculate_portion_multiplier(
            base_unit=resolved.get("unit", "serving"),
            requested_unit=target_unit,
            quantity=qty,
            food_name=resolved.get("food_name", ""),
        )

        item_cal = round(resolved["calories"] * multiplier, 1)
        item_p = round(resolved["protein_g"] * multiplier, 1)
        item_c = round(resolved["carbs_g"] * multiplier, 1)
        item_f = round(resolved["fat_g"] * multiplier, 1)
        item_fib = round(resolved["fiber_g"] * multiplier, 1)

        if existing:
            await db.daily_food_logs.update_one(
                {"id": existing["id"]},
                {"$set": {
                    "food_name": target_food_name,
                    "food_id": resolved["food_id"],
                    "quantity_amount": qty,
                    "quantity_unit": target_unit,
                    "calories": item_cal,
                    "protein_g": item_p,
                    "carbs_g": item_c,
                    "fat_g": item_f,
                    "fiber_g": item_fib,
                    "updated_at": now,
                }}
            )
            reply = f"Updated {target_food_name} to {int(qty) if qty.is_integer() else qty} {target_unit} ({int(item_cal)} kcal)."
        else:
            # If not found, log it afresh
            return await FoodService.process_and_log_food(
                user_id,
                [FoodItemInput(food=target_food, quantity=qty, unit=target_unit)],
                log_date_str=target_date_str,
            )

        summary_result = await FoodService.get_daily_grouped_food_cards(user_id, target_date_str)
        return FoodLoggingResult(
            success=True,
            requiresClarification=False,
            loggedItems=[],
            groupedFoodCards=summary_result["groupedFoodCards"],
            currentGroupedFoodCards=summary_result["groupedFoodCards"],
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
            currentGroupedFoodCards=summary_result["groupedFoodCards"],
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
    async def sync_food_log_to_conversation_messages(
        user_id: str,
        log_id: str,
        updated_entry: Optional[Dict[str, Any]] = None,
        is_deleted: bool = False,
    ) -> None:
        """
        Synchronizes food log updates or deletions to all conversation messages containing this log ID.
        Ensures page refreshes, session reloads, and multi-tab sync never revert to stale data.
        """
        db = get_db()
        cursor = db.conversation_messages.find({"raw_entities": {"$ne": None}})
        messages = await cursor.to_list(length=500)

        for m in messages:
            raw_ent = m.get("raw_entities")
            if not isinstance(raw_ent, dict):
                continue
            grouped_cards = raw_ent.get("groupedFoodCards")
            if not grouped_cards or not isinstance(grouped_cards, list):
                continue

            card_modified = False
            new_cards = []

            for card in grouped_cards:
                entries = card.get("entries", [])
                new_entries = []
                for entry in entries:
                    entry_id = str(entry.get("id") or "")
                    if entry_id == str(log_id):
                        card_modified = True
                        if is_deleted:
                            continue  # drop deleted entry
                        elif updated_entry:
                            dt = updated_entry.get("logged_at") or updated_entry.get("created_at") or datetime.now(timezone.utc)
                            has_exp = updated_entry.get("has_explicit_time", False)
                            tf = FoodService.format_time(dt) if has_exp else ""
                            new_entries.append({
                                **entry,
                                "foodName": updated_entry.get("food_name"),
                                "foodMasterId": updated_entry.get("food_id"),
                                "quantity": updated_entry.get("quantity_amount"),
                                "unit": updated_entry.get("quantity_unit"),
                                "calories": updated_entry.get("calories"),
                                "mealType": updated_entry.get("meal_type", "—"),
                                "timeFormatted": tf,
                                "macros": {
                                    "proteinG": updated_entry.get("protein_g", 0.0),
                                    "carbsG": updated_entry.get("carbs_g", 0.0),
                                    "fatG": updated_entry.get("fat_g", 0.0),
                                    "fiberG": updated_entry.get("fiber_g", 0.0),
                                },
                            })
                    else:
                        new_entries.append(entry)

                if new_entries:
                    total_qty = sum(float(e.get("quantity", 0)) for e in new_entries)
                    total_cal = sum(float(e.get("calories", 0)) for e in new_entries)
                    total_p = sum(float(e.get("macros", {}).get("proteinG", 0)) for e in new_entries)
                    total_c = sum(float(e.get("macros", {}).get("carbsG", 0)) for e in new_entries)
                    total_f = sum(float(e.get("macros", {}).get("fatG", 0)) for e in new_entries)
                    total_fib = sum(float(e.get("macros", {}).get("fiberG", 0)) for e in new_entries)

                    first_entry = new_entries[0]
                    new_cards.append({
                        **card,
                        "foodName": first_entry.get("foodName", card.get("foodName")),
                        "foodMasterId": first_entry.get("foodMasterId", card.get("foodMasterId")),
                        "foodKey": f"food_{first_entry.get('foodMasterId') or first_entry.get('foodName', '').lower()}",
                        "icon": FoodService.resolve_food_icon(first_entry.get("foodName", "")),
                        "totalQuantity": int(total_qty) if total_qty.is_integer() else round(total_qty, 1),
                        "totalCalories": round(total_cal),
                        "entryCount": len(new_entries),
                        "unit": first_entry.get("unit", card.get("unit")),
                        "macros": {
                            "proteinG": round(total_p, 1),
                            "carbsG": round(total_c, 1),
                            "fatG": round(total_f, 1),
                            "fiberG": round(total_fib, 1),
                        },
                        "entries": new_entries,
                    })

            if card_modified:
                raw_ent["groupedFoodCards"] = new_cards
                # Refresh daily summary
                log_date = TimeService.get_current_local_date_str()
                if updated_entry and updated_entry.get("log_date"):
                    log_date = updated_entry["log_date"]
                daily_sum_res = await FoodService.get_daily_grouped_food_cards(user_id, log_date)
                raw_ent["dailyNutritionSummary"] = daily_sum_res["dailyNutritionSummary"].model_dump()

                # Update message text if it has bullet items
                if new_cards:
                    bullet_items = []
                    for c in new_cards:
                        for e in c.get("entries", []):
                            q_val = int(e["quantity"]) if float(e["quantity"]).is_integer() else e["quantity"]
                            bullet_items.append(f"* {q_val} {e['unit']} {e['foodName']} ({int(e['calories'])} kcal)")
                    b_str = "\n".join(bullet_items)
                    m_type = new_cards[0]["entries"][0].get("mealType") or "—"
                    meal_title = m_type if m_type == "—" else m_type.title()
                    tot_cal = sum(float(c.get("totalCalories", 0)) for c in new_cards)
                    d_sum = raw_ent["dailyNutritionSummary"]
                    new_msg_text = (
                        f"🍽️ **Food Logged**\n\n"
                        f"{b_str}\n\n"
                        f"Meal total ({meal_title}): {int(tot_cal)} kcal\n"
                        f"Today's total: {int(d_sum.get('totalCalories', tot_cal))} / {int(d_sum.get('targetCalories', 2000))} kcal"
                    )
                else:
                    new_msg_text = "All logged items for this meal were removed."

                await db.conversation_messages.update_one(
                    {"id": m["id"]},
                    {"$set": {"raw_entities": raw_ent, "message": new_msg_text}}
                )

    @staticmethod
    def group_food_logs(logs: List[Dict[str, Any]], target_calories: float = 2000.0, date_str: str = "") -> Dict[str, Any]:
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
            has_exp_time = log.get("has_explicit_time", False)
            time_formatted = FoodService.format_time(dt) if has_exp_time else ""
            meal_type = log.get("meal_type") or "—"

            g["entries"].append(
                FoodLogEntrySummary(
                    id=str(log.get("id") or log.get("_id")),
                    foodMasterId=log.get("food_id"),
                    foodName=log.get("food_name"),
                    quantity=qty,
                    unit=log.get("quantity_unit", "serving"),
                    calories=round(cal, 1),
                    loggedAt=dt.isoformat() if hasattr(dt, "isoformat") else str(dt),
                    timeFormatted=time_formatted,
                    hasExplicitTime=bool(has_exp_time),
                    mealType=meal_type,
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

    @staticmethod
    async def get_daily_grouped_food_cards(user_id: str, date_str: str) -> Dict[str, Any]:
        db = get_db()
        cursor = db.daily_food_logs.find({"user_id": user_id, "log_date": date_str}).sort("created_at", 1)
        logs = await cursor.to_list(length=500)

        # Fetch user target calories
        user = await db.users.find_one({"id": user_id}) or await db.users.find_one({"user_id": user_id}) or {}
        profile = user.get("profile") or {}
        target_calories = profile.get("dailyCalorieTarget", 2000)

        return FoodService.group_food_logs(logs, target_calories, date_str)

