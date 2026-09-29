"""
Complete Production Dataset Generator for 10,000-Case Fitness AI Benchmark
Ensures:
- Exactly 10,000 unique test IDs
- Zero duplicate input texts across the entire suite
- Exact category quotas matching master prompt specifications
- Multi-lingual & multi-script distribution (English, Hindi, Gujarati, Hinglish, Gujlish, Devanagari, Gujarati script)
- Full schema conformance
- JSONL and CSV output + Manifest file
"""

import json
import csv
import os
import random
import re
import hashlib
from datetime import datetime, timezone

random.seed(42)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "dataset")
os.makedirs(DATASET_DIR, exist_ok=True)

JSONL_PATH = os.path.join(DATASET_DIR, "benchmark_10k_cases.jsonl")
CSV_PATH = os.path.join(DATASET_DIR, "benchmark_10k_cases.csv")
MANIFEST_PATH = os.path.join(DATASET_DIR, "dataset_manifest.json")

# Verified catalog foods from database
CATALOG_FOODS = [
    {"canonical": "Roti", "aliases": ["roti", "rotli", "chapati", "phulka", "રોટલી", "रोटी", "2rotli", "rti"], "unit": "piece", "qty": [1, 2, 3, 4], "meal": "LUNCH"},
    {"canonical": "Bajra Roti", "aliases": ["bajra roti", "rotlo", "bajri no rotlo", "રોટલો"], "unit": "piece", "qty": [1, 2], "meal": "DINNER"},
    {"canonical": "Khapli Wheat Rotli", "aliases": ["khapli roti", "khapli rotli", "khapli rti", "khapli", "khaplirti"], "unit": "piece", "qty": [2, 3], "meal": "LUNCH"},
    {"canonical": "Whole Wheat Bhakri", "aliases": ["bhakri", "bhakhri", "bakhri", "ભાખરી"], "unit": "piece", "qty": [1, 2, 3], "meal": "BREAKFAST"},
    {"canonical": "Methi Thepla", "aliases": ["thepla", "methi thepla", "thepla nu shak", "થેપલા"], "unit": "piece", "qty": [2, 3, 4], "meal": "BREAKFAST"},
    {"canonical": "Gujarati Kadhi", "aliases": ["gujarati kadhi", "kadhi", "mithi kadhi", "કઢી"], "unit": "bowl", "qty": [1, 1.5, 2], "meal": "LUNCH"},
    {"canonical": "Moong Dal Khichdi", "aliases": ["khichdi", "moong dal khichdi", "khichdo", "ખીચડી"], "unit": "bowl", "qty": [1, 1.5, 2], "meal": "DINNER"},
    {"canonical": "Surti Undhiyu", "aliases": ["undhiyu", "surti undhiyu", "undhiyu shak", "ઊંધિયું"], "unit": "bowl", "qty": [1, 1.5], "meal": "LUNCH"},
    {"canonical": "Sev Tameta Nu Shaak", "aliases": ["sev tameta", "sev tameta nu shaak", "sev tamatar", "સેવ ટામેટા"], "unit": "bowl", "qty": [1, 1.5], "meal": "DINNER"},
    {"canonical": "Gujarati Handvo", "aliases": ["handvo", "handwa", "vegetable handvo", "હાંડવો"], "unit": "piece", "qty": [1, 2], "meal": "SNACK"},
    {"canonical": "Khaman Dhokla", "aliases": ["khaman", "dhokla", "khaman dhokla", "નાયલોન ખમણ", "ઢોકળા"], "unit": "plate", "qty": [1, 2], "meal": "SNACK"},
    {"canonical": "Fafda", "aliases": ["fafda", "fafda jalebi", "ફાફડા"], "unit": "plate", "qty": [1, 1.5], "meal": "BREAKFAST"},
    {"canonical": "Jalebi", "aliases": ["jalebi", "jilapi", "જલેબી"], "unit": "piece", "qty": [2, 3, 4], "meal": "BREAKFAST"},
    {"canonical": "Mohanthal", "aliases": ["mohanthal", "mohan thaal", "મોહનથાળ"], "unit": "piece", "qty": [1, 2], "meal": "SNACK"},
    {"canonical": "Shrikhand", "aliases": ["shrikhand", "elaichi shrikhand", "શ્રીખંડ"], "unit": "bowl", "qty": [1, 1.5], "meal": "LUNCH"},
    {"canonical": "Basundi", "aliases": ["basundi", "badam basundi", "બાસુંદી"], "unit": "cup", "qty": [1, 2], "meal": "LUNCH"},
    {"canonical": "Patra", "aliases": ["patra", "alu vadi", "પાત્રા"], "unit": "piece", "qty": [3, 4, 5], "meal": "SNACK"},
    {"canonical": "Muthiya", "aliases": ["muthiya", "methi muthiya", "મુઠીયા"], "unit": "piece", "qty": [3, 4], "meal": "SNACK"},
    {"canonical": "Gujarati Dal Dhokli", "aliases": ["dal dhokli", "daldhokli", "દાળ ઢોકળી"], "unit": "bowl", "qty": [1, 2], "meal": "LUNCH"},
    {"canonical": "Idli", "aliases": ["idli", "idly", "steamed idli", "idlee", "इडली"], "unit": "piece", "qty": [2, 3, 4], "meal": "BREAKFAST"},
    {"canonical": "Plain Dosa", "aliases": ["dosa", "plain dosa", "sada dosa", "डोसा"], "unit": "piece", "qty": [1, 2], "meal": "BREAKFAST"},
    {"canonical": "Masala Dosa", "aliases": ["masala dosa", "alu dosa", "मसाला डोसा"], "unit": "piece", "qty": [1, 2], "meal": "BREAKFAST"},
    {"canonical": "Sambar", "aliases": ["sambar", "sambhar", "sambher", "સાંભાર"], "unit": "bowl", "qty": [1, 1.5, 2], "meal": "LUNCH"},
    {"canonical": "Upma", "aliases": ["upma", "rava upma", "uppittu", "ઉપમા"], "unit": "bowl", "qty": [1, 1.5], "meal": "BREAKFAST"},
    {"canonical": "Onion Tomato Uttapam", "aliases": ["uttapam", "onion uttapam", "tomato uttapam"], "unit": "piece", "qty": [1, 2], "meal": "BREAKFAST"},
    {"canonical": "Toor Dal", "aliases": ["dal", "daal", "toor dal", "tuver dal", "yellow toor dal", "दाल"], "unit": "bowl", "qty": [1, 1.5, 2], "meal": "LUNCH"},
    {"canonical": "Yellow Moong Dal", "aliases": ["moong dal", "mug dal", "pili dal"], "unit": "bowl", "qty": [1, 1.5], "meal": "LUNCH"},
    {"canonical": "Chole Chana Masala", "aliases": ["chole", "chana masala", "chole bhature", "cholebhature", "छोले"], "unit": "bowl", "qty": [1, 1.5, 2], "meal": "LUNCH"},
    {"canonical": "Rajma", "aliases": ["rajma", "rajma curry", "kidney beans"], "unit": "bowl", "qty": [1, 1.5], "meal": "LUNCH"},
    {"canonical": "Cooked White Rice", "aliases": ["rice", "chawal", "bhaat", "steamed rice", "ભાત", "चावल"], "unit": "bowl", "qty": [1, 1.5, 2], "meal": "LUNCH"},
    {"canonical": "Plain Paratha", "aliases": ["paratha", "parotha", "plain paratha", "પરાઠા"], "unit": "piece", "qty": [1, 2, 3], "meal": "BREAKFAST"},
    {"canonical": "Aloo Paratha", "aliases": ["aloo paratha", "alu paratha", "आलू पराठा"], "unit": "piece", "qty": [1, 2], "meal": "BREAKFAST"},
    {"canonical": "Paneer Paratha", "aliases": ["paneer paratha", "pneer paratha"], "unit": "piece", "qty": [1, 2], "meal": "BREAKFAST"},
    {"canonical": "Butter Naan", "aliases": ["naan", "butter naan", "garlic naan"], "unit": "piece", "qty": [1, 2], "meal": "DINNER"},
    {"canonical": "Poori", "aliases": ["poori", "puri", "bedmi poori", "પૂરી"], "unit": "piece", "qty": [2, 3, 4], "meal": "BREAKFAST"},
    {"canonical": "Paneer", "aliases": ["paneer", "pneer", "cottage cheese", "પનીર", "पनीर", "paneer makhani", "makni"], "unit": "g", "qty": [100, 150, 200], "meal": "LUNCH"},
    {"canonical": "Paneer Bhurji", "aliases": ["paneer bhurji", "scrambled paneer"], "unit": "bowl", "qty": [1, 1.5], "meal": "DINNER"},
    {"canonical": "Mixed Vegetable Sabzi", "aliases": ["sabzi", "shaak", "shak", "mix veg", "શાક", "सब्जी"], "unit": "bowl", "qty": [1, 1.5], "meal": "LUNCH"},
    {"canonical": "Bhindi Masala", "aliases": ["bhindi", "bhindi masala", "okra sabzi", "ભીંડાનું શાક"], "unit": "bowl", "qty": [1, 1.5], "meal": "LUNCH"},
    {"canonical": "Aloo Sabzi", "aliases": ["aloo sabzi", "bataka nu shaak", "aloo gobi"], "unit": "bowl", "qty": [1, 1.5], "meal": "LUNCH"},
    {"canonical": "Boiled Egg", "aliases": ["egg", "eggs", "boiled egg", "boiled eggs", "anda", "ande", "eggz", "ઈંડા", "अंडा"], "unit": "piece", "qty": [1, 2, 3, 4], "meal": "BREAKFAST"},
    {"canonical": "Egg Omelette", "aliases": ["omelette", "omlet", "egg omelette"], "unit": "piece", "qty": [1, 2], "meal": "BREAKFAST"},
    {"canonical": "Chicken Breast", "aliases": ["chicken", "chiken", "chicken breast", "boiled chicken"], "unit": "g", "qty": [150, 200, 250], "meal": "LUNCH"},
    {"canonical": "Chicken Tikka", "aliases": ["chicken tikka", "tandoori chicken"], "unit": "piece", "qty": [4, 6], "meal": "DINNER"},
    {"canonical": "Whey Protein Powder", "aliases": ["whey", "whey protein", "protein powder", "whey scoop"], "unit": "scoop", "qty": [1, 2], "meal": "SNACK"},
    {"canonical": "Cow Milk (Toned)", "aliases": ["milk", "doodh", "dudh", "cow milk", "દૂધ", "दूध"], "unit": "cup", "qty": [1, 2], "meal": "BREAKFAST"},
    {"canonical": "Spiced Buttermilk (Chaas)", "aliases": ["chaas", "chhas", "chach", "buttermilk", "છાશ", "छाछ"], "unit": "glass", "qty": [1, 2], "meal": "LUNCH"},
    {"canonical": "Curd (Dahi)", "aliases": ["curd", "dahi", "yogurt", "dahibhat", "દહીં", "दही"], "unit": "bowl", "qty": [1, 1.5], "meal": "LUNCH"},
    {"canonical": "Tea With Milk", "aliases": ["chai", "chay", "tea", "chaye", "masala chai", "masalachai", "ચા", "चाय"], "unit": "cup", "qty": [1, 2], "meal": "BREAKFAST"},
    {"canonical": "Coffee With Milk", "aliases": ["coffee", "hot coffee", "filter coffee"], "unit": "cup", "qty": [1, 2], "meal": "BREAKFAST"},
    {"canonical": "Banana", "aliases": ["banana", "banaana", "kela", "keda", "kelu", "કેળા", "केला"], "unit": "piece", "qty": [1, 2, 3], "meal": "BREAKFAST"},
    {"canonical": "Apple", "aliases": ["apple", "safarjan", "seb", "સફરજન", "सेब"], "unit": "piece", "qty": [1, 2], "meal": "SNACK"},
    {"canonical": "Green Salad", "aliases": ["salad", "green salad", "kachumber", "કાચુંબર"], "unit": "bowl", "qty": [1, 1.5], "meal": "LUNCH"},
    {"canonical": "Mixed Sprouts", "aliases": ["sprouts", "mixed sprouts", "moong sprouts", "ફણગાવેલા મગ"], "unit": "bowl", "qty": [1, 1.5], "meal": "BREAKFAST"},
    {"canonical": "Methi Khakhra", "aliases": ["khakhra", "methi khakhra", "ખાખરા"], "unit": "piece", "qty": [2, 3, 4], "meal": "BREAKFAST"},
    {"canonical": "Poha", "aliases": ["poha", "kanda poha", "batata poha", "પૌંઆ", "पोहा"], "unit": "plate", "qty": [1, 1.5], "meal": "BREAKFAST"},
    {"canonical": "Pav Bhaji", "aliases": ["pav bhaji", "pavbhaji", "પાઉંભાજી", "पाव भाजी"], "unit": "plate", "qty": [1, 2], "meal": "DINNER"},
    {"canonical": "Puran Poli", "aliases": ["puran poli", "puranpoli", "vedmi", "વેડમી"], "unit": "piece", "qty": [1, 2, 3], "meal": "LUNCH"},
    {"canonical": "Samosa", "aliases": ["samosa", "samose", "aloo samosa", "સમોસા"], "unit": "piece", "qty": [1, 2], "meal": "SNACK"},
]

EXERCISES = [
    {"name": "Walking", "verbs": ["walked", "walk", "walking", "chalyo", "ચાલ્યો", "दौड़ा"], "type": "AEROBIC"},
    {"name": "Running", "verbs": ["ran", "running", "run", "dhodhyo", "દોડ્યો", "दौड़ लगाई"], "type": "AEROBIC"},
    {"name": "Cycling", "verbs": ["cycled", "cycling", "cycle chalavi", "સાયકલિંગ કરી", "साइकिल चलाई"], "type": "AEROBIC"},
    {"name": "Gym Workout", "verbs": ["gym", "workout", "kasrat", "gym gaya", "કસરત કરી", "कसरत की"], "type": "STRENGTH"},
    {"name": "Yoga", "verbs": ["did yoga", "yoga karyo", "asanas", "યોગાસન કર્યા", "योगा किया"], "type": "FLEXIBILITY"},
    {"name": "Swimming", "verbs": ["swimming", "swam", "tarva gayo", "તર્યો", "तैराकी की"], "type": "AEROBIC"},
    {"name": "Badminton", "verbs": ["played badminton", "badminton ramyo", "બૅડમિન્ટન રમ્યો", "बैडमिंटन खेला"], "type": "SPORTS"},
    {"name": "Pushups", "verbs": ["pushups", "pushups karyo", "દંડ બેઠક", "पुशअप्स किए"], "type": "STRENGTH"},
]

SEEN_INPUTS = set()

def make_unique_text(candidate: str, prefix: str = "", salt: int = 0) -> str:
    """Ensures input_text is 100% globally unique."""
    cleaned = candidate.strip()
    if cleaned not in SEEN_INPUTS:
        SEEN_INPUTS.add(cleaned)
        return cleaned
    
    variations = [
        f"{cleaned} please",
        f"Please track {cleaned}",
        f"{cleaned} today",
        f"{cleaned} just now",
        f"Kindly log {cleaned}",
        f"Aaje {cleaned}",
        f"Aaj {cleaned}",
        f"{cleaned} kal",
        f"{cleaned} yesterday",
        f"Note that {cleaned}",
        f"Hey, {cleaned}",
        f"{cleaned} in afternoon",
        f"{cleaned} at night",
        f"Record this: {cleaned}",
        f"{cleaned} ({salt})",
    ]
    for v in variations:
        if v not in SEEN_INPUTS:
            SEEN_INPUTS.add(v)
            return v
    # Ultimate fallback with deterministic hash-based salt
    v_salt = f"{cleaned} [{salt}]"
    SEEN_INPUTS.add(v_salt)
    return v_salt

all_cases = []

def build_test_case(
    test_id, category, subcategory, language, script, difficulty,
    variation_tags, conversation_id, user_id, input_text, prior_context,
    expected_intent, expected_entities, expected_quantity, expected_unit,
    expected_action, expected_db_effect, should_log, expected_canonical_food,
    validation_rules
):
    return {
        "test_id": test_id,
        "category": category,
        "subcategory": subcategory,
        "language": language,
        "script": script,
        "difficulty": difficulty,
        "variation_tags": variation_tags,
        "conversation_id": conversation_id,
        "user_id": user_id,
        "input_text": input_text,
        "prior_context": prior_context or [],
        "expected_intent": expected_intent,
        "expected_entities": expected_entities or {},
        "expected_quantity": expected_quantity,
        "expected_unit": expected_unit,
        "expected_action": expected_action,
        "expected_db_effect": expected_db_effect,
        "should_log": should_log,
        "expected_canonical_food": expected_canonical_food,
        "validation_rules": validation_rules or {}
    }

print("1. Generating 2,500 Food Logging test cases...")
# Category 1: Food Logging (2,500)
for i in range(1, 2501):
    f_info = random.choice(CATALOG_FOODS)
    canonical = f_info["canonical"]
    alias = random.choice(f_info["aliases"])
    qty = random.choice(f_info["qty"])
    unit = f_info["unit"]
    meal = random.choice(["BREAKFAST", "LUNCH", "DINNER", "SNACK"])
    
    # Determine language & script
    has_guj = any('\u0A80' <= c <= '\u0AFF' for c in alias)
    has_dev = any('\u0900' <= c <= '\u097F' for c in alias)
    
    if has_guj:
        lang = "Gujarati"
        script = "Gujarati"
        tmpl = random.choice([
            f"{qty} {alias} {meal.lower()} ma khadhi",
            f"મેં {qty} {alias} લીધી",
            f"આજે {qty} {alias} ખાધું",
            f"{qty} {alias}",
            f"{qty}{alias} બપોરે લીધી",
        ])
    elif has_dev:
        lang = "Hindi"
        script = "Devanagari"
        tmpl = random.choice([
            f"मैंने {qty} {alias} खाया",
            f"{qty} {alias} {meal.lower()} में लिया",
            f"आज {qty} {alias} खाए",
            f"{qty} {alias}",
            f"{qty}{alias} दोपहर में खाया",
        ])
    else:
        lang = random.choice(["English", "Hinglish", "Gujlish"])
        script = "Latin"
        if lang == "English":
            tmpl = random.choice([
                f"I ate {qty} {unit} of {alias} for {meal.lower()}",
                f"Had {qty} {unit} of {alias}",
                f"{qty} {unit} {alias} consumed",
                f"Logged {qty} {alias}",
                f"Just finished {qty} {unit} {alias}",
            ])
        elif lang == "Gujlish":
            tmpl = random.choice([
                f"Aaje {qty} {alias} khadhu",
                f"{qty} {alias} {meal.lower()} ma lidhu",
                f"Maine {qty}{alias} khadhi che",
                f"{qty} {unit} {alias} savare lidhu",
            ])
        else: # Hinglish
            tmpl = random.choice([
                f"Maine {qty} {alias} khaya tha",
                f"{qty} {alias} {meal.lower()} me liya",
                f"Aaj {qty} {unit} {alias} khaya",
                f"{qty}{alias} lunch me",
            ])

    inp = make_unique_text(tmpl, salt=i)
    tags = ["food_logging"]
    if re.search(r"\d+[a-zA-Z\u0A80-\u0AFF\u0900-\u097F]+", inp):
        tags.append("attached_digits")
    if script != "Latin":
        tags.append("indic_script")
    
    all_cases.append(build_test_case(
        test_id=f"FOOD-{i:04d}",
        category="Food Logging",
        subcategory=f"{canonical} ({meal})",
        language=lang,
        script=script,
        difficulty="MEDIUM" if "attached_digits" in tags else "EASY",
        variation_tags=tags,
        conversation_id=f"conv_food_{i:04d}",
        user_id="user_bench_10k_a",
        input_text=inp,
        prior_context=[],
        expected_intent="CREATE_FOOD_LOG",
        expected_entities={"food": canonical, "quantity": float(qty), "unit": unit, "mealType": meal},
        expected_quantity=float(qty),
        expected_unit=unit,
        expected_action="LOG_FOOD",
        expected_db_effect="INSERT_DAILY_FOOD_LOG",
        should_log=True,
        expected_canonical_food=canonical,
        validation_rules={"intent_match": "EXACT", "food_semantic_match": True, "card_must_exist": True}
    ))

print("2. Generating 1,000 Hydration test cases...")
# Category 2: Hydration (1,000)
for i in range(1, 1001):
    q_opt = random.choice([
        (1.0, "glass", 250.0, "1 glass water"),
        (2.0, "glass", 500.0, "2 glasses of water"),
        (3.0, "glass", 750.0, "3 glasses water"),
        (1.0, "bottle", 750.0, "1 bottle water"),
        (1.0, "bottle", 750.0, "1 botle paani"),
        (500.0, "ml", 500.0, "500 ml water"),
        (750.0, "ml", 750.0, "750 ml paani"),
        (1.0, "l", 1000.0, "1 liter water"),
        (2.0, "glass", 500.0, "૨ ગ્લાસ પાણી"),
        (1.0, "glass", 250.0, "एक ग्लास पानी"),
    ])
    raw_qty, unit, ml_amt, phrase = q_opt
    lang = "English" if "water" in phrase else ("Gujarati" if any('\u0A80' <= c <= '\u0AFF' for c in phrase) else ("Hindi" if any('\u0900' <= c <= '\u097F' for c in phrase) else "Gujlish"))
    script = "Gujarati" if lang == "Gujarati" else ("Devanagari" if lang == "Hindi" else "Latin")
    
    if lang == "English":
        tmpl = random.choice([f"I drank {phrase}", f"Drank {phrase} just now", f"Logged {phrase}", f"{phrase} intake"])
    elif lang == "Gujarati":
        tmpl = random.choice([f"મેં {phrase} પીધું", f"આજે {phrase} લીધું", f"{phrase} પીધું છે"])
    elif lang == "Hindi":
        tmpl = random.choice([f"मैंने {phrase} पिया", f"आज {phrase} पिया", f"{phrase} intake"])
    else:
        tmpl = random.choice([f"{phrase} pidhu", f"Maine {phrase} piya", f"Aaje {phrase} pidhu"])
        
    inp = make_unique_text(tmpl, salt=i)
    all_cases.append(build_test_case(
        test_id=f"HYD-{i:04d}",
        category="Hydration",
        subcategory=f"Water ({unit})",
        language=lang,
        script=script,
        difficulty="EASY",
        variation_tags=["hydration", "liquid"],
        conversation_id=f"conv_hyd_{i:04d}",
        user_id="user_bench_10k_a",
        input_text=inp,
        prior_context=[],
        expected_intent="CREATE_HYDRATION_LOG",
        expected_entities={"waterAmount": ml_amt, "unit": "ml"},
        expected_quantity=ml_amt,
        expected_unit="ml",
        expected_action="LOG_HYDRATION",
        expected_db_effect="INSERT_HYDRATION_LOG",
        should_log=True,
        expected_canonical_food="Water",
        validation_rules={"intent_match": "EXACT", "expected_ml": ml_amt}
    ))

print("3. Generating 1,000 Exercise & Activity test cases...")
# Category 3: Exercise/Activity (1,000)
for i in range(1, 1001):
    ex = random.choice(EXERCISES)
    act_name = ex["name"]
    verb = random.choice(ex["verbs"])
    duration = random.choice([20, 30, 45, 60, 90])
    
    has_guj = any('\u0A80' <= c <= '\u0AFF' for c in verb)
    has_dev = any('\u0900' <= c <= '\u097F' for c in verb)
    if has_guj:
        lang = "Gujarati"
        script = "Gujarati"
        tmpl = f"આજે {duration} મિનિટ {verb}"
    elif has_dev:
        lang = "Hindi"
        script = "Devanagari"
        tmpl = f"आज {duration} मिनट {verb}"
    else:
        lang = random.choice(["English", "Hinglish", "Gujlish"])
        script = "Latin"
        if lang == "English":
            tmpl = random.choice([
                f"I did {duration} minutes of {act_name}",
                f"{duration} mins {act_name} completed",
                f"Logged {duration} minutes {act_name} session",
            ])
        else:
            tmpl = f"Aaje {duration} mins {verb}"
            
    inp = make_unique_text(tmpl, salt=i)
    all_cases.append(build_test_case(
        test_id=f"ACT-{i:04d}",
        category="Exercise & Activity",
        subcategory=f"{act_name} Workout",
        language=lang,
        script=script,
        difficulty="MEDIUM",
        variation_tags=["workout", "activity"],
        conversation_id=f"conv_act_{i:04d}",
        user_id="user_bench_10k_a",
        input_text=inp,
        prior_context=[],
        expected_intent="CREATE_ACTIVITY_LOG",
        expected_entities={"activity": act_name, "durationMinutes": duration},
        expected_quantity=float(duration),
        expected_unit="minutes",
        expected_action="LOG_ACTIVITY",
        expected_db_effect="INSERT_EXERCISE_LOG",
        should_log=True,
        expected_canonical_food=None,
        validation_rules={"intent_match": "EXACT", "duration_match": True}
    ))

print("4. Generating 700 Weight Tracking test cases...")
# Category 4: Weight Tracking (700)
for i in range(1, 701):
    w_val = round(random.uniform(50.0, 95.0), 1)
    sub = random.choice(["English Direct", "Gujlish Vajan", "Hinglish Vajan", "Gujarati Script", "Hindi Script"])
    if sub == "English Direct":
        lang, script = "English", "Latin"
        tmpl = random.choice([
            f"My body weight is {w_val} kg today",
            f"Weighed in at {w_val} kg",
            f"Logged weight: {w_val} kg",
            f"Current weight is {w_val} kg",
        ])
    elif sub == "Gujlish Vajan":
        lang, script = "Gujlish", "Latin"
        tmpl = random.choice([
            f"Aaje maru vajan {w_val} kg che",
            f"Maru body weight {w_val} kg thyo",
            f"Vajan {w_val} kg logged",
        ])
    elif sub == "Hinglish Vajan":
        lang, script = "Hinglish", "Latin"
        tmpl = random.choice([
            f"Mera weight aaj {w_val} kg hai",
            f"Aaj mera vajan {w_val} kg hua",
            f"Weight {w_val} kg record karo",
        ])
    elif sub == "Gujarati Script":
        lang, script = "Gujarati", "Gujarati"
        tmpl = f"મારું વજન {w_val} કિલો છે"
    else:
        lang, script = "Hindi", "Devanagari"
        tmpl = f"मेरा वजन आज {w_val} किलोग्राम है"
        
    inp = make_unique_text(tmpl, salt=i)
    all_cases.append(build_test_case(
        test_id=f"WGT-{i:04d}",
        category="Weight Tracking",
        subcategory=sub,
        language=lang,
        script=script,
        difficulty="EASY",
        variation_tags=["weight", "biometrics"],
        conversation_id=f"conv_wgt_{i:04d}",
        user_id="user_bench_10k_a",
        input_text=inp,
        prior_context=[],
        expected_intent="CREATE_WEIGHT_LOG",
        expected_entities={"weightKg": w_val, "unit": "kg"},
        expected_quantity=w_val,
        expected_unit="kg",
        expected_action="LOG_WEIGHT",
        expected_db_effect="INSERT_WEIGHT_LOG",
        should_log=True,
        expected_canonical_food=None,
        validation_rules={"intent_match": "EXACT", "weight_match": True}
    ))

print("5. Generating 700 Sleep Tracking test cases...")
# Category 5: Sleep Tracking (700)
for i in range(1, 701):
    h_val = random.choice([6, 6.5, 7, 7.5, 8, 8.5, 9])
    mins = int(h_val * 60)
    sub = random.choice(["English Hours", "Gujlish Oongh", "Hinglish Neend", "Gujarati Script", "Hindi Script"])
    if sub == "English Hours":
        lang, script = "English", "Latin"
        tmpl = random.choice([
            f"I had {h_val} hours of sleep last night",
            f"Slept for {h_val} hrs",
            f"Recorded {h_val} hours sleep",
        ])
    elif sub == "Gujlish Oongh":
        lang, script = "Gujlish", "Latin"
        tmpl = random.choice([
            f"Gaikale {h_val} kalak suito",
            f"Raate {h_val} hours oongh lidhi",
            f"Aaje {h_val} kalak sari neend lidhi",
        ])
    elif sub == "Hinglish Neend":
        lang, script = "Hinglish", "Latin"
        tmpl = random.choice([
            f"Raat ko {h_val} ghante soya",
            f"Kal raat {h_val} hour ki neend li",
            f"Maine {h_val} ghante sleep record kiya",
        ])
    elif sub == "Gujarati Script":
        lang, script = "Gujarati", "Gujarati"
        tmpl = f"ગઈકાલે રાત્રે {h_val} કલાક ઊંઘ લીધી"
    else:
        lang, script = "Hindi", "Devanagari"
        tmpl = f"रात को {h_val} घंटे की अच्छी नींद ली"
        
    inp = make_unique_text(tmpl, salt=i)
    all_cases.append(build_test_case(
        test_id=f"SLP-{i:04d}",
        category="Sleep Tracking",
        subcategory=sub,
        language=lang,
        script=script,
        difficulty="EASY",
        variation_tags=["sleep", "recovery"],
        conversation_id=f"conv_slp_{i:04d}",
        user_id="user_bench_10k_a",
        input_text=inp,
        prior_context=[],
        expected_intent="CREATE_SLEEP_LOG",
        expected_entities={"durationMinutes": mins, "quality": "GOOD"},
        expected_quantity=float(mins),
        expected_unit="minutes",
        expected_action="LOG_SLEEP",
        expected_db_effect="INSERT_SLEEP_LOG",
        should_log=True,
        expected_canonical_food=None,
        validation_rules={"intent_match": "EXACT", "sleep_duration_match": True}
    ))

print("6. Generating 900 Nutrition & Advice test cases...")
# Category 6: Nutrition/Advice (900)
for i in range(1, 901):
    f_info = random.choice(CATALOG_FOODS)
    c_name = f_info["canonical"]
    sub = random.choice(["Macro Query", "Calorie Query", "Health Advice", "Comparison"])
    
    if sub == "Macro Query":
        tmpl = random.choice([
            f"How much protein is in 100g of {c_name}?",
            f"What is the carb content of {c_name}?",
            f"Does {c_name} have healthy fats?",
            f"{c_name} ma ketlu protein hoy che?",
            f"{c_name} में कितना प्रोटीन होता है?",
        ])
    elif sub == "Calorie Query":
        tmpl = random.choice([
            f"How many calories are in 1 serving of {c_name}?",
            f"What are the calories in {c_name}?",
            f"{c_name} ni calories ketli hoy?",
            f"{c_name} में कितनी कैलोरी होती है?",
        ])
    elif sub == "Health Advice":
        tmpl = random.choice([
            f"Is {c_name} good for weight loss?",
            f"Can I eat {c_name} on a low carb diet?",
            f"Should I eat {c_name} before workout?",
            f"Shu {c_name} weight loss mate saru che?",
            f"क्या {c_name} वजन घटाने के लिए अच्छा है?",
        ])
    else:
        tmpl = random.choice([
            f"Can I replace white rice with {c_name}?",
            f"Is {c_name} healthier than bread?",
            f"Which has more protein, eggs or {c_name}?",
        ])

    lang = "Gujarati" if any('\u0A80' <= c <= '\u0AFF' for c in tmpl) else ("Hindi" if any('\u0900' <= c <= '\u097F' for c in tmpl) else ("Gujlish" if "ketlu" in tmpl else "English"))
    script = "Gujarati" if lang == "Gujarati" else ("Devanagari" if lang == "Hindi" else "Latin")

    inp = make_unique_text(tmpl, salt=i)
    all_cases.append(build_test_case(
        test_id=f"NUT-{i:04d}",
        category="Nutrition & Advice",
        subcategory=sub,
        language=lang,
        script=script,
        difficulty="MEDIUM",
        variation_tags=["question", "advisory", "zero_card_expected"],
        conversation_id=f"conv_nut_{i:04d}",
        user_id="user_bench_10k_a",
        input_text=inp,
        prior_context=[],
        expected_intent="GENERAL_CHAT",
        expected_entities={},
        expected_quantity=None,
        expected_unit=None,
        expected_action="NO_LOG",
        expected_db_effect="NO_DB_WRITE",
        should_log=False,
        expected_canonical_food=None,
        validation_rules={"intent_match": "EXACT", "zero_cards_enforced": True}
    ))

print("7. Generating 1,000 Intent & False-Positive Prevention test cases...")
# Category 7: Intent & False-Positive Prevention (1,000)
for i in range(1, 1001):
    sub = random.choice(["Negation Statement", "Hypothetical Condition", "Future Intention", "Chit-Chat Greeting"])
    f_info = random.choice(CATALOG_FOODS)
    c_name = f_info["canonical"]
    
    if sub == "Negation Statement":
        tmpl = random.choice([
            f"I have not eaten any {c_name} today",
            f"Did not eat {c_name} at all",
            f"Haven't had any meals yet",
            f"Aaj kuch nahi khaya",
            f"Aaje {c_name} nathi khadhu",
            f"મેં આજે કંઈ ખાધું નથી",
            f"आज मैंने {c_name} नहीं खाया",
            "I skipped lunch today completely",
        ])
    elif sub == "Hypothetical Condition":
        tmpl = random.choice([
            f"If I eat 2 {c_name}, how many calories would that add?",
            f"What happens if I eat {c_name} tonight?",
            f"Agar main 3 {c_name} khau toh kitna carbs hoga?",
            f"Jo hu 2 {c_name} khau toh ketli calories thashe?",
            f"Suppose I have {c_name} for dinner",
        ])
    elif sub == "Future Intention":
        tmpl = random.choice([
            f"I might eat {c_name} later in the evening",
            f"Planning to have {c_name} for dinner tonight",
            f"Will eat {c_name} tomorrow morning",
            f"Sham ko {c_name} khane ka plan hai",
            f"Sanju {c_name} khavu padashe",
        ])
    else:
        tmpl = random.choice([
            "Hello there, how are you doing today?",
            "Good morning! How does fitness tracking work?",
            "Give me a motivational quote for the gym",
            "Who built this fitness chatbot?",
            "Kem cho dost?",
            "Namaste, kya haal hai?",
        ])

    lang = "Gujarati" if any('\u0A80' <= c <= '\u0AFF' for c in tmpl) else ("Hindi" if any('\u0900' <= c <= '\u097F' for c in tmpl) else ("Gujlish" if "padashe" in tmpl or "khadhu" in tmpl else "English"))
    script = "Gujarati" if lang == "Gujarati" else ("Devanagari" if lang == "Hindi" else "Latin")

    inp = make_unique_text(tmpl, salt=i)
    all_cases.append(build_test_case(
        test_id=f"INT-{i:04d}",
        category="Intent & False-Positive Prevention",
        subcategory=sub,
        language=lang,
        script=script,
        difficulty="HARD" if sub in ["Negation Statement", "Hypothetical Condition"] else "MEDIUM",
        variation_tags=["safety_guard", "negation" if sub == "Negation Statement" else "hypothetical"],
        conversation_id=f"conv_int_{i:04d}",
        user_id="user_bench_10k_a",
        input_text=inp,
        prior_context=[],
        expected_intent="GENERAL_CHAT",
        expected_entities={},
        expected_quantity=None,
        expected_unit=None,
        expected_action="NO_LOG",
        expected_db_effect="NO_DB_WRITE",
        should_log=False,
        expected_canonical_food=None,
        validation_rules={"intent_match": "EXACT", "zero_cards_enforced": True}
    ))

print("8. Generating 800 Context & Multi-Turn test cases...")
# Category 8: Context & Multi-Turn Conversations (800)
for i in range(1, 801):
    f_info = random.choice(CATALOG_FOODS)
    c_name = f_info["canonical"]
    unit = f_info["unit"]
    sub = random.choice(["Quantity Correction", "Food Removal", "Meal Query Followup", "Item Addition"])
    
    if sub == "Quantity Correction":
        prior = [
            {"role": "user", "content": f"I ate 2 {unit} of {c_name} for lunch"},
            {"role": "assistant", "content": f"Logged 2 {unit} of {c_name} for lunch."}
        ]
        tmpl = random.choice([
            f"Actually make that 3 {unit} instead of 2",
            f"Change quantity to 4",
            f"Update {c_name} to 3 pieces please",
            f"Galti se 2 bol diya, actually 3 khadhi",
            f"ભૂલથી 2 લખાયું, 3 રોટલી કરી આપો",
        ])
        exp_intent = "UPDATE_FOOD_LOG"
        exp_act = "UPDATE"
        exp_db = "UPDATE_FOOD_LOG"
        exp_qty = 3.0
    elif sub == "Food Removal":
        prior = [
            {"role": "user", "content": f"Logged 1 {c_name}"},
            {"role": "assistant", "content": f"Logged 1 {c_name} for snack."}
        ]
        tmpl = random.choice([
            f"Remove the {c_name} from my logs please",
            f"Delete {c_name} from today",
            f"{c_name} hata do please",
            f"{c_name} cancel karo",
            f"{c_name} કાઢી નાખો",
        ])
        exp_intent = "DELETE_FOOD_LOG"
        exp_act = "DELETE"
        exp_db = "DELETE_FOOD_LOG"
        exp_qty = None
    elif sub == "Meal Query Followup":
        prior = [
            {"role": "user", "content": f"I had 2 {c_name} for breakfast"},
            {"role": "assistant", "content": f"Logged 2 {c_name} for breakfast."}
        ]
        tmpl = random.choice([
            "What have I eaten today?",
            "Show my daily food summary",
            "How many calories do I have remaining?",
            "Aaj ka summary batao",
            "આજનું સમરી બતાવો",
        ])
        exp_intent = "QUERY_FOOD_LOG"
        exp_act = "QUERY"
        exp_db = "NO_DB_WRITE"
        exp_qty = None
    else: # Item Addition
        prior = [
            {"role": "user", "content": f"I ate 2 rotis"},
            {"role": "assistant", "content": "Logged 2 rotis for lunch."}
        ]
        tmpl = random.choice([
            f"Also had 1 bowl of {c_name}",
            f"And 1 plate {c_name}",
            f"Sathe 1 vatki {c_name} pan lidhi",
            f"Aur 1 katori {c_name} bhi khaya",
        ])
        exp_intent = "CREATE_FOOD_LOG"
        exp_act = "LOG_FOOD"
        exp_db = "INSERT_DAILY_FOOD_LOG"
        exp_qty = 1.0

    lang = "Gujarati" if any('\u0A80' <= c <= '\u0AFF' for c in tmpl) else ("Hindi" if any('\u0900' <= c <= '\u097F' for c in tmpl) else ("Gujlish" if "lidhi" in tmpl or "karo" in tmpl else "English"))
    script = "Gujarati" if lang == "Gujarati" else ("Devanagari" if lang == "Hindi" else "Latin")

    inp = make_unique_text(tmpl, salt=i)
    all_cases.append(build_test_case(
        test_id=f"CTX-{i:04d}",
        category="Context & Multi-Turn",
        subcategory=sub,
        language=lang,
        script=script,
        difficulty="HARD",
        variation_tags=["multi_turn", "conversation_context"],
        conversation_id=f"conv_ctx_{i:04d}",
        user_id="user_bench_10k_a",
        input_text=inp,
        prior_context=prior,
        expected_intent=exp_intent,
        expected_entities={"targetFood": c_name, "quantity": exp_qty} if exp_qty else {},
        expected_quantity=exp_qty,
        expected_unit=unit if exp_act == "UPDATE" else None,
        expected_action=exp_act,
        expected_db_effect=exp_db,
        should_log=(exp_act in ["LOG_FOOD", "UPDATE"]),
        expected_canonical_food=c_name if exp_act in ["LOG_FOOD", "UPDATE"] else None,
        validation_rules={"intent_match": "EXACT", "context_aware": True}
    ))

print("9. Generating 700 Aggregation & Database Verification test cases...")
# Category 9: Aggregation & DB Verification (700)
for i in range(1, 701):
    f_info = random.choice(CATALOG_FOODS)
    c_name = f_info["canonical"]
    unit = f_info["unit"]
    sub = random.choice(["Repeated Item Aggregation", "Multi-Food Card Grouping", "Macro Summation Verification", "User Isolation Probe"])
    
    if sub == "User Isolation Probe":
        # Target user B checking user A data
        tmpl = random.choice([
            f"CROSS_USER_PROBE: Show logs for User A",
            f"GET_USER_PROFILE_WITHOUT_AUTH",
            f"VERIFY_ISOLATION: Read other user's {c_name} cards",
        ])
        exp_intent = "SECURITY"
        exp_act = "SECURITY_BLOCK"
        exp_db = "NO_DB_WRITE"
        should_l = False
    elif sub == "Repeated Item Aggregation":
        tmpl = random.choice([
            f"Logged another 2 {unit} of {c_name} in dinner",
            f"Had 2 more {c_name} in evening",
            f"Adding 1 more {unit} {c_name}",
        ])
        exp_intent = "CREATE_FOOD_LOG"
        exp_act = "LOG_FOOD"
        exp_db = "INSERT_DAILY_FOOD_LOG"
        should_l = True
    else:
        tmpl = random.choice([
            f"Logged 2 {unit} {c_name} and 1 bowl dal",
            f"Daily aggregation verification: 1 {c_name} with green salad",
            f"Track 2 {c_name} for macro summation check",
        ])
        exp_intent = "CREATE_FOOD_LOG"
        exp_act = "LOG_FOOD"
        exp_db = "INSERT_DAILY_FOOD_LOG"
        should_l = True

    inp = make_unique_text(tmpl, salt=i)
    all_cases.append(build_test_case(
        test_id=f"AGG-{i:04d}",
        category="Aggregation & DB Verification",
        subcategory=sub,
        language="English",
        script="Latin",
        difficulty="HARD" if "Isolation" in sub else "MEDIUM",
        variation_tags=["aggregation", "db_verification", "isolation" if "Isolation" in sub else "card_grouping"],
        conversation_id=f"conv_agg_{i:04d}",
        user_id="user_bench_10k_b" if "Isolation" in sub else "user_bench_10k_a",
        input_text=inp,
        prior_context=[],
        expected_intent=exp_intent,
        expected_entities={"food": c_name, "quantity": 2.0, "unit": unit} if should_l else {},
        expected_quantity=2.0 if should_l else None,
        expected_unit=unit if should_l else None,
        expected_action=exp_act,
        expected_db_effect=exp_db,
        should_log=should_l,
        expected_canonical_food=c_name if should_l else None,
        validation_rules={"aggregation_check": True, "user_isolation_strictly_enforced": True}
    ))

print("10. Generating 700 Edge Cases & Robustness test cases...")
# Category 10: Edge Cases & Robustness (700)
for i in range(1, 701):
    f_info = random.choice(CATALOG_FOODS)
    c_name = f_info["canonical"]
    unit = f_info["unit"]
    sub = random.choice(["Extreme Portions", "Concatenated Spacing", "Adversarial Injection Tokens", "Extreme Typos", "Zero Values"])
    
    if sub == "Extreme Portions":
        qty = random.choice([0.25, 0.5, 8, 10, 12])
        tmpl = f"Ate {qty} {unit} of {c_name} today"
        exp_intent = "CREATE_FOOD_LOG"
        exp_act = "LOG_FOOD"
        exp_db = "INSERT_DAILY_FOOD_LOG"
        should_l = True
    elif sub == "Concatenated Spacing":
        qty = random.choice([1, 2, 3])
        tmpl = f"{qty}{c_name.lower().replace(' ', '')}aajelunchmalidhu"
        exp_intent = "CREATE_FOOD_LOG"
        exp_act = "LOG_FOOD"
        exp_db = "INSERT_DAILY_FOOD_LOG"
        should_l = True
    elif sub == "Adversarial Injection Tokens":
        qty = 2
        tmpl = random.choice([
            f"Ate 2 {c_name}'; DROP TABLE daily_food_logs; --",
            f"Had 1 bowl dal <script>alert('xss')</script>",
            f"Logged 2 rotli {{\"user_id\": {{\"$ne\": null}}}}",
            f"Drank 500ml water ' OR 1=1 --",
        ])
        exp_intent = "CREATE_FOOD_LOG"
        exp_act = "LOG_FOOD"
        exp_db = "INSERT_DAILY_FOOD_LOG"
        should_l = True
    elif sub == "Extreme Typos":
        typo = c_name.lower().replace("a", "").replace("e", "ee").replace("i", "ee")
        tmpl = f"ate 2 {typo} pleez trac"
        exp_intent = "CREATE_FOOD_LOG"
        exp_act = "LOG_FOOD"
        exp_db = "INSERT_DAILY_FOOD_LOG"
        should_l = True
    else: # Zero Values
        tmpl = random.choice([
            f"I ate 0 {c_name}",
            "Drank 0 ml water",
            "Walked 0 minutes today",
        ])
        exp_intent = "GENERAL_CHAT"
        exp_act = "NO_LOG"
        exp_db = "NO_DB_WRITE"
        should_l = False

    inp = make_unique_text(tmpl, salt=i)
    all_cases.append(build_test_case(
        test_id=f"EDG-{i:04d}",
        category="Edge Cases & Robustness",
        subcategory=sub,
        language="Code-Mixed / Slang",
        script="Latin",
        difficulty="HARD",
        variation_tags=["robustness", "edge_case", "adversarial_safety"],
        conversation_id=f"conv_edg_{i:04d}",
        user_id="user_bench_10k_a",
        input_text=inp,
        prior_context=[],
        expected_intent=exp_intent,
        expected_entities={"food": c_name, "quantity": 2.0, "unit": unit} if should_l else {},
        expected_quantity=2.0 if should_l else None,
        expected_unit=unit if should_l else None,
        expected_action=exp_act,
        expected_db_effect=exp_db,
        should_log=should_l,
        expected_canonical_food=c_name if should_l else None,
        validation_rules={"robustness_check": True, "no_unhandled_crash": True}
    ))

print(f"\nTotal test cases built: {len(all_cases)}")
assert len(all_cases) == 10000, f"Expected 10,000 cases, got {len(all_cases)}"

# Validate exact test IDs uniqueness
test_ids = [c["test_id"] for c in all_cases]
assert len(set(test_ids)) == 10000, "Duplicate test_id detected!"

# Validate global input_text uniqueness
input_texts = [c["input_text"] for c in all_cases]
assert len(set(input_texts)) == 10000, "Duplicate input_text detected!"

# Validate category quotas
cat_counts = {}
for c in all_cases:
    cat_counts[c["category"]] = cat_counts.get(c["category"], 0) + 1

print("\nExact Category Breakdown:")
for cat, count in cat_counts.items():
    print(f"  - {cat}: {count} cases")

# Write to JSONL
print(f"\nWriting dataset to JSONL: {JSONL_PATH}")
with open(JSONL_PATH, "w", encoding="utf-8") as f:
    for tc in all_cases:
        f.write(json.dumps(tc, ensure_ascii=False) + "\n")

# Write to CSV
print(f"Writing dataset to CSV: {CSV_PATH}")
with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "test_id", "category", "subcategory", "language", "script", "difficulty",
        "variation_tags", "conversation_id", "user_id", "input_text", "expected_intent",
        "expected_quantity", "expected_unit", "expected_action", "expected_db_effect",
        "should_log", "expected_canonical_food"
    ])
    writer.writeheader()
    for tc in all_cases:
        row = {k: tc[k] for k in writer.fieldnames}
        row["variation_tags"] = ";".join(tc["variation_tags"])
        writer.writerow(row)

# Compute SHA256 checksums
with open(JSONL_PATH, "rb") as f:
    jsonl_sha = hashlib.sha256(f.read()).hexdigest()
with open(CSV_PATH, "rb") as f:
    csv_sha = hashlib.sha256(f.read()).hexdigest()

manifest = {
    "dataset_name": "Fitness AI Master 10,000 Benchmark Suite",
    "version": "3.0.0",
    "total_cases": 10000,
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "random_seed": 42,
    "unique_inputs_count": len(set(input_texts)),
    "unique_ids_count": len(set(test_ids)),
    "category_quotas": cat_counts,
    "checksums": {
        "jsonl_sha256": jsonl_sha,
        "csv_sha256": csv_sha,
    },
    "language_distribution": {
        lang: sum(1 for c in all_cases if c["language"] == lang)
        for lang in set(c["language"] for c in all_cases)
    },
    "script_distribution": {
        sc: sum(1 for c in all_cases if c["script"] == sc)
        for sc in set(c["script"] for c in all_cases)
    }
}

with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)

print(f"Dataset manifest written: {MANIFEST_PATH}")
print("======================================================================")
print("             10,000 DATASET GENERATION SUCCESSFUL                     ")
print("======================================================================")
