import re
import difflib
import unicodedata
from typing import Dict, Any, List, Optional, Tuple
from .time_service import TimeService

# Gujarati and Devanagari digit mapping
INDIC_DIGITS = {
    # Gujarati digits
    '૦': '0', '૧': '1', '૨': '2', '૩': '3', '૪': '4',
    '૫': '5', '૬': '6', '૭': '7', '૮': '8', '૯': '9',
    # Devanagari / Hindi digits
    '०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
    '५': '5', '६': '6', '७': '7', '८': '8', '९': '9',
}

# Number words to float values
NUMBER_WORDS = {
    # English
    "one": 1.0, "two": 2.0, "three": 3.0, "four": 4.0,
    "five": 5.0, "six": 6.0, "seven": 7.0, "eight": 8.0, "nine": 9.0, "ten": 10.0,
    "half": 0.5, "quarter": 0.25,
    # Hindi / Urdu
    "ek": 1.0, "do": 2.0, "teen": 3.0, "tin": 3.0, "chaar": 4.0, "char": 4.0,
    "paanch": 5.0, "panch": 5.0, "chheh": 6.0, "chhe": 6.0, "saat": 7.0, "sat": 7.0,
    "aath": 8.0, "nau": 9.0, "nav": 9.0, "dus": 10.0, "das": 10.0,
    "aadha": 0.5, "adha": 0.5, "paav": 0.25, "paw": 0.25, "dedh": 1.5, "dhai": 2.5,
    # Gujarati
    "be": 2.0, "tran": 3.0, "traan": 3.0, "chha": 6.0,
    "adho": 0.5, "adhu": 0.5, "pau": 0.25, "dhedh": 1.5, "adhadho": 0.5,
    # Gujarati script words
    "એક": 1.0, "બે": 2.0, "ત્રણ": 3.0, "ચાર": 4.0, "પાંચ": 5.0,
    "છ": 6.0, "સાત": 7.0, "આઠ": 8.0, "નવ": 9.0, "દસ": 10.0,
    "અડધો": 0.5, "અડધી": 0.5, "દોઢ": 1.5, "અઢી": 2.5,
    # Hindi script words
    "एक": 1.0, "दो": 2.0, "तीन": 3.0, "चार": 4.0, "पांच": 5.0,
    "छह": 6.0, "सात": 7.0, "आठ": 8.0, "नौ": 9.0, "दस": 10.0,
    "आधा": 0.5, "डेढ़": 1.5, "ढाई": 2.5,
}

# Unit normalizations
UNIT_MAP = {
    "katori": "bowl", "katoris": "bowl", "vatki": "bowl", "vatkis": "bowl",
    "vaatki": "bowl", "bowl": "bowl", "bowls": "bowl", "katora": "bowl", "bwl": "bowl",
    "cup": "cup", "cups": "cup", "kapp": "cup", "kap": "cup",
    "glass": "glass", "glasses": "glass", "glaas": "glass", "gls": "glass", "pyala": "glass",
    "plate": "plate", "plates": "plate", "dish": "plate", "thaali": "plate", "plet": "plate",
    "piece": "piece", "pieces": "piece", "pcs": "piece", "pc": "piece", "pice": "piece", "pices": "piece",
    "nag": "piece", "tukda": "piece",
    "slice": "slice", "slices": "slice", "scoop": "scoop", "scoops": "scoop",
    "spoon": "tbsp", "spoons": "tbsp", "spoonful": "tbsp",
    "chamach": "tbsp", "chamacha": "tbsp", "chamchi": "tbsp", "chammach": "tbsp", "chamcho": "tbsp",
    "tablespoon": "tbsp", "tablespoons": "tbsp", "teaspoon": "tsp", "teaspoons": "tsp",
    "tbsp": "tbsp", "tsp": "tsp", "ml": "ml", "liter": "l", "litre": "l",
    "l": "l", "ltr": "l", "gram": "g", "grams": "g", "g": "g", "kg": "kg",
    "bottle": "bottle", "bottles": "bottle", "botle": "bottle",
    "serving": "serving", "servings": "serving",
    # Gujarati script units
    "વાટકી": "bowl", "કટોરી": "bowl", "ગ્લાસ": "glass", "કપ": "cup", "પ્લેટ": "plate", "ડીશ": "plate", "નંગ": "piece", "ટુકડો": "piece",
    "ચમચી": "tbsp", "ચમચો": "tbsp", "સ્કૂપ": "scoop",
    # Hindi / Devanagari script units
    "कटोरी": "bowl", "कटोरा": "bowl", "ग्लास": "glass", "कप": "cup", "प्लेट": "plate", "टुकड़ा": "piece",
    "चम्मच": "tbsp", "चमच": "tbsp", "स्कूप": "scoop",
}

FOOD_NOUNS = [
    "roti", "rotli", "rotis", "rotlis", "chapati", "chapatis", "phulka", "phulkas", "khapli", "apple", "banana", "kela", "milk", "doodh", "dudh",
    "dal", "daal", "rice", "chawal", "poha", "upma", "egg", "anda", "bread",
    "salad", "sabzi", "shaak", "shak", "thepla", "theplas", "paratha", "chaas", "chhas", "chach", "dahi", "bhakri", "bhakhri",
    "chai", "chay", "tea", "coffee", "lassi", "paneer", "pneer", "pneeeer", "almonds",
    "lemon water", "nimbu pani", "black coffee", "pre workout", "preworkout",
    "whey", "protein powder", "protein shake", "protein", "whey protein", "shake", "protein drink",
    "dosa", "tikka", "pulao", "uttapam", "payasam", "sandesh", "curd", "biryani",
    "chicken", "momo", "idli", "vada", "samosa", "pakora", "khichdi", "chole", "bhature",
    "kulche", "mutton", "fish", "halwa", "puri", "poori", "toast", "curry", "sprouts", "chana",
    "dhokla", "khaman", "handvo", "fafda", "jalebi", "undhiyu", "patra", "muthiya", "locho",
    "kachori", "misal", "bharta", "bharthu", "pongal", "appam", "puttu", "bisi bele", "avial",
    "shrikhand", "basundi", "kheer", "gulab jamun", "bhatura", "puran poli", "varan phal",
    "chitranna", "thayir sadam", "aloo gobi", "okra", "khichdo", "sev tameta", "wada pav",
    "hopper", "idly", "jilapi", "matho", "phulka", "butter naan", "naan", "handwa",
    "khakhra", "rajma", "bhindi", "pav bhaji", "pavbhaji", "vedmi", "mohanthal",
    # Gujarati script food nouns
    "રોટલી", "રોટલો", "ભાખરી", "ચા", "દાળ", "ભાત", "દૂધ", "છાશ", "કેળા", "કેળું", "શાક", "ખીચડી",
    "ઢોકળા", "હાંડવો", "થેપલા", "ઊંધિયું", "બાસુંદી", "ભીંડી", "મુઠીયા", "પાત્રા", "સેવ ટમેટા", "સેવ ટામેટા",
    "મોહનથાળ", "ખાખરા", "સમોસા", "શ્રીખંડ", "ફણગાવેલા મગ", "મગ", "ઈંડા", "ઈંડું", "વેડમી", "ઉપમા",
    "પૌંઆ", "પોહા", "સફરજન", "પનીર", "રાજમા", "ચણા", "ઢોંસા", "ઢોસા", "ઇડલી", "ઉત્તપમ", "ઉત્તપા",
    "નાન", "પાઉંભાજી", "પાંવભાજી", "પાઉં ભાજી", "જલેબી", "ફાફડા", "સુખડી", "લાડવા", "દહીંવડા", "દહીં", "કઢી", "પૂરી",
    "પ્રોટીન શેક", "પ્રોટીન પાવડર", "પ્રોટીન", "શેક",
    # Devanagari script food nouns
    "रोटी", "दाल", "चावल", "दूध", "छाछ", "केला", "सब्जी", "खीचड़ी", "पनीर", "समोसा", "इडली", "डोसा",
    "पोहा", "उपमा", "राजमा", "भिंडी", "बासुंदी", "सेव टमाटर", "पराठा", "अंडा", "अंडे", "कढ़ी", "कढ़ी",
    "खाखरा", "पाव भाजी", "पावभाजी", "नान", "छोले", "रायता", "सेब", "उत्पम", "उत्तपम", "मुठिया",
    "पात्रा", "श्रीखंड", "मोहनथाल", "फाफड़ा", "जलेबी", "दही", "पूरी",
    "प्रोटीन शेक", "प्रोटीन पाउडर", "प्रोटीन",
    # Urdu script
    "بھنڈی"
]

EATING_VERBS = [
    "ate", "had", "eaten", "consumed", "taking", "took", "eating", "logged", "finished", "having",
    "khadha", "khadhi", "khadhu", "khaye", "khaya", "khayi", "khalo",
    "lidhi", "lidhu", "lidho", "leedhi", "leedhu", "liya", "li",
    "ખાધી", "ખાધું", "ખાધા", "લીધું", "લીધી",
    "खाया", "खाई", "खाए", "लिया", "ली"
]

DRINKING_VERBS = [
    "pidhi", "pidhu", "pidha", "piya", "peeli", "peena", "drink", "drank", "drunk", "peeya",
    "પીધું", "પીધી", "पिया", "पी"
]

WORKOUT_PATTERNS = [
    r"\bwalk\b", r"\bwalked\b", r"\bwalking\b", r"\brun\b", r"\brunning\b", r"\bran\b",
    r"\bgym\b", r"(?<!pre[-\s])\bworkout\b", r"\bexercise\b", r"\bcycling\b", r"\bpush-?ups?\b", r"\bpull-?ups?\b",
    r"\bback\b(?!\s+(?:tea|coffee))", r"\bbiceps?\b", r"\btriceps?\b", r"\bchest\b", r"\blegs?\b", r"\bshoulders?\b", r"\babs\b",
    r"\byoga\b", r"\bbadminton\b", r"\bcricket\b", r"\bswimming\b", r"\bfootball\b",
    r"\bjump rope\b", r"\bhiit\b", r"\bpilates\b", r"\bzumba\b", r"\bdance\b",
    r"\bsquats?\b", r"\blunges?\b", r"\bcrunches?\b", r"\bplanks?\b", r"\bburpees?\b",
    r"\bbench press\b", r"\bdeadlifts?\b", r"\bstretching\b", r"\bstrength\s*training\b", r"\bdhodhyo\b", r"\bkasrat\b", r"\bchalyo\b",
    r"દૌડ્યા", r"દૌડ્યો", r"દોડ્યો", r"ચાલ્યો", r"કસરત", r"વર્કઆઉટ", r"યોગા", r"સ્ક્વોટ્સ?", r"પુશઅપ્સ?", r"સ્ટ્રેન્થ\s*ટ્રેનિંગ",
    r"दौड़ा", r"दौड़ी", "कसरत", "वर्कआउट", "योगा", "व्यायाम", r"स्क्वैट्स?", r"पुशअप्स?", r"स्ट्रेंथ\s*ट्रेनिंग"
]

# Common food spelling corrections & slang aliases
INDIAN_FOOD_SYNONYMS: Dict[str, str] = {
    # Roti / Breads / Grains
    "khapli rti": "Khapli Wheat Rotli",
    "khapli roti": "Khapli Wheat Rotli",
    "khapli rotli": "Khapli Wheat Rotli",
    "khapli": "Khapli Wheat Rotli",
    "rotli": "Roti",
    "rotlis": "Roti",
    "roti": "Roti",
    "rotis": "Roti",
    "rotliyo": "Roti",
    "rotlee": "Roti",       # phonetic variant: rotlee sounds like rotli
    "rotlii": "Roti",       # double-i phonetic variant
    "chapati": "Chapati",
    "chapatis": "Chapati",
    "phulka": "Phulka",
    "phulke": "Phulka",
    "phulkas": "Phulka",
    "theplas": "Methi Thepla",
    "theple": "Methi Thepla",
    "rotlo": "Rotlo",
    "rotla": "Rotlo",
    "rotlu": "Rotlo",
    "bajra rotlo": "Rotlo",
    "bajri rotla": "Rotlo",
    "bajri no rotlo": "Rotlo",
    "bajra roti": "Rotlo",
    "bajre ki roti": "Rotlo",
    "bhadthu": "Baingan Bharta",
    "bharthu": "Baingan Bharta",
    "olo": "Baingan Bharta",
    "ringna no olo": "Baingan Bharta",
    "baingan bharta": "Baingan Bharta",
    "bhakri": "Bhakri",
    "bhakhri": "Bhakri",
    "bakhri": "Bhakri",
    "whole wheat bhakri": "Bhakri",
    "thepla": "Methi Thepla",
    "methi thepla": "Methi Thepla",
    "paratha": "Plain Paratha",
    "aloo paratha": "Aloo Paratha",
    "paneer paratha": "Paneer Paratha",
    "pneer paratha": "Paneer Paratha",
    "panir paratha": "Paneer Paratha",
    "poori": "Poori",
    "puri": "Poori",
    "naan": "Butter Naan",
    "butter naan": "Butter Naan",
    "chai": "Tea With Milk",
    "chay": "Tea With Milk",
    "tea": "Tea With Milk",
    "masala chai": "Tea With Milk",
    "masala tea": "Tea With Milk",
    "coffee": "Coffee With Milk",
    "cofee": "Coffee With Milk",
    "black coffee": "Black Coffee",
    "black cofee": "Black Coffee",
    "lemon water": "Lemon Water",
    "nimbu pani": "Lemon Water",
    "leembu pani": "Lemon Water",
    "pre workout": "Pre Workout",
    "pre-workout": "Pre Workout",
    "preworkout": "Pre Workout",
    "green tea": "Green Tea",
    "chawal": "Cooked White Rice",
    "bhaat": "Cooked White Rice",
    "rice": "Cooked White Rice",
    "steamed rice": "Cooked White Rice",
    "khichdi": "Moong Dal Khichdi",
    "khichdo": "Moong Dal Khichdi",
    "moong dal khichdi": "Moong Dal Khichdi",
    "poha": "Poha",
    "upma": "Upma",
    "idli": "Idli",
    "idly": "Idli",
    "dosa": "Plain Dosa",
    "plain dosa": "Plain Dosa",
    "masala dosa": "Masala Dosa",

    # Dairy
    "doodh": "Cow Milk (Toned)",
    "dudh": "Cow Milk (Toned)",
    "milk": "Cow Milk (Toned)",
    "cow milk": "Cow Milk (Toned)",
    "chaas": "Spiced Buttermilk (Chaas)",
    "chhas": "Spiced Buttermilk (Chaas)",
    "chach": "Spiced Buttermilk (Chaas)",
    "buttermilk": "Spiced Buttermilk (Chaas)",
    "dahi": "Curd (Dahi)",
    "curd": "Curd (Dahi)",
    "yogurt": "Curd (Dahi)",
    "paneer": "Paneer",
    "pneer": "Paneer",
    "paneer bhurji": "Paneer Bhurji",
    "paneer makhani": "Paneer",
    "paneer tikka": "Paneer Tikka",
    "ghee": "Desi Ghee",
    "butter": "Butter",
    "cheese": "Cheese",
    "lassi": "Sweet Lassi",

    # Dals & Pulses
    "dal": "Toor Dal",
    "daal": "Toor Dal",
    "toor dal": "Toor Dal",
    "tuver dal": "Toor Dal",
    "yellow dal": "Toor Dal",
    "yellow toor dal": "Toor Dal",
    "moong dal": "Yellow Moong Dal",
    "mug dal": "Yellow Moong Dal",
    "chana dal": "Chana Dal",
    "kadhi": "Gujarati Kadhi",
    "sambhar": "Sambar",
    "sambar": "Sambar",
    "chole": "Chole Chana Masala",
    "chole chana": "Chole Chana Masala",
    "chole masala": "Chole Chana Masala",
    "chana masala": "Chole Chana Masala",
    "rajma": "Rajma",
    "kidney bean": "Rajma",
    "kidney beans": "Rajma",
    "chana": "Boiled Chickpeas",
    "sprouts": "Mixed Sprouts",

    # Fruits & Vegetables
    "banana": "Banana",
    "banaana": "Banana",
    "bananna": "Banana",
    "kela": "Banana",
    "keda": "Banana",
    "kelu": "Banana",
    "apple": "Apple",
    "safarjan": "Apple",
    "seb": "Apple",
    "mango": "Mango",
    "keri": "Mango",
    "aam": "Mango",
    "orange": "Orange",
    "santre": "Orange",
    "papaya": "Papaya",
    "watermelon": "Watermelon",
    "tarbooz": "Watermelon",
    "sabzi": "Mixed Vegetable Sabzi",
    "shaak": "Mixed Vegetable Sabzi",
    "shak": "Mixed Vegetable Sabzi",
    "bhindi": "Bhindi Masala",
    "bhindi sabzi": "Bhindi Masala",
    "bhindi masala": "Bhindi Masala",
    "okra": "Bhindi Masala",
    "okra sabzi": "Bhindi Masala",
    "okra sabji": "Bhindi Masala",
    "aloo sabzi": "Aloo Sabzi",
    "alu sabzi": "Aloo Sabzi",
    "alu sabji": "Aloo Sabzi",
    "aloo sabji": "Aloo Sabzi",
    "bataka nu shaak": "Aloo Sabzi",
    "bataka ni subji": "Aloo Sabzi",
    "bataka subji": "Aloo Sabzi",
    "bateka ni subji": "Aloo Sabzi",
    "bateka subji": "Aloo Sabzi",
    "bateka nu shaak": "Aloo Sabzi",
    "bateta nu shaak": "Aloo Sabzi",
    "bateta ni sabji": "Aloo Sabzi",
    "bateta subji": "Aloo Sabzi",
    "aloo gobi": "Aloo Sabzi",
    "alu gobi": "Aloo Sabzi",
    "palak": "Palak Paneer",
    "salad": "Green Salad",

    # Non-Veg & Proteins
    "egg": "Boiled Egg",
    "eggs": "Boiled Egg",
    "anda": "Boiled Egg",
    "ande": "Boiled Egg",
    "boiled egg": "Boiled Egg",
    "boiled eggs": "Boiled Egg",
    "omelette": "Egg Omelette",
    "omelet": "Egg Omelette",
    "egg omelette": "Egg Omelette",
    "egg omlette": "Egg Omelette",
    "egg white": "Egg White",
    "chicken": "Chicken Breast",
    "chiken": "Chicken Breast",
    "chicken breast": "Chicken Breast",
    "chicken tikka": "Chicken Tikka",
    "fish": "Grilled Fish",
    "whey": "Whey Protein Powder",
    "whey protein": "Whey Protein Powder",
    "whey protein powder": "Whey Protein Powder",
    "protein powder": "Whey Protein Powder",
    "protin powder": "Whey Protein Powder",
    "protien powder": "Whey Protein Powder",
    "protein shake": "Protein Shake",
    "protein shakes": "Protein Shake",
    "protin shake": "Protein Shake",
    "protien shake": "Protein Shake",
    "shake": "Protein Shake",
    "shakes": "Protein Shake",
    "whey shake": "Protein Shake",
    "whey protein shake": "Protein Shake",
    "protein drink": "Protein Shake",
    "whey powder": "Whey Protein Powder",
    "protein powders": "Whey Protein Powder",
    "plant protein": "Plant Protein Powder",
    "plant protein powder": "Plant Protein Powder",
    "protein": "Protein Shake",

    # Snacks & Regional
    "biscuit": "Digestive Biscuit",
    "biscuits": "Digestive Biscuit",
    "khakhra": "Methi Khakhra",
    "samosa": "Samosa",
    "dhokla": "Khaman Dhokla",
    "khaman": "Khaman Dhokla",
    "khaman dhokla": "Khaman Dhokla",
    "handvo": "Gujarati Handvo",
    "handwa": "Gujarati Handvo",
    "sev tameta": "Sev Tameta Nu Shaak",
    "sev tameta nu shaak": "Sev Tameta Nu Shaak",
    "farsan": "Gujarati Farsan",
    "mohanthal": "Mohanthal",
    "kheer": "Rice Kheer",
    "sandesh": "Sandesh",
    "veg pulao": "Veg Pulao",
    "boondi raita": "Boondi Raita",
    "semiya payasam": "Semiya Payasam",
    "onion tomato uttapam": "Onion Tomato Uttapam",
    "uttapam": "Onion Tomato Uttapam",
    "undhiyu": "Surti Undhiyu",
    "surti undhiyu": "Surti Undhiyu",
    "dal dhokli": "Gujarati Dal Dhokli",
    "muthiya": "Muthiya",
    "patra": "Patra",
    "shrikhand": "Shrikhand",
    "basundi": "Basundi",
    "kachumber": "Green Salad",
    "fafda": "Fafda",
    "jalebi": "Jalebi",
    "jilapi": "Jalebi",
    "puran poli": "Puran Poli",
    "puranpoli": "Puran Poli",
    "vedmi": "Puran Poli",
    "pav bhaji": "Pav Bhaji",
    "pavbhaji": "Pav Bhaji",
    "alu dosa": "Masala Dosa",
    "aloo dosa": "Masala Dosa",
    "protein powder": "Whey Protein Powder",
    "chole bhature": "Chole Chana Masala",
    "dahi bhat": "Curd (Dahi)",
    "water": "Water",
    "paani": "Water",
    "pani": "Water",

    # Native Gujarati Script
    "રોટલી": "Roti",
    "રોટલો": "Rotlo",
    "રોટલા": "Rotlo",
    "બાજરીનો રોટલો": "Rotlo",
    "ભડથું": "Baingan Bharta",
    "ભરથું": "Baingan Bharta",
    "ઓળો": "Baingan Bharta",
    "રીંગણાનો ઓળો": "Baingan Bharta",
    "ભાખરી": "Bhakri",
    "ભાખરીઓ": "Bhakri",
    "દાળ": "Toor Dal",
    "તુવેર દાળ": "Toor Dal",
    "ભાત": "Cooked White Rice",
    "ચોખા": "Cooked White Rice",    # alternate Gujarati word for rice
    "ખીચડી": "Moong Dal Khichdi",
    "દૂધ": "Cow Milk (Toned)",
    "ચા": "Tea With Milk",           # Gujarati script for chai/tea
    "છાશ": "Spiced Buttermilk (Chaas)",
    "દહીં": "Curd (Dahi)",
    "પનીર": "Paneer",
    "શાક": "Mixed Vegetable Sabzi",
    "કેળા": "Banana",
    "કેળું": "Banana",
    "સફરજન": "Apple",
    "ઈંડું": "Boiled Egg",
    "ઈંડા": "Boiled Egg",
    "પાણી": "Water",
    "બાસુંદી": "Basundi",
    "ભીંડી": "Bhindi Masala",
    "મુઠીયા": "Muthiya",
    "પાત્રા": "Patra",
    "સેવ ટમેટા": "Sev Tameta Nu Shaak",
    "સેવ ટામેટા": "Sev Tameta Nu Shaak",
    "સેવ ટમેટા નુ શાક": "Sev Tameta Nu Shaak",
    "મોહનથાળ": "Mohanthal",
    "ખાખરા": "Methi Khakhra",
    "સમોસા": "Samosa",
    "શ્રીખંડ": "Shrikhand",
    "ફણગાવેલા મગ": "Mixed Sprouts",
    "મગ": "Yellow Moong Dal",
    "વેડમી": "Puran Poli",
    "ઉપમા": "Upma",
    "પૌંઆ": "Poha",
    "પૌઆ": "Poha",    # alternate spelling without anusvara
    "પોહા": "Poha",
    "રાજમા": "Rajma",
    "ચણા": "Chole Chana Masala",
    "ઢોંસા": "Plain Dosa",
    "ઢોસા": "Plain Dosa",
    "ઇડલી": "Idli",
    "ઉત્તપમ": "Onion Tomato Uttapam",
    "નાન": "Butter Naan",
    "પાઉંભાજી": "Pav Bhaji",
    "પાંવભાજી": "Pav Bhaji",
    "પાઉં ભાજી": "Pav Bhaji",
    "જલેબી": "Jalebi",
    "ફાફડા": "Fafda",
    "સુખડી": "Sukhdi",
    "કઢી": "Gujarati Kadhi",
    "પૂરી": "Poori",
    "ખમણ": "Khaman Dhokla",
    "નાયલોન ખમણ": "Khaman Dhokla",
    "દાળ ઢોકળી": "Gujarati Dal Dhokli",
    "દાળઢોકળી": "Gujarati Dal Dhokli",
    "છોલે": "Chole Chana Masala",
    "છોલે ચના મસાલા": "Chole Chana Masala",
    "પનીર પરાઠા": "Paneer Paratha",
    "આલૂ સબ્જી": "Aloo Sabzi",
    "આલૂ પરોઠા": "Aloo Paratha",
    "આલૂ પરાઠા": "Aloo Paratha",
    "હાંડવો": "Gujarati Handvo",
    "થેપલા": "Methi Thepla",
    "થેપલાં": "Methi Thepla",
    "ચપાતી": "Chapati",
    "ફૂલકા": "Phulka",
    "પ્રોટીન શેક": "Protein Shake",
    "પ્રોટીન પાવડર": "Whey Protein Powder",
    "પ્રોટીન": "Protein Shake",
    "પ્રોટિન શેક": "Protein Shake",
    "પ્રોટિન પાવડર": "Whey Protein Powder",
    "પ્રોટિન": "Protein Shake",
    "શેક": "Protein Shake",

    # Native Devanagari Script
    "रोटी": "Roti",
    "रोटियां": "Roti",
    "रोटियाँ": "Roti",
    "चपाती": "Chapati",
    "फुलका": "Phulka",
    "थेपले": "Methi Thepla",
    "दाल": "Toor Dal",
    "चावल": "Cooked White Rice",
    "खिचड़ी": "Moong Dal Khichdi",
    "दूध": "Cow Milk (Toned)",
    "छाछ": "Spiced Buttermilk (Chaas)",
    "दही": "Curd (Dahi)",
    "पनीर": "Paneer",
    "सब्जी": "Mixed Vegetable Sabzi",
    "केला": "Banana",
    "सेब": "Apple",
    "अंडा": "Boiled Egg",
    "अंडे": "Boiled Egg",
    "पानी": "Water",
    "पोहा": "Poha",
    "उपमा": "Upma",
    "राजमा": "Rajma",
    "छोले": "Chole Chana Masala",
    "छोले चना मसाला": "Chole Chana Masala",
    "चना मसाला": "Chole Chana Masala",
    "दाल ढोकली": "Gujarati Dal Dhokli",
    "दालढोकली": "Gujarati Dal Dhokli",
    "पनीर पराठा": "Paneer Paratha",
    "आलू गोभी": "Aloo Sabzi",
    "आलू गोबी": "Aloo Sabzi",
    "आलू सब्जी": "Aloo Sabzi",
    "आलू पराठा": "Aloo Paratha",
    "अंडा ऑमलेट": "Egg Omelette",
    "ऑमलेट": "Egg Omelette",
    "भिंडी": "Bhindi Masala",
    "बासुंदी": "Basundi",
    "सेव टमाटर": "Sev Tameta Nu Shaak",
    "कढ़ी": "Gujarati Kadhi",
    "कढ़ी": "Gujarati Kadhi",
    "पाव भाजी": "Pav Bhaji",
    "पावभाजी": "Pav Bhaji",
    "पराठा": "Plain Paratha",
    "खाखरा": "Methi Khakhra",
    "समोसा": "Samosa",
    "इडली": "Idli",
    "डोसा": "Plain Dosa",
    "मसाला डोसा": "Masala Dosa",
    "उत्पम": "Onion Tomato Uttapam",
    "उत्तपम": "Onion Tomato Uttapam",
    "मुठिया": "Muthiya",
    "पात्रा": "Patra",
    "श्रीखंड": "Shrikhand",
    "मोहनथाल": "Mohanthal",
    "फाफड़ा": "Fafda",
    "जलेबी": "Jalebi",
    "पूरी": "Poori",
    "प्रोटीन शेक": "Protein Shake",
    "प्रोटीन पाउडर": "Whey Protein Powder",
    "प्रोटीन": "Protein Shake",
    "व्हे प्रोटीन": "Whey Protein Powder",

    # Urdu Script
    "بھنڈی": "Bhindi Masala",
}

class AgentNLP:
    @staticmethod
    def normalize_indic_digits(text: str) -> str:
        """Converts Gujarati and Hindi/Devanagari numerals to ASCII digits."""
        res = []
        for ch in text:
            res.append(INDIC_DIGITS.get(ch, ch))
        return "".join(res)

    @staticmethod
    def detect_language(text: str) -> str:
        """Detects whether text contains Gujarati, Devanagari, or Latin script."""
        has_gujarati = any('\u0A80' <= ch <= '\u0AFF' for ch in text)
        if has_gujarati:
            return "gu"
        has_devanagari = any('\u0900' <= ch <= '\u097F' for ch in text)
        if has_devanagari:
            return "hi"
        # Check for Gujlish / Hinglish keywords
        lower = text.lower()
        if any(w in lower for w in ["rotli", "ane", "chhas", "khadhi", "lidhu", "lidhi", "thyu", "kem", "chho"]):
            return "gu-Latn"
        if any(w in lower for w in ["roti", "khaya", "khayi", "aur", "peena", "kya", "hua"]):
            return "hi-Latn"
        return "en"

    @staticmethod
    def repair_missing_spaces_and_typos(text: str) -> str:
        """Repairs attached digits, decompounds common fused words, and normalizes typos."""
        norm = AgentNLP.normalize_indic_digits(text)
        norm = unicodedata.normalize("NFC", norm)
        # Separate attached digits from words: e.g. '2rotli' -> '2 rotli', '500ml' -> '500 ml'
        norm = re.sub(r"(\d+)([a-zA-Z\u0A80-\u0AFF\u0900-\u097F]+)", r"\1 \2", norm)
        norm = re.sub(r"([a-zA-Z\u0A80-\u0AFF\u0900-\u097F]+)(\d+)", r"\1 \2", norm)

        decompounds = {
            r"\bpavbhaji\b": "pav bhaji",
            r"\bdahibhat\b": "dahi bhat",
            r"\bmasalachai\b": "masala chai",
            r"\bmaslachaye\b": "masala chai",
            r"\bcholebhature\b": "chole bhature",
            r"\bdaldhokli\b": "dal dhokli",
            r"\bsambarrice\b": "sambar rice",
            r"\bkhaplirti\b": "khapli roti",
            r"\bpuranpoli\b": "puran poli",
        }
        for pat, repl in decompounds.items():
            norm = re.sub(pat, repl, norm, flags=re.IGNORECASE)

        typos = {
            # Conjunctions & prepositions
            r"\bamd\b": "and",
            r"\bwid\b": "with",
            r"\bwth\b": "with",
            # Hydration & beverages
            r"\bwatter\b": "water",
            r"\blamon\b": "lemon",
            r"\bleman\b": "lemon",
            r"\blimbu\b": "lemon",
            r"\bwatwr\b": "water",
            r"\bwatr\b": "water",
            r"\bwtr\b": "water",
            r"\bwaater\b": "water",
            r"\bpaani\b": "pani",
            r"\bpanni\b": "pani",
            r"\bcofee\b": "coffee",
            r"\bcoffe\b": "coffee",
            r"\bcofe\b": "coffee",
            r"\bcaffe\b": "coffee",
            r"\bblck\b": "black",
            r"\bmilkk\b": "milk",
            r"\bmlik\b": "milk",
            # Workout & exercise
            r"\bbiseps?\b": "biceps",
            r"\bbicep\b": "biceps",
            r"\bbyceps?\b": "biceps",
            r"\btricep\b": "triceps",
            r"\btriseps?\b": "triceps",
            r"\btrisep\b": "triceps",
            r"\bsholder\b": "shoulder",
            r"\bsholders\b": "shoulders",
            r"\bwalikng\b": "walking",
            r"\bwalkng\b": "walking",
            r"\bwaking\b": "walking",
            r"\bwlak\b": "walk",
            r"\bwokout\b": "workout",
            r"\bworkot\b": "workout",
            r"\bwrkout\b": "workout",
            r"\bexersise\b": "exercise",
            r"\bexcersise\b": "exercise",
            # Food & supplements
            r"\bprotien\b": "protein",
            r"\bprotin\b": "protein",
            r"\bpowdr\b": "powder",
            r"\bpawder\b": "powder",
            r"\bkhapali\b": "khapli",
            r"\brti\b": "roti",
            r"\bpice\b": "piece",
            r"\bpices\b": "pieces",
            r"\bplet\b": "plate",
            r"\bbwl\b": "bowl",
            r"\bgls\b": "glass",
            r"\bglaas\b": "glass",
            r"\bbotle\b": "bottle",
            r"\bchaye\b": "chai",
            r"\bpneer\b": "paneer",
            r"\bpneeeer\b": "paneer",
            r"\bpanner\b": "paneer",
            r"\bpoh\b": "poha",
            r"\bmakni\b": "makhani",
            r"\beggz\b": "eggs",
            r"\bsamose\b": "samosa",
            r"\bidlee\b": "idli",
            r"\bsambher\b": "sambar",
            r"\bparotha\b": "paratha",
            r"\bdaal\b": "dal",
            r"\bbanaana\b": "banana",
            r"\bchiken\b": "chicken",
            r"\blitr\b": "litre",
            r"\blieter\b": "litre",
            r"\bskoop\b": "scoop",
            r"\bscop\b": "scoop",
            r"\bskup\b": "scoop",
        }
        for pat, repl in typos.items():
            norm = re.sub(pat, repl, norm, flags=re.IGNORECASE)

        # Safe fuzzy correction for remaining typos against core vocabulary.
        # Words in this list are EXCLUDED from fuzzy correction (they are treated as
        # correct as-is). This prevents valid Gujlish words like 'rotli', 'chaas',
        # 'thepla' from being corrupted into their closest English neighbours.
        # Also protects Gujlish slang that must NOT be misread as food names —
        # e.g. 'dabbu' (tiffin box) must not become 'khapli'.
        fuzzy_vocab = [
            "lemon", "water", "coffee", "biceps", "triceps", "walking", "workout", "protein",
            "powder", "scoop", "glass", "bottle", "roti", "khapli", "milk",
            # Gujlish food/exercise words — must not be fuzzy-corrected to similar English words
            "rotli", "chaas", "chhas", "thepla", "bhakri", "khichdi", "bhaat", "khadhi",
            "lidhu", "lidhi", "khadha", "pidhi", "pidhu", "paneer", "paratha",
            # Gujlish slang / non-food words that must not be matched to food names
            "dabbu",   # tiffin box / lunchbox — NOT a food name
            "dabba",   # same concept, Hinglish spelling
            "tiffin",  # generic container word
            "khali",   # Gujarati/Hindi: empty / finished — NOT a food
            "khalo",   # Gujarati verb: eat (imperative) — NOT a food name
            "karyu",   # Gujarati verb: did — NOT a food name
            "thakor",  # Gujarati proper noun / title
        ]
        words = norm.split(" ")
        corrected_words = []
        for w in words:
            w_clean = re.sub(r"^[^\w]+|[^\w]+$", "", w.lower())
            if len(w_clean) >= 4 and w_clean not in fuzzy_vocab and not w_clean.isdigit():
                matches = difflib.get_close_matches(w_clean, fuzzy_vocab, n=1, cutoff=0.82)
                if matches:
                    w = re.sub(rf"\b{re.escape(w_clean)}\b", matches[0], w, flags=re.I)
            corrected_words.append(w)
        norm = " ".join(corrected_words)

        return norm

    @staticmethod
    def parse_number_tokens(text: str) -> str:
        """Replaces written number words (e.g. 'two', 'be', 'ek', 'aadha') with numeric strings while preserving newlines."""
        lines = text.splitlines(keepends=True)
        res_lines = []
        for line in lines:
            ends_with_newline = line.endswith("\n") or line.endswith("\r")
            content = line.rstrip("\r\n")
            tokens = content.split(" ")
            out = []
            for i, t in enumerate(tokens):
                if not t:
                    out.append(t)
                    continue
                cleaned = re.sub(r"[^\w\.]", "", t.lower())
                prev_token = re.sub(r"[^\w\.]", "", tokens[i-1].lower()) if i > 0 else ""
                next_token = re.sub(r"[^\w\.]", "", tokens[i+1].lower()) if i + 1 < len(tokens) else ""

                # Guard English verb "do" (e.g. "what did i do today", "how do i", "what to do")
                if cleaned == "do" and (prev_token in ["i", "you", "we", "they", "to", "did", "how", "what", "can", "will", "would", "could", "should"] or next_token in ["i", "you", "today", "it", "not", "so", "exercise", "workout"]):
                    out.append(t)
                    continue

                if cleaned in NUMBER_WORDS:
                    val = NUMBER_WORDS[cleaned]
                    out.append(str(int(val) if val.is_integer() else val))
                else:
                    out.append(t)
            res_line = " ".join(out)
            if ends_with_newline:
                res_line += "\n"
            res_lines.append(res_line)
        return "".join(res_lines)

    @staticmethod
    def normalize_text(text: str) -> str:
        """Full deterministic preprocessing pipeline."""
        repaired = AgentNLP.repair_missing_spaces_and_typos(text)
        numbered = AgentNLP.parse_number_tokens(repaired)
        return numbered

    @staticmethod
    def detect_intent(text: str) -> str:
        """Classifies intent using high-precision multilingual patterns."""
        norm = AgentNLP.normalize_text(text)
        lower = norm.lower()

        # 0. Zero quantity check -> GENERAL_CHAT (DO NOT LOG)
        if re.search(r"\b(?:ate|had|consumed|drank|eaten|have|khadha|khadhi|khadhu|khaya|khayi|pidhu|pidhi)\s+0(?:\.0+)?\b|\b0(?:\.0+)?\s*(?:ml|liter|litre|glass|cup|bottle|serving|bowl|plate|piece|nag|katori|vatki|g|kg|scoop)\b|\b(?:ate|had|drank)\s+zero\b", lower):
            return "GENERAL_CHAT"

        # 1. Update / Correction intent
        if any(w in lower for w in [
            "make it", "change to", "update to", "instead of", "actually", "sudharo",
            "badlo", "ferfar", "change karo", "update karo", "not 2 but", "galti se",
            "સુધારો", "બદલો", "ફેરફાર", "બદલ", "बदलो", "अपडेट", "गलती से"
        ]):
            return "UPDATE_FOOD_LOG"

        # 2. Deletion / Removal intent
        if any(w in lower for w in [
            "delete", "remove", "cancel", "hatao", "nikalo", "kadhi nakho",
            "kadho", "delete karo", "remove karo", "cancel karo", "mitado",
            "કાઢી નાખો", "હટાવો", "કેન્સલ", "हटाओ", "डिलीट", "मिटा दो", "रद्द"
        ]):
            return "DELETE_FOOD_LOG"

        # 3. Water Intake Query intent (e.g. "Aaj ketlu pani pidhu?", "How much water did I drink today?", "Aaj kitna pani piya?")
        is_water_query = any(w in lower for w in [
            "ketlu pani pidhu", "ketlu pani", "pani ketlu", "aaj ketlu pani", "ketla glass pani",
            "kitna pani piya", "kitna paani piya", "pani kitna piya", "kitna pani", "kitna paani",
            "how much water did i drink", "how much water today", "how much water have i drank",
            "water intake today", "did i drink enough water", "water status", "how much water is left",
            "how much water left", "water goal reached", "water target", "how many glasses of water",
            "ketlu pani baki", "pani baki chhe", "pani baki hai",
            "કેટલું પાણી પીધું", "કેટલું પાણી", "પાણી કેટલું", "કેટલા ગ્લાસ પાણી",
            "कितना पानी पिया", "पानी कितना पिया", "कितना पानी बाकी"
        ]) or (
            ("water" in lower or "pani" in lower or "paani" in lower or "પાણી" in lower or "पानी" in lower) and
            any(w in lower for w in ["how much", "status", "goal", "target", "ketlu", "kitna", "baki", "left", "reach", "did i", "ketla"])
        )
        if is_water_query:
            return "QUERY_HYDRATION_LOG"

        # 4. Daily Overall Summary intent (e.g. "Aaj ni summary aap", "What did I do today?", "Aaj ka summary batao", "Today's summary")
        is_daily_summary = any(w in lower for w in [
            "aaj ni summary", "aaj nu summary", "aaj no summary", "aaj summary", "summary aap", "summary aapo",
            "aaj ka summary", "aaj ki summary", "aaj ka hisab", "summary batao", "summary do",
            "what did i do today", "what i did today", "what have i done today", "what did i do",
            "aaje su karyu", "aaj su karyu", "aaje ketlu karyu", "aaj maine kya kiya", "aaj kya kiya",
            "today's summary", "todays summary", "daily summary", "my summary today", "give me today's summary",
            "give me daily summary", "show my summary", "show daily summary", "show today's summary",
            "health summary", "fitness summary", "how was my day", "daily fitness summary", "daily report",
            "aaj no report", "aaj ni report", "aaj ki report",
            "આજની સમરી", "આજનું સમરી", "આજનો હિસાબ", "આજે મેં શું કર્યું", "આજે શું કર્યું", "સમરી આપો", "સમરી આપ",
            "आज का सारांश", "आज की समरी", "आज मैंने क्या किया", "आज क्या किया", "सारांश बताओ", "समरी बताओ", "आज का हिसाब"
        ])
        if is_daily_summary:
            return "DAILY_SUMMARY"

        # 5. Food Suggestions intent (e.g. "What should I eat for dinner?", "Suggest healthy food", "Su khavu joiye?", "Kya khana chahiye?")
        is_food_suggestion = any(w in lower for w in [
            "what should i eat", "what to eat", "what can i eat", "what do i eat",
            "suggest food", "suggest healthy food", "suggest meal", "suggest dinner", "suggest lunch",
            "suggest breakfast", "suggest snack", "food suggestion", "meal suggestion", "food suggestions",
            "meal suggestions", "healthy food suggestion", "healthy meal ideas", "healthy dinner ideas",
            "healthy breakfast ideas", "healthy lunch ideas", "what to have for dinner", "what to have for breakfast",
            "what to have for lunch", "what should i have for dinner", "what should i have for lunch",
            "what should i have for breakfast", "healthy snacks to eat", "what healthy food",
            "su khavu joiye", "shu khavu joiye", "su khavu", "shu khavu", "su khau", "shu khau", "aaj su khavu",
            "lunch ma su khau", "dinner ma su khau", "dinner ma su banavu", "savare su khavu", "nasta ma su levu",
            "khavanu suggest karo", "healthy khavanu suggest karo", "su jamvu", "bapor na su khavu",
            "kya khana chahiye", "kya khau", "kya khaye", "kya khayein", "lunch me kya khau", "dinner me kya khau",
            "dinner me kya banau", "khana suggest karo", "kuch healthy batao khane", "nashte me kya khau",
            "kya khana accha", "healthy khana suggest",
            "શું ખાવું જોઈએ", "શું ખાવું", "શું ખાઉં", "ડિનરમાં શું બનાવવું", "લંચમાં શું ખાવું", "નાસ્તામાં શું લેવું", "સ્વસ્થ ખોરાક", "શું જમવું",
            "क्या खाना चाहिए", "क्या खाऊं", "क्या खाएं", "डिनर में क्या बनाऊं", "लंच में क्या खाऊं", "नाश्ते में क्या लें", "हेल्दी खाना"
        ])
        if is_food_suggestion:
            return "FOOD_SUGGESTION"

        # 6. Workout Suggestions intent (e.g. "Suggest an exercise", "What workout should I do today?", "Aaje kai kasrat karu?", "Koi exercise batao")
        is_workout_suggestion = any(w in lower for w in [
            "suggest exercise", "suggest workout", "suggest an exercise", "suggest a workout",
            "what exercise should i do", "what workout should i do", "exercise suggestions",
            "workout suggestions", "give me exercise", "give me workout", "recommend exercise",
            "recommend workout", "which exercise should i do", "exercise suggest karo",
            "workout suggest karo", "kai exercise karu", "kai kasrat karu", "kasrat suggest karo",
            "koi exercise batao", "koi workout batao", "aaj kaunsa workout", "aaje kai kasrat",
            "kai exercise karvi joiye", "kai kasrat karvi joiye", "suggest workout for",
            "કઈ કસરત કરું", "કસરત સજેસ્ટ", "વર્કઆઉટ સજેસ્ટ", "કોઈ કસરત બતાવો",
            "कौन सी एक्सरसाइज करूं", "एक्सरसाइज सजेस्ट करो", "वर्कआउट सजेस्ट करो", "कोई एक्सरसाइज बताओ"
        ])
        if is_workout_suggestion:
            return "WORKOUT_SUGGESTION"

        # 0. Question / Advisory / Negative / Hypothetical check -> GENERAL_CHAT (DO NOT LOG)
        is_hypothetical = any(w in lower for w in [
            "if i eat", "if i have", "might eat", "will eat", "planning to eat", "planning to have", "planning to",
            "plan to eat", "plan to have", "plan hai", "plane hai", "plane chhe", "plan chhe",
            "khane ka plan", "khavu padashe", "khavu padshe", "khana padega",
            "suppose", "assume", "what if", "agar me khau", "jo hu khau", "soch raha hu", "soch raha tha", "soch raha",
            "vicharu chhu", "vichar chhe", "will drink", "planning to drink"
        ])
        is_negative = any(w in lower for w in [
            "did not eat", "have not eaten", "haven't eaten", "havent eaten", "not eat anything", "didn't eat", "not eaten any",
            "not eat anything yet", "didn't have", "did not have", "have not had", "haven't had", "not had any",
            "nathi khadhu", "nathi pidhu", "nahi khaya", "kuch nahi khaya", "kahi nahi khaya", "nahi khai", "nahi khaye",
            "nahi piya", "kahi nathi khadhu", "kahi nathi lidhu", "nahi li", "nahi liya",
            "khadhu nathi", "khadha nathi", "khadhi nathi", "khaya nahi", "khayi nahi", "khaye nahi", "piya nahi",
            "ખાધું નથી", "ખાધા નથી", "ખાધી નથી", "ખાધુ નથી", "પીધું નથી", "લીધું નથી", "લીધી નથી", "કંઈ ખાધું નથી", "કઈ ખાધું નથી", "કંઈ નથી ખાધું",
            "खाया नहीं", "खाई नहीं", "खाए नहीं", "पिया नहीं", "नहीं खाया", "नहीं खाई", "नहीं खाए", "नहीं पिया", "नहीं ली", "नहीं लिया", "कुछ नहीं खाया"
        ])
        is_advisory = any(w in lower for w in [
            "how many calories in", "how many calories are in", "how much protein in", "how much protein is in",
            "is it healthy", "is roti healthy", "is healthy", "should i eat",
            "can i replace", "can i eat", "tell me about", "guide me", "how to lose", "how to gain",
            "ketli calories hoy", "ketlu protein hoy", "kitni calories", "kitna protein",
            "tell me about sleep tracking", "how does water tracking work", "can i drink more water",
            "motivational quote", "motivation"
        ])
        is_question = "?" in lower and not any(w in lower for w in [
            "what did i eat", "summary", "show logs", "show me", "aaj nu summary",
            "protein did i eat", "calories did i eat", "protein today", "calories today",
            "forgot what i ate", "what i ate", "remaining", "ketli calories thai", "calories thai"
        ])

        # Fitness & Workout Question / Recommendation Check -> FITNESS_ADVISORY (DO NOT LOG)
        has_q_word = bool(re.search(r"\b(?:what|how|which|why|give me|suggest|batao|aapo|kya|kaise|kaunse|shu|kem|kaya|kai)\b", lower)) or "?" in lower or any(ch in lower for ch in ["કયા", "શું", "કેમ", "કેવી રીતે", "ફાયદા", "ફાયદો", "क्या", "कैसे", "कौनसे", "फायदे"])
        is_fitness_advisory = any(w in lower for w in [
            "benefits of", "benefit of", "fayda", "fayde", "faida", "faide", "લાભ", "ફાયદા", "ફાયદો", "ફायदे", "लाभ",
            "workout plan", "routine plan", "exercise plan", "beginner workout", "beginner plan", "workout for beginner",
            "stamina", "endurance", "સ્ટેમિના", "स्टैमिना", "दम", "improve my stamina", "improve stamina", "increase stamina",
            "stamina kem", "stamina kaise", "badhaye", "vadharvu", "target the legs", "target legs", "leg exercise", "leg workout",
            "exercises for", "exercise for", "exercises target", "which exercises", "which exercise", "kaya exercise",
            "kaunse exercise", "calories does", "calories burn", "burn calories", "calorie burn", "ketli calories burn",
            "kitni calories burn", "give me a beginner", "how to improve", "how can i", "how do i improve",
            "how to build stamina", "best exercise", "exercises target"
        ]) or (
            has_q_word and any(bool(re.search(pat, lower)) for pat in WORKOUT_PATTERNS)
        )
        if is_fitness_advisory:
            return "FITNESS_ADVISORY"

        if is_hypothetical or is_negative or is_advisory or is_question:
            return "GENERAL_CHAT"

        # 7. Query Food Log
        if any(w in lower for w in [
            "what did i eat", "show my food", "today's calories", "todays calories", "remaining",
            "how many calories did i eat", "how many calories today", "how many calories left", "how many calories do i have",
            "how much protein did i eat", "protein did i eat", "how much protein today", "protein today",
            "ketli calories", "ketlu khadhu", "forgot what i ate",
            "show logs", "show food", "kya khaya",
            "my lunch calories", "remaining calories", "baki calories", "ketli calories thai", "calories thai",
            "daily food summary",
            "શું ખાધું", "કેટલી કેલરી", "क्या खाया", "कितनी कैलोरी"
        ]):
            return "QUERY_FOOD_LOG"

        # Domain terms detection
        # NOTE: Use word-boundary matching for eating/drinking verbs to prevent
        # short tokens like "li" from matching inside words like "khali" (empty).
        has_explicit_food = any(w in lower for w in FOOD_NOUNS)
        has_eating_verb = any(
            bool(re.search(rf"\b{re.escape(v)}\b", lower)) for v in EATING_VERBS
        )
        has_drinking_verb = any(
            bool(re.search(rf"\b{re.escape(v)}\b", lower)) for v in DRINKING_VERBS
        )
        has_workout = any(bool(re.search(pat, lower)) for pat in WORKOUT_PATTERNS)
        
        # Check water (water or paani in non pani puri context)
        has_water = (any(w in lower for w in ["water", "paani", "પાણી", "पानी"]) or 
                     (re.search(r"\bpani\b", lower) and "pani puri" not in lower))

        has_weight = any(w in lower for w in [
            "weight", "vajan", "kilo", "kilos", "kg", "kilogram",
            "વજન", "કિલો", "કિલોગ્રામ", "वजन", "किलो", "किलोग्राम"
        ]) and any(w in lower for w in [
            "my body weight", "my weight", "mera weight", "mera vajan", "maru vajan",
            "વજન", "वजन", "is", "che", "hai", "kg", "kilos", "કિલો", "किलो", "today", "aaj", "aaje"
        ])

        has_sleep = any(w in lower for w in [
            "sleep", "slept", "suvo", "suito", "suto", "suti", "oongh", "neend", "so gaya", "soya", "bed at", "woke up at",
            "hours sleep", "hour sleep", "hr sleep", "hrs sleep", "hours of sleep", "hour of sleep", "kalak suito", "kalak suto",
            "ઊંઘ", "સુઈ ગયો", "સુતો", "સુતી", "सोया", "नींद"
        ])

        # Multi-log check (food + workout or food + water)
        if (has_explicit_food and has_workout) or (has_explicit_food and has_water):
            return "CREATE_MULTI_LOG"

        # Pure domain actions
        if has_water and not has_explicit_food:
            return "CREATE_HYDRATION_LOG"

        if has_workout and not has_explicit_food:
            return "CREATE_ACTIVITY_LOG"

        if has_weight and not has_explicit_food:
            return "CREATE_WEIGHT_LOG"

        if has_sleep and not has_explicit_food:
            return "CREATE_SLEEP_LOG"

        if has_explicit_food or has_eating_verb or has_drinking_verb:
            # Container/tiffin guard: sentences about emptying or handling a
            # lunchbox/tiffin without mentioning an actual food noun are not food
            # logs — they describe a container action, not consumption.
            # Only fire when there is NO explicit food noun present.
            _CONTAINER_WORDS = {"dabbu", "dabba", "tiffin", "lunchbox", "lunch box", "डब्बा"}
            _CONTAINER_ACTIONS = {
                "khali", "saaf", "bharo", "lai", "muki", "rakh", "dho", "pack",
                "empty", "clean", "fill", "खाली", "साफ",
            }
            has_container = any(
                bool(re.search(rf"\b{re.escape(cw)}\b", lower)) for cw in _CONTAINER_WORDS
            )
            has_container_action = any(
                bool(re.search(rf"\b{re.escape(ca)}\b", lower)) for ca in _CONTAINER_ACTIONS
            )
            if has_container and has_container_action and not has_explicit_food:
                return "GENERAL_CHAT"
            return "CREATE_FOOD_LOG"

        return "GENERAL_CHAT"

    @staticmethod
    def extract_weight_entity(text: str) -> Dict[str, Any]:
        """Extracts weight value in kg."""
        norm = AgentNLP.normalize_text(text)
        m = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:kg|kilos?|કિલો|किलो)?\b", norm)
        if m:
            val = float(m.group(1))
            if 30 <= val <= 250:
                return {"weightKg": val, "unit": "kg"}
        return {"weightKg": 70.0, "unit": "kg"}

    @staticmethod
    def extract_hydration_entities(text: str) -> List[Dict[str, Any]]:
        """
        Extracts all hydration items from text with their specific amounts and explicit times.
        Supports:
        - "400ml water", "1 ltr water", "300ml water"
        - "lemon water 1 glass" (filtered out since it's a beverage handled as food)
        """
        norm = AgentNLP.normalize_text(text)
        lower = norm.lower()
        local_now = TimeService.get_current_local_datetime()

        water_terms_regex = r"water|paani|પાણી|पानी|pani"
        excluded_foods = ["pani puri", "panipuri", "water melon", "watermelon", "પાણીપુરી", "પાણી પૂરી", "પાની પુરી", "पानी पुरी"]

        results = []
        lines = [line.strip() for line in norm.splitlines() if line.strip()]
        if not lines:
            lines = [lower]

        active_period = None
        for line in lines:
            l_low = line.lower()
            if any(w in l_low for w in ["morning", "savar", "savare", "saware", "subah", "સવાર", "સવારે", "सुबह"]):
                active_period = "morning"
            elif any(w in l_low for w in ["afternoon", "bapor", "bapore", "dopahar", "બપોર", "બપોરે", "दोपहर"]):
                active_period = "afternoon"
            elif any(w in l_low for w in ["evening", "sanj", "sanje", "shaam", "સાંજ", "સાંજે", "शाम"]):
                active_period = "evening"
            elif any(w in l_low for w in ["night", "raat", "raate", "રાત", "રાત્રે", "रात"]):
                active_period = "night"

            time_input = f"{active_period} {line}" if (active_period and not any(w in l_low for w in ["am", "pm", "morning", "evening", "night", "savar", "subah", "bapor", "sanj", "raat"])) else line
            line_dt, has_line_time = TimeService.extract_time_from_text(time_input, reference_time=local_now)
            effective_dt = line_dt if has_line_time else local_now

            clauses = re.split(r",| and | ane | aur | અને | और | with | along with | sathe | સાથે | ساتھ میں | साथ में |\+", line, flags=re.I)
            for clause in clauses:
                c = clause.strip()
                if not c:
                    continue

                c_lower = c.lower()
                if any(ex in c_lower for ex in excluded_foods):
                    continue

                if not re.search(rf"\b{water_terms_regex}\b", c_lower):
                    continue

                bev_name = "Water"
                if any(w in c_lower for w in ["lemon water", "lamon water", "nimbu pani", "nimbu paani", "limbu pani", "leembu pani", "લીંબુ પાણી", "નીંબુ પાની"]):
                    bev_name = "Lemon Water"
                elif any(w in c_lower for w in ["coconut water", "nariyal pani", "nariyal paani", "નાળિયેર પાણી", "નારિયલ પાની"]):
                    bev_name = "Coconut Water"
                elif any(w in c_lower for w in ["jeera water", "jeera pani", "જીરું પાણી"]):
                    bev_name = "Jeera Water"

                c_time_input = f"{active_period} {c}" if (active_period and not any(w in c_lower for w in ["am", "pm", "morning", "evening", "night", "savar", "subah", "bapor", "sanj", "raat"])) else c
                clause_dt, has_clause_time = TimeService.extract_time_from_text(c_time_input, reference_time=local_now)
                item_has_time = has_clause_time or has_line_time
                item_dt = clause_dt if has_clause_time else effective_dt

                c_no_time = re.sub(r"(?:at\s+|@\s*)?\b\d{1,2}[:.]\d{2}(?:\s*(?:am|pm|a\.m\.|p\.m\.))?\b", " ", c, flags=re.I)
                c_no_time = re.sub(r"\b\d{1,2}\s*(?:am|pm|a\.m\.|p\.m\.)\b", " ", c_no_time, flags=re.I)

                m_qty = re.search(r"\b(\d+(?:\.\d+)?)\b", c_no_time)
                qty = float(m_qty.group(1)) if m_qty else 1.0

                c_lower_clean = c_no_time.lower()
                amount_ml = 250.0
                if "bottle" in c_lower_clean or "botle" in c_lower_clean or "બોટલ" in c_lower_clean or "बोतल" in c_lower_clean:
                    amount_ml = 750.0 * qty
                elif "glass" in c_lower_clean or "glaas" in c_lower_clean or "ગ્લાસ" in c_lower_clean or "ग्लास" in c_lower_clean:
                    amount_ml = 250.0 * qty
                elif "cup" in c_lower_clean or "kapp" in c_lower_clean or "કપ" in c_lower_clean or "कप" in c_lower_clean:
                    amount_ml = 200.0 * qty
                elif any(re.search(rf"\b{re.escape(w)}\b", c_lower_clean) for w in ["liter", "litre", "ltr", "liters", "litres", "લીટર", "लीटर"]) or re.search(r"\b\d+\s*l\b", c_lower_clean):
                    amount_ml = 1000.0 * qty
                elif "ml" in c_lower_clean:
                    amount_ml = qty
                else:
                    amount_ml = 250.0 * qty

                if amount_ml > 0:
                    results.append({
                        "beverage_name": bev_name,
                        "beverageName": bev_name,
                        "waterAmount": amount_ml,
                        "amountMl": amount_ml,
                        "amount_ml": amount_ml,
                        "unit": "ml",
                        "logged_at": item_dt.isoformat(),
                        "has_explicit_time": item_has_time,
                        "time_formatted": TimeService.format_time(item_dt) if item_has_time else "",
                        "raw_text": c,
                    })

        return results

    @staticmethod
    def extract_hydration_entity(text: str) -> Dict[str, Any]:
        """Extracts primary water quantity in ml (backward-compatible)."""
        ents = AgentNLP.extract_hydration_entities(text)
        if ents:
            return ents[0]
        return {"waterAmount": 250.0, "amountMl": 250.0, "amount_ml": 250.0, "unit": "ml"}

    @staticmethod
    def extract_activity_entities(text: str) -> List[Dict[str, Any]]:
        """
        Extracts all exercise activities, durations, repetitions, and sets.
        Supports single and multiple exercises across English, Hindi, Gujarati, Hinglish, Gujlish.
        """
        norm = AgentNLP.normalize_text(text)
        lower = norm.lower()
        local_now = TimeService.get_current_local_datetime()
        global_dt, has_global_time = TimeService.extract_time_from_text(text, reference_time=local_now)
        active_time_dt = global_dt if has_global_time else local_now

        lines = [line.strip() for line in norm.splitlines() if line.strip()]
        if not lines:
            lines = [lower]

        exercise_map = [
            (r"\bsquats?\b|સ્ક્વોટ્સ?|સ્કવોટ્સ?|स्क्वैट्स?", "Squats", 5.0, True),
            (r"\bpush-?ups?\b|પુશઅપ્સ?|पुशअप્સ?|\bદંડ\b", "Push-ups", 4.5, True),
            (r"\bpull-?ups?\b|પુલઅપ્સ?|पुलअप्स?|ચિનઅપ", "Pull-ups", 5.0, True),
            (r"\blunges?\b|લંજીસ?|લંજ", "Lunges", 4.5, True),
            (r"\bcrunches?\b|sit-?ups?|ક્રંચ|क्रंचेस", "Crunches", 3.8, True),
            (r"\bplanks?\b|પ્લેન્ક|પ્લેંક|प्लैंक", "Plank", 3.5, False),
            (r"\bburpees?\b|બર્પી|बर्पी", "Burpees", 8.0, True),
            (r"\bjump(?:ing)?\s*jacks?\b|જમ્પિંગ\s*જેક", "Jumping Jacks", 8.0, True),
            (r"\bjump\s*rope\b|skipping|દોરડા\s*કૂદવા|रस्सी\s*कूद", "Jump Rope", 10.0, False),
            (r"\bbench\s*press\b|બેન્ચ\s*પ્રેસ|बेंच\s*प्रेस", "Bench Press", 5.5, True),
            (r"\bdeadlifts?\b|ડેડલિફ્ટ|डेडલિफ्ट", "Deadlift", 6.0, True),
            (r"\bback\b|\bપીઠ\b", "Back Workout", 5.5, False),
            (r"\bbiceps?\b|\bબાઈસેપ્સ?\b", "Biceps Workout", 5.5, False),
            (r"\btriceps?\b|\bટ્રાઈસેપ્સ?\b", "Triceps Workout", 5.5, False),
            (r"\bchest\b|\bછાતી\b", "Chest Workout", 5.5, False),
            (r"\blegs?\b|\bપગ\b", "Legs Workout", 5.5, False),
            (r"\bshoulders?\b|\bખભા\b", "Shoulders Workout", 5.5, False),
            (r"\babs\b|\bcore\b", "Abs Workout", 4.5, False),
            (r"\brun(?:ning)?\b|\bran\b|દોડ|दौड़", "Running", 8.5, False),
            (r"\bwalk(?:ing)?\b|\bwalked\b|ચાલ|ટહેલ|टहल", "Walking", 3.5, False),
            (r"\bcycl(?:ing|e)\b|સાયકલ|साइकिल", "Cycling", 6.0, False),
            (r"\bswim(?:ming)?\b|તરવું|तैरना", "Swimming", 7.0, False),
            (r"\byoga\b|યોગ|योग", "Yoga", 3.0, False),
            (r"\bbadminton\b", "Badminton", 5.5, False),
            (r"\bcricket\b", "Cricket", 5.0, False),
            (r"\bstrength\s*training\b|સ્ટ્રેન્થ\s*ટ્રેનિંગ|स्ट्रेंथ\s*ट्रेनिंग", "Strength Training", 5.5, False),
            (r"\bgym\b|(?<!pre[-\s])\bworkout\b|\bexercise\b|\bkasrat\b|\bvyayam\b|કસરત|વર્કઆઉટ|વ્યાયામ|व्यायाम|कसरत", "Workout", 5.0, False),
        ]

        extracted = []
        seen_names = set()

        active_period = None
        for line in lines:
            line_lower = line.lower()
            if any(w in line_lower for w in ["morning", "savar", "savare", "saware", "subah", "સવાર", "સવારે", "सुबह"]):
                active_period = "morning"
            elif any(w in line_lower for w in ["afternoon", "bapor", "bapore", "dopahar", "બપોર", "બપોરે", "दोपहर"]):
                active_period = "afternoon"
            elif any(w in line_lower for w in ["evening", "sanj", "sanje", "shaam", "સાંજ", "સાંજે", "शाम"]):
                active_period = "evening"
            elif any(w in line_lower for w in ["night", "raat", "raate", "રાત", "રાત્રે", "रात"]):
                active_period = "night"

            time_input = f"{active_period} {line}" if (active_period and not any(w in line_lower for w in ["am", "pm", "morning", "evening", "night", "savar", "subah", "bapor", "sanj", "raat"])) else line
            range_info = TimeService.extract_time_range_from_text(time_input, reference_time=local_now)
            line_dt, has_line_time = TimeService.extract_time_from_text(time_input, reference_time=local_now)
            if range_info:
                line_dt = range_info["start_dt"]
                has_line_time = True
                active_time_dt = line_dt
            elif has_line_time:
                active_time_dt = line_dt

            # Strip raw time range match from processed line so digits aren't treated as duration/reps
            line_processed = line_lower
            if range_info:
                line_processed = line_processed.replace(range_info["raw_match"].lower(), " ")

            # Split line into clauses
            clauses = re.split(r"[,;()&+]|\band\b|\bane\b|\baur\b|\bતથા\b|\bઅને\b", line_processed)
            clauses = [c.strip() for c in clauses if c.strip()]
            if not clauses:
                clauses = [line_processed]

            line_matched = []
            for clause in clauses:
                matched_name = None
                matched_met = 4.0
                is_rep_based = False
                matched_pat = ""

                for pat, name, met, rep_flag in exercise_map:
                    if re.search(pat, clause):
                        matched_name = name
                        matched_met = met
                        is_rep_based = rep_flag
                        matched_pat = pat
                        break

                if not matched_name or matched_name in seen_names:
                    continue

                # 1. Extract sets if any
                sets_val = 1
                m_sets = re.search(r"(\d+)\s*(?:sets?|સેટ|सेट)", clause)
                if m_sets:
                    sets_val = int(m_sets.group(1))

                # 2. Extract reps if any
                reps_val = None
                m_reps = re.search(r"(\d+)\s*(?:reps?|repetitions?|rep|રેપ|रेप|દાણા|વખત)", clause)
                if m_reps:
                    reps_val = int(m_reps.group(1))
                elif is_rep_based:
                    m_num = re.search(r"(\d+)\s*(?:" + matched_pat + r")|(?:" + matched_pat + r")\s*(\d+)", clause)
                    if m_num:
                        num_str = m_num.group(1) or m_num.group(2)
                        if num_str:
                            reps_val = int(num_str)

                # 3. Extract explicit duration in minutes if any
                duration_val = None
                m_min = re.search(r"(\d+(?:\.\d+)?)\s*(?:minutes?|mins?|min|મિનિટ|मिनट)", clause)
                if m_min:
                    duration_val = float(m_min.group(1))
                else:
                    m_hr = re.search(r"(\d+(?:\.\d+)?)\s*(?:hours?|hrs?|hr|કલાક|घंटे|घंटा)", clause)
                    if m_hr:
                        duration_val = float(m_hr.group(1)) * 60.0

                c_time_input = f"{active_period} {clause}" if (active_period and not any(w in clause.lower() for w in ["am", "pm", "morning", "evening", "night", "savar", "subah", "bapor", "sanj", "raat"])) else clause
                clause_dt, has_clause_time = TimeService.extract_time_from_text(c_time_input, reference_time=local_now)
                if has_clause_time:
                    active_time_dt = clause_dt
                    act_dt = clause_dt
                elif has_line_time:
                    act_dt = line_dt
                else:
                    act_dt = active_time_dt

                line_matched.append({
                    "matched_name": matched_name,
                    "matched_met": matched_met,
                    "reps_val": reps_val,
                    "sets_val": sets_val,
                    "duration_val": duration_val,
                    "is_rep_based": is_rep_based,
                    "clause": clause,
                    "act_dt": act_dt,
                })

            # If specific exercises are matched on this line, drop generic "Workout"
            has_specific = any(it["matched_name"] != "Workout" for it in line_matched)
            if has_specific:
                line_matched = [it for it in line_matched if it["matched_name"] != "Workout"]

            # Distribute time range duration across exercises that didn't specify individual duration
            if range_info:
                unspecified = [it for it in line_matched if it["duration_val"] is None]
                if unspecified:
                    distributed_mins = round(range_info["duration_minutes"] / len(unspecified), 1)
                    for it in unspecified:
                        it["duration_val"] = distributed_mins
                        it["time_formatted"] = range_info["range_str"]

            for it in line_matched:
                had_explicit_measure = (it["duration_val"] is not None or it["reps_val"] is not None or bool(range_info))
                requires_clarification = not had_explicit_measure

                if it["duration_val"] is None and it["reps_val"] is not None:
                    total_reps = it["reps_val"] * it["sets_val"]
                    it["duration_val"] = max(1.0, round(total_reps * 0.08, 1))

                if it["duration_val"] is None:
                    it["duration_val"] = 30.0

                time_formatted = it.get("time_formatted") or (range_info["range_str"] if range_info else TimeService.format_time(it["act_dt"]))

                seen_names.add(it["matched_name"])
                extracted.append({
                    "activity": it["matched_name"],
                    "activity_name": it["matched_name"],
                    "reps": it["reps_val"],
                    "sets": it["sets_val"] if it["reps_val"] else None,
                    "durationMinutes": it["duration_val"],
                    "intensity": "MEDIUM",
                    "metValue": it["matched_met"],
                    "logged_at": it["act_dt"].isoformat(),
                    "timeFormatted": time_formatted,
                    "requiresClarification": requires_clarification,
                })

        # Fallback if no clause matched but whole text had an exercise:
        if not extracted:
            for pat, name, met, rep_flag in exercise_map:
                if re.search(pat, lower):
                    mins = 30.0
                    m_min = re.search(r"(\d+(?:\.\d+)?)\s*(?:minutes?|mins?|min|મિનિટ|मिनट)", lower)
                    if m_min:
                        mins = float(m_min.group(1))
                    reps = None
                    m_rep = re.search(r"(\d+)\s*(?:reps?|rep|રેપ|रेप)", lower)
                    if m_rep:
                        reps = int(m_rep.group(1))
                        mins = max(1.0, round(reps * 0.08, 1))
                    act_dt = global_dt if has_global_time else local_now
                    extracted.append({
                        "activity": name,
                        "activity_name": name,
                        "reps": reps,
                        "sets": 1 if reps else None,
                        "durationMinutes": mins,
                        "intensity": "MEDIUM",
                        "metValue": met,
                        "logged_at": act_dt.isoformat(),
                        "timeFormatted": TimeService.format_time(act_dt),
                        "requiresClarification": (m_min is None and m_rep is None),
                    })
                    break

        if not extracted:
            act_dt = global_dt if has_global_time else local_now
            extracted.append({
                "activity": "Workout",
                "activity_name": "Workout",
                "reps": None,
                "sets": None,
                "durationMinutes": 30.0,
                "intensity": "MEDIUM",
                "metValue": 5.0,
                "logged_at": act_dt.isoformat(),
                "timeFormatted": TimeService.format_time(act_dt),
                "requiresClarification": True,
            })

        return extracted

    @staticmethod
    def extract_activity_entity(text: str) -> Dict[str, Any]:
        """Extracts primary exercise activity entity (backward-compatible)."""
        entities = AgentNLP.extract_activity_entities(text)
        return entities[0]

    @staticmethod
    def extract_sleep_entity(text: str) -> Dict[str, Any]:
        """Extracts sleep duration in minutes."""
        norm = AgentNLP.normalize_text(text)
        lower = norm.lower()
        mins = 480
        m = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:hour|hours|hr|hrs|કલાક|घंटे)\b", lower)
        if m:
            mins = int(float(m.group(1)) * 60)
        else:
            m2 = re.search(r"\b(\d+)\b", lower)
            if m2:
                v = int(m2.group(1))
                if v <= 24:
                    mins = v * 60
                else:
                    mins = v
        return {"durationMinutes": mins, "quality": "GOOD"}

    @staticmethod
    def extract_food_entities_heuristically(text: str) -> List[Dict[str, Any]]:
        """Fallback entity extractor for food messages with typos, quantities, and units across multiple lines."""
        norm = AgentNLP.normalize_text(text)
        local_now = TimeService.get_current_local_datetime()
        lines = [line.strip() for line in norm.splitlines() if line.strip()]
        if not lines:
            lines = [norm]

        has_active_time = False
        active_time_dt = local_now
        active_meal = "—"

        results = []

        active_period = None
        for line in lines:
            line = re.sub(r"\b(dal|daal|દાળ|દાલ|दाल)\s+(rice|bhat|chawal|ભાત|ચોખા|चावल)\b", r"\1 and \2", line, flags=re.I)
            line = re.sub(r"\b(roti|rotli|chapati|રોટલી|रोटी)\s+(dal|daal|sabzi|shak|દાળ|શાક|दाल|सब्जी)\b", r"\1 and \2", line, flags=re.I)
            line = re.sub(r"\b(tea|chai|coffee)\s+with\s+milk\b", r"\1_with_milk", line, flags=re.I)
            
            l_low = line.lower()
            if any(w in l_low for w in ["morning", "savar", "savare", "saware", "subah", "સવાર", "સવારે", "सुबह"]):
                active_period = "morning"
            elif any(w in l_low for w in ["afternoon", "bapor", "bapore", "dopahar", "બપોર", "બપોરે", "दोपहर"]):
                active_period = "afternoon"
            elif any(w in l_low for w in ["evening", "sanj", "sanje", "shaam", "સાંજ", "સાંજે", "शाम"]):
                active_period = "evening"
            elif any(w in l_low for w in ["night", "raat", "raate", "રાત", "રાત્રે", "रात"]):
                active_period = "night"

            time_input = f"{active_period} {line}" if (active_period and not any(w in l_low for w in ["am", "pm", "morning", "evening", "night", "savar", "subah", "bapor", "sanj", "raat"])) else line
            line_dt, has_line_time = TimeService.extract_time_from_text(time_input, reference_time=local_now)
            if has_line_time:
                active_time_dt = line_dt
                has_active_time = True
                active_meal = TimeService.infer_meal_type(line, dt=line_dt)

            effective_line_dt = line_dt if has_line_time else (active_time_dt if has_active_time else None)
            line_meal = TimeService.infer_meal_type(line, dt=effective_line_dt)
            if line_meal != "—":
                active_meal = line_meal

            # Split message into clauses using separators
            clauses = re.split(r",| and | ane | aur | અને | અને\s+| અને| aur\s+| और | sath me | sathe | સાથે | સાથે\s+| साथ में | with |\+", line, flags=re.I)

            for clause in clauses:
                clause = clause.strip().replace("_with_milk", " with milk")
                if not clause:
                    continue

                c_low = clause.lower()

                # Meta commands and confirmation phrases (e.g., "Aa badhu log kari do", "log all", "log this")
                is_meta = (
                    any(bool(re.search(pat, c_low)) for pat in [
                        r"\blog\s*(?:kari\s*do|karo|kar|do|kardo|karo\s*ne|de|dena|kariye|kijiye)\b",
                        r"\b(?:aa\s*badhu|badhu|badhu\s*j|aa\s*badha|aa\s*badhu\s*log|aa\s*badhu\s*save)\b",
                        r"\b(?:ye\s*sab|ye\s*sab\s*log|ye\s*bhi|sab\s*log\s*karo|yeh\s*sab)\b",
                        r"\b(?:log\s*all|save\s*all|track\s*all|log\s*this|save\s*this|track\s*this)\b",
                        r"\b(?:record\s*this|record\s*all|enter\s*this)\b",
                        r"(?:આ\s*બધું|બધું\s*લોગ|લોગ\s*કરી\s*દો|લોગ\s*કરો|આ\s*બધુ)",
                        r"(?:ये\s*सब|सब\s*लॉग|लॉग\s*कर\s*दो|लॉग\s*करो)",
                    ])
                    or c_low in ["aa badhu", "badhu", "ye sab", "sab log", "log kari do", "log kar do", "log this"]
                )
                if is_meta:
                    continue

                is_culinary_water = any(w in c_low for w in [
                    "lemon water", "nimbu pani", "nimbu paani", "leembu pani",
                    "coconut water", "nariyal pani", "nariyal paani", "jeera water", "jeera pani",
                    "detox water", "pani puri", "water melon", "watermelon",
                    "પાણીપુરી", "પાણી પૂરી", "લીંબુ પાણી", "નીંબુ પાની", "પાની પુરી", "पानी पुरी"
                ])

                # Skip pure water clauses
                is_pure_water = (any(w in c_low for w in ["pani", "water", "watwr", "paani", "પાણી", "પાની", "पानी"]) and not is_culinary_water)
                if is_pure_water:
                    continue

                # Skip exercise, muscle groups, or sleep (protect pre workout / pre-workout as food!)
                is_pre_workout = bool(re.search(r"\bpre[-\s]?workout\b", c_low))
                is_activity_or_sleep = False
                if not is_pre_workout:
                    is_activity_or_sleep = (
                        any(bool(re.search(pat, c_low)) for pat in [
                            r"\b(?:walk|walked|walking|run|running|ran|gym|cycling|swimming|yoga|badminton|cricket)\b",
                            r"\b(?:kasrat|vyayam|cardio|stretching|aerobics|hiit)\b",
                            r"(?<!pre[-\s])\bworkout\b",
                            r"\b(?:biceps?|triceps?|delts?|quads?|hamstrings?|glutes?|calves|abs|core)\b",
                            r"\bback\b(?!\s+(?:tea|coffee))",
                            r"\b(?:bench\s*press|push-?ups?|pull-?ups?|squats?|deadlifts?|crunches?|planks?|lunges?|burpees?)\b",
                            r"\b(?:sleep|slept|oongh|neend|suto|suvo)\b",
                        ])
                        or any(w in c_low for w in ["કસરત", "વ્યાયામ", "ચાલ", "દોડ", "યોગ", "ઊંઘ", "નીંદ", "સોયા", "सोया"])
                    )

                if is_activity_or_sleep:
                    continue

                # Strip SQL injection attempts and benchmark noise
                clause = re.sub(r";\s*DROP TABLE.*|;\s*--.*", "", clause, flags=re.IGNORECASE)
                clause = re.sub(r"\bpleez\s+trac\w*\b|\bpleez\b|\btrac\b", "", clause, flags=re.IGNORECASE)
                clause = re.sub(r'\{"user_id".*\}', '', clause)

                c_time_input = f"{active_period} {clause}" if (active_period and not any(w in c_low for w in ["am", "pm", "morning", "evening", "night", "savar", "subah", "bapor", "sanj", "raat"])) else clause
                clause_dt, has_clause_time = TimeService.extract_time_from_text(c_time_input, reference_time=local_now)
                if has_clause_time:
                    active_time_dt = clause_dt
                    has_active_time = True
                    active_meal = TimeService.infer_meal_type(clause, dt=clause_dt)

                item_has_exp_time = bool(has_clause_time or has_line_time or has_active_time)
                item_dt = clause_dt if has_clause_time else (line_dt if has_line_time else (active_time_dt if has_active_time else local_now))
                item_meal = TimeService.infer_meal_type(clause, dt=clause_dt if has_clause_time else effective_line_dt)
                if item_meal == "—" and line_meal != "—":
                    item_meal = line_meal
                if item_meal == "—" and active_meal != "—":
                    item_meal = active_meal

                # Strip explicit time tokens before quantity extraction to avoid treating '8:30' as quantity '8'
                clause_no_time = re.sub(r"(?:at\s+|@\s*)?\b\d{1,2}[:.]\d{2}(?:\s*(?:am|pm|a\.m\.|p\.m\.))?\b", " ", clause, flags=re.I)
                clause_no_time = re.sub(r"\b\d{1,2}\s*(?:am|pm|a\.m\.|p\.m\.)\b", " ", clause_no_time, flags=re.I)

                # Extract quantity
                has_explicit_qty = False
                qty = 1.0
                num_match = re.search(r"\b(\d+(?:\.\d+)?)\b", clause_no_time)
                if num_match:
                    try:
                        qty = float(num_match.group(1))
                        has_explicit_qty = True
                    except Exception:
                        qty = 1.0
                else:
                    for nw_word, nw_val in NUMBER_WORDS.items():
                        if any(ord(c) > 127 for c in nw_word):
                            if re.search(rf"(?<![\u0A80-\u0AFF\u0900-\u097F]){re.escape(nw_word)}(?![\u0A80-\u0AFF\u0900-\u097F])", clause_no_time):
                                qty = nw_val
                                has_explicit_qty = True
                                break
                        else:
                            if re.search(rf"\b{re.escape(nw_word)}\b", clause_no_time, flags=re.I):
                                qty = nw_val
                                has_explicit_qty = True
                                break
                    if not has_explicit_qty and any(w in clause_no_time.lower() for w in ["thodu", "thoda", "thodi", "thodak", "zara", "thora", "થોડું", "થોડી", "थोड़ा", "थोड़ी"]):
                        qty = 0.5
                        has_explicit_qty = True

                # Extract unit safely with word boundaries for short keys
                unit = "serving"
                for u_raw in sorted(UNIT_MAP.keys(), key=len, reverse=True):
                    if any(ord(c) > 127 for c in u_raw):
                        if re.search(rf"(?<![\u0A80-\u0AFF\u0900-\u097F]){re.escape(u_raw)}(?![\u0A80-\u0AFF\u0900-\u097F])", clause):
                            unit = UNIT_MAP[u_raw]
                            break
                    else:
                        if re.search(rf"\b{re.escape(u_raw)}\b", clause, flags=re.I):
                            unit = UNIT_MAP[u_raw]
                            break

                # Clean food phrase by stripping numbers, units, verbs, and filler words
                clean = clause
                clean = re.sub(r"^\d+(\.\d+)?", "", clean)
                clean = re.sub(r"\b\d+(\.\d+)?\b", "", clean)
                for nw_word in sorted(NUMBER_WORDS.keys(), key=len, reverse=True):
                    if any(ord(c) > 127 for c in nw_word):
                        clean = re.sub(rf"(?<![\u0A80-\u0AFF\u0900-\u097F]){re.escape(nw_word)}(?![\u0A80-\u0AFF\u0900-\u097F])", " ", clean)
                    else:
                        clean = re.sub(rf"\b{re.escape(nw_word)}\b", " ", clean, flags=re.I)
                for u_raw in sorted(UNIT_MAP.keys(), key=len, reverse=True):
                    if any(ord(c) > 127 for c in u_raw):
                        clean = re.sub(rf"(?<![\u0A80-\u0AFF\u0900-\u097F]){re.escape(u_raw)}(?![\u0A80-\u0AFF\u0900-\u097F])", " ", clean)
                    else:
                        clean = re.sub(rf"\b{re.escape(u_raw)}\b", " ", clean, flags=re.I)

                # Remove time words, postpositions, informal modifiers, and eating verbs
                clean = re.sub(
                    r"\b(?:morning|afternoon|evening|night|breakfast|lunch|dinner|snack|savar|savare|saware|sawar|savaar|bapor|bapore|sanj|sanje|saanj|saanje|sanju|raat|raate|subah|subha|dopahar|shaam|sham|shami)\b"
                    r"|\b(?:thodu|thoda|thodi|thodak|zara|thora|kam|thoda sa|thodi si|થોડું|થોડી|थोड़ा|थोड़ी)\b"
                    r"|\b(?:ma|maa|me|mein|ko|ne|nu|na|ni|no|thi|par|pe|se|of|for|in|at|on|with)\b"
                    r"|\b(?:i|my|mine|me|maine|hamne|aaj|aaje|today|please|track|just now|yesterday|kal)\b"
                    r"|\b(?:and|ane|aur|sathe|sath|along with)\b"
                    r"|\b(?:ate|had|eaten|have|drank|drink|drinking|khadha|khadhi|khadhu|khadho|khado|khaye|khaya|khayi|khalo|pidhi|pidhu|pidha|pidho|pido|piya|piyi|peeli|peena|lidhi|lidhu|lidho|lido|leedhi|leedhu|liya|li)\b"
                    r"|\b(?:che|tha|thi|the|hata|hati|chho|chhe)\b"
                    r"|(?:મેં|ખાધો|ખાધી|ખાધું|ખાધા|લીધો|લીધી|લીધું|લીધા|પીધો|પીધું|પીધી|પીધા|છે|હતી|હતો|હતા|આજે|બપોરે|બપોર|સવાર|સવારે|સાંજ|સાંજે|રાત્રે|રાત|સાથે|નાસ્તો|વાળુ|વાળું|માં|ના|ની|નો|નું|ને|થી|પર|માટે)"
                    r"|(?:मैंने|खाया|खाई|खाए|पिया|पी|लिया|ली|है|था|थी|आज|सुबह|दोपहर|रात|साथ|नाश्ता|में|का|की|के|को|से|पर|पे|ने|लिए)",
                    " ",
                    clean,
                    flags=re.I
                )
                clean = re.sub(r"[^\w\s\u0A80-\u0AFF\u0900-\u097F]", " ", clean).strip()
                clean = re.sub(r"\s+", " ", clean).strip()

                if clean:
                    if clean.lower() in ["aa badhu", "badhu", "ye sab", "sab", "log", "all", "today", "aaj", "aaje", "badhu j"]:
                        continue
                    canonical = None
                    is_recognized = False

                    # 1. Exact lookup
                    if clean.lower() in INDIAN_FOOD_SYNONYMS:
                        canonical = INDIAN_FOOD_SYNONYMS[clean.lower()]
                        is_recognized = True

                    # 2. Check multi-word phrase keys first (longest first) with strict boundaries
                    if not canonical:
                        for food_key in sorted(INDIAN_FOOD_SYNONYMS.keys(), key=len, reverse=True):
                            if any(ord(c) > 127 for c in food_key):
                                if food_key == clean or food_key in clean.split() or f" {food_key} " in f" {clean} ":
                                    canonical = INDIAN_FOOD_SYNONYMS[food_key]
                                    is_recognized = True
                                    break
                            else:
                                if re.search(rf"\b{re.escape(food_key)}\b", clean, flags=re.I):
                                    canonical = INDIAN_FOOD_SYNONYMS[food_key]
                                    is_recognized = True
                                    break

                    # 3. Check single tokens — but only after trying the full cleaned phrase
                    #    to avoid losing compound foods like "paneer sabzi" to single-token
                    #    "sabzi" lookup.
                    if not canonical:
                        # 3a. Check if the full clean phrase is itself a synonym key (catches
                        #     multi-word entries like "paneer tikka", "aloo sabzi" etc.).
                        full_key = clean.lower()
                        if full_key in INDIAN_FOOD_SYNONYMS:
                            canonical = INDIAN_FOOD_SYNONYMS[full_key]
                            is_recognized = True

                    if not canonical:
                        tokens = clean.split()
                        for t in tokens:
                            if t.lower() in INDIAN_FOOD_SYNONYMS:
                                canonical = INDIAN_FOOD_SYNONYMS[t.lower()]
                                is_recognized = True
                                break

                    # 4. Check known FOOD_NOUNS with strict boundaries
                    if not canonical:
                        for noun in sorted(FOOD_NOUNS, key=len, reverse=True):
                            if any(ord(c) > 127 for c in noun):
                                if noun == clean or noun in clean.split() or f" {noun} " in f" {clean} ":
                                    canonical = noun.title()
                                    is_recognized = True
                                    break
                            else:
                                if re.search(rf"\b{re.escape(noun)}\b", clean, flags=re.I):
                                    canonical = noun.title()
                                    is_recognized = True
                                    break

                    # If unrecognized, preserve user's exact food name; do NOT invent or guess random foods
                    if not canonical:
                        canonical = clean.title()

                    # Context-aware default unit when unit was not specified or quantity was not explicitly given
                    if not has_explicit_qty or unit == "serving":
                        c_lower = canonical.lower()
                        if any(w in c_lower for w in ["powder", "whey", "pre workout", "preworkout"]):
                            unit = "scoop"
                        elif any(w in c_lower for w in ["shake", "smoothie"]):
                            unit = "scoop"
                        elif any(w in c_lower for w in ["coffee", "tea", "chai"]):
                            unit = "cup"
                        elif any(w in c_lower for w in ["milk", "doodh", "dudh", "chaas", "chhas", "lassi", "juice"]):
                            unit = "glass"
                        elif any(w in c_lower for w in ["roti", "rotli", "bhakri", "thepla", "egg", "banana", "apple", "chapati", "phulka", "naan", "paratha", "poori"]):
                            unit = "piece"
                        elif any(w in c_lower for w in ["dal", "daal", "rice", "chawal", "khichdi", "sabzi", "shaak", "curd", "dahi", "salad"]):
                            unit = "bowl"

                    if not has_explicit_qty:
                        qty = 1.0

                    confidence = 0.95 if is_recognized else 0.3
                    requires_clarification = not is_recognized
                    clarification_reason = "UNKNOWN_FOOD" if not is_recognized else None

                    results.append({
                        "food": canonical,
                        "food_name": canonical,
                        "quantity": qty,
                        "unit": unit,
                        "mealType": item_meal,
                        "meal_type": item_meal,
                        "logged_at": item_dt.isoformat(),
                        "has_explicit_time": item_has_exp_time,
                        "timeFormatted": TimeService.format_time(item_dt) if item_has_exp_time else "",
                        "confidence": confidence,
                        "is_recognized": is_recognized,
                        "has_explicit_quantity": has_explicit_qty,
                        "requires_clarification": requires_clarification,
                        "clarification_reason": clarification_reason,
                        "raw_text": clause,
                    })

        return results

    @staticmethod
    def extract_structured_actions(text: str) -> List[Dict[str, Any]]:
        """
        Extracts all valid structured actions (Food, Activity, Hydration) from the message.
        """
        norm = AgentNLP.normalize_text(text)
        actions = []

        # 1. Foods
        foods = AgentNLP.extract_food_entities_heuristically(text)
        for f in foods:
            actions.append({
                "type": "CREATE_FOOD_LOG",
                "food_name": f["food"],
                "quantity": f["quantity"],
                "unit": f["unit"],
                "logged_at": f.get("logged_at"),
                "has_explicit_time": f.get("has_explicit_time", False),
                "time_formatted": f.get("timeFormatted", ""),
                "meal_type": f.get("mealType", "—"),
                "is_recognized": f.get("is_recognized", True),
                "has_explicit_quantity": f.get("has_explicit_quantity", True),
                "requires_clarification": f.get("requires_clarification", False),
                "clarification_reason": f.get("clarification_reason"),
            })

        # 2. Activities
        lower = norm.lower()
        has_workout = any(bool(re.search(pat, lower)) for pat in WORKOUT_PATTERNS)
        if has_workout:
            acts = AgentNLP.extract_activity_entities(text)
            for a in acts:
                if a.get("activity") and a["activity"] != "Workout":
                    actions.append({
                        "type": "CREATE_ACTIVITY_LOG",
                        "activity_name": a["activity"],
                        "duration_minutes": a.get("durationMinutes", 30.0),
                        "reps": a.get("reps"),
                        "sets": a.get("sets"),
                        "logged_at": a.get("logged_at"),
                        "time_formatted": a.get("timeFormatted"),
                        "met_value": a.get("metValue"),
                        "requires_clarification": a.get("requiresClarification", False),
                    })
                elif not foods:
                    actions.append({
                        "type": "CREATE_ACTIVITY_LOG",
                        "activity_name": a.get("activity", "Workout"),
                        "duration_minutes": a.get("durationMinutes", 30.0),
                        "reps": a.get("reps"),
                        "sets": a.get("sets"),
                        "logged_at": a.get("logged_at"),
                        "time_formatted": a.get("timeFormatted"),
                        "met_value": a.get("metValue", 5.0),
                        "requires_clarification": a.get("requiresClarification", False),
                    })

        # 3. Hydration
        hyd_ents = AgentNLP.extract_hydration_entities(text)
        for h_ent in hyd_ents:
            actions.append({
                "type": "CREATE_HYDRATION_LOG",
                "beverage_name": h_ent.get("beverage_name", "Water"),
                "amount_ml": h_ent.get("amount_ml", 250.0),
                "unit": "ml",
                "logged_at": h_ent.get("logged_at"),
                "has_explicit_time": h_ent.get("has_explicit_time", False),
                "time_formatted": h_ent.get("time_formatted", ""),
            })

        return actions
