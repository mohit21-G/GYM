import re
import unicodedata
from typing import Dict, Any, List, Optional, Tuple

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
    r"\bgym\b", r"\bworkout\b", r"\bexercise\b", r"\bcycling\b", r"\bpush-?ups?\b", r"\bpull-?ups?\b",
    r"\byoga\b", r"\bbadminton\b", r"\bcricket\b", r"\bswimming\b", r"\bfootball\b",
    r"\bjump rope\b", r"\bhiit\b", r"\bpilates\b", r"\bzumba\b", r"\bdance\b",
    r"\bsquats?\b", r"\blunges?\b", r"\bcrunches?\b", r"\bplanks?\b", r"\bburpees?\b",
    r"\bbench press\b", r"\bdeadlifts?\b", r"\bstretching\b", r"\bdhodhyo\b", r"\bkasrat\b", r"\bchalyo\b",
    r"દૌડ્યા", r"દૌડ્યો", r"દોડ્યો", r"ચાલ્યો", r"કસરત", r"વર્કઆઉટ", r"યોગા", r"સ્ક્વોટ્સ?", r"પુશઅપ્સ?",
    r"दौड़ा", r"दौड़ी", "कसरत", "वर्कआउट", "योगा", "व्यायाम", r"स्क्वैट्स?", r"पुशअप्स?"
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
    "chapati": "Chapati",
    "chapatis": "Chapati",
    "phulka": "Phulka",
    "phulke": "Phulka",
    "phulkas": "Phulka",
    "theplas": "Methi Thepla",
    "theple": "Methi Thepla",
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
    "black coffee": "Black Coffee",
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
    "ખીચડી": "Moong Dal Khichdi",
    "દૂધ": "Cow Milk (Toned)",
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
            r"\brti\b": "roti",
            r"\bpice\b": "piece",
            r"\bpices\b": "pieces",
            r"\bplet\b": "plate",
            r"\bbwl\b": "bowl",
            r"\bgls\b": "glass",
            r"\bbotle\b": "bottle",
            r"\bwid\b": "with",
            r"\bchaye\b": "chai",
            r"\bpneer\b": "paneer",
            r"\bpneeeer\b": "paneer",
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
        }
        for pat, repl in typos.items():
            norm = re.sub(pat, repl, norm, flags=re.IGNORECASE)

        return norm

    @staticmethod
    def parse_number_tokens(text: str) -> str:
        """Replaces written number words (e.g. 'two', 'be', 'ek', 'aadha') with numeric strings."""
        tokens = text.split()
        out = []
        for i, t in enumerate(tokens):
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
        return " ".join(out)

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
        has_explicit_food = any(w in lower for w in FOOD_NOUNS)
        has_eating_verb = any(w in lower for w in EATING_VERBS)
        has_drinking_verb = any(w in lower for w in DRINKING_VERBS)
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
    def extract_hydration_entity(text: str) -> Dict[str, Any]:
        """Extracts water quantity in ml."""
        norm = AgentNLP.normalize_text(text)
        lower = norm.lower()
        qty = 1.0
        m = re.search(r"\b(\d+(?:\.\d+)?)\b", lower)
        if m:
            qty = float(m.group(1))
        
        amount = 250.0
        if "botle" in lower or "bottle" in lower:
            amount = 750.0 * qty
        elif "glass" in lower or "glaas" in lower or "ગ્લાસ" in lower or "ग्लास" in lower:
            amount = 250.0 * qty
        elif "cup" in lower or "kapp" in lower or "કપ" in lower or "कप" in lower:
            amount = 200.0 * qty
        elif "liter" in lower or "litre" in lower or re.search(r"\b\d+\s*l\b", lower):
            amount = 1000.0 * qty
        elif "ml" in lower:
            amount = qty
        else:
            amount = 250.0 * qty
            
        return {"waterAmount": amount, "amountMl": amount, "unit": "ml"}

    @staticmethod
    def extract_activity_entities(text: str) -> List[Dict[str, Any]]:
        """
        Extracts all exercise activities, durations, repetitions, and sets.
        Supports single and multiple exercises across English, Hindi, Gujarati, Hinglish, Gujlish.
        """
        norm = AgentNLP.normalize_text(text)
        lower = norm.lower()
        
        # Split into potential exercise clauses
        clauses = re.split(r"[,;\n\+]|\band\b|\bane\b|\baur\b|\bતથા\b|\bઅને\b", lower)
        clauses = [c.strip() for c in clauses if c.strip()]
        if not clauses:
            clauses = [lower]

        exercise_map = [
            (r"\bsquats?\b|સ્ક્વોટ્સ?|સ્કવોટ્સ?|स्क्वैट्स?", "Squats", 5.0, True),
            (r"\bpush-?ups?\b|પુશઅપ્સ?|पुशअप्स?|\bદંડ\b", "Push-ups", 4.5, True),
            (r"\bpull-?ups?\b|પુલઅપ્સ?|पुलअप्स?|ચિનઅપ", "Pull-ups", 5.0, True),
            (r"\blunges?\b|લંજીસ?|લંજ", "Lunges", 4.5, True),
            (r"\bcrunches?\b|sit-?ups?|ક્રંચ|क्रंचेस", "Crunches", 3.8, True),
            (r"\bplanks?\b|પ્લેન્ક|પ્લેંક|प्लैंक", "Plank", 3.5, False),
            (r"\bburpees?\b|બર્પી|बर्पी", "Burpees", 8.0, True),
            (r"\bjump(?:ing)?\s*jacks?\b|જમ્પિંગ\s*જેક", "Jumping Jacks", 8.0, True),
            (r"\bjump\s*rope\b|skipping|દોરડા\s*કૂદવા|रस्सी\s*कूद", "Jump Rope", 10.0, False),
            (r"\bbench\s*press\b|બેન્ચ\s*પ્રેસ|बेंच\s*प्रेस", "Bench Press", 5.5, True),
            (r"\bdeadlifts?\b|ડેડલિફ્ટ|डेडलिफ्ट", "Deadlift", 6.0, True),
            (r"\brun(?:ning)?\b|\bran\b|દોડ|दौड़", "Running", 8.5, False),
            (r"\bwalk(?:ing)?\b|\bwalked\b|ચાલ|ટહેલ|टहल", "Walking", 3.5, False),
            (r"\bcycl(?:ing|e)\b|સાયકલ|साइकिल", "Cycling", 6.0, False),
            (r"\bswim(?:ming)?\b|તરવું|तैरना", "Swimming", 7.0, False),
            (r"\byoga\b|યોગ|योग", "Yoga", 3.0, False),
            (r"\bbadminton\b", "Badminton", 5.5, False),
            (r"\bcricket\b", "Cricket", 5.0, False),
            (r"\bgym\b|\bworkout\b|\bexercise\b|\bkasrat\b|\bvyayam\b|કસરત|વર્કઆઉટ|વ્યાયામ|व्यायाम|कसरत", "Workout", 5.0, False),
        ]

        extracted = []
        seen_names = set()

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

            if not matched_name:
                continue

            if matched_name in seen_names:
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
                # E.g. "20 squats" or "squats 20" or "15 pushups"
                m_num = re.search(r"(\d+)\s*(?:" + matched_pat + r")|(?:" + matched_pat + r")\s*(\d+)", clause)
                if m_num:
                    num_str = m_num.group(1) or m_num.group(2)
                    if num_str:
                        reps_val = int(num_str)

            # 3. Extract duration in minutes if any
            duration_val = None
            m_min = re.search(r"(\d+(?:\.\d+)?)\s*(?:minutes?|mins?|min|મિનિટ|मिनट)", clause)
            if m_min:
                duration_val = float(m_min.group(1))
            else:
                m_hr = re.search(r"(\d+(?:\.\d+)?)\s*(?:hours?|hrs?|hr|કલાક|घंटे|घंटा)", clause)
                if m_hr:
                    duration_val = float(m_hr.group(1)) * 60.0

            # If duration is missing but reps is present: estimate duration based on reps & sets
            if duration_val is None and reps_val is not None:
                total_reps = reps_val * sets_val
                duration_val = max(1.0, round(total_reps * 0.08, 1))

            # If reps is missing and duration is missing:
            # Check if there is a loose number in the clause (not sets or weight)
            if duration_val is None and reps_val is None:
                m_loose = re.search(r"\b(\d+)\b", clause)
                if m_loose:
                    val = int(m_loose.group(1))
                    if is_rep_based and val <= 100:
                        reps_val = val
                        duration_val = max(1.0, round(reps_val * 0.08, 1))
                    else:
                        duration_val = float(val)

            requires_clarification = (duration_val is None and reps_val is None)
            if duration_val is None:
                duration_val = 30.0  # default tracker baseline if forced

            seen_names.add(matched_name)
            extracted.append({
                "activity": matched_name,
                "reps": reps_val,
                "sets": sets_val if reps_val else None,
                "durationMinutes": duration_val,
                "intensity": "MEDIUM",
                "metValue": matched_met,
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
                    extracted.append({
                        "activity": name,
                        "reps": reps,
                        "sets": 1 if reps else None,
                        "durationMinutes": mins,
                        "intensity": "MEDIUM",
                        "metValue": met,
                        "requiresClarification": (m_min is None and m_rep is None),
                    })
                    break

        if not extracted:
            extracted.append({
                "activity": "Workout",
                "reps": None,
                "sets": None,
                "durationMinutes": 30.0,
                "intensity": "MEDIUM",
                "metValue": 5.0,
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
        """Fallback entity extractor for food messages with typos, quantities, and units."""
        norm = AgentNLP.normalize_text(text)
        lower = norm.lower()

        # Split message into clauses using separators
        clauses = re.split(r",| and | ane | aur | અને | અને\s+| અને| aur\s+| और | sath me | sathe | સાથે | સાથે\s+| साथ में | with |\+", lower)
        results = []

        # Guess meal type from sentence
        meal_type = "LUNCH"
        if any(w in lower for w in [
            "morning", "breakfast", "savar", "savare", "saware", "sawar", "savaar", 
            "subah", "subha", "nasto", "nashta", "સવાર", "સવારે", "નાસ્તો", "सुबह", "नाश्ता"
        ]):
            meal_type = "BREAKFAST"
        elif any(w in lower for w in [
            "dinner", "sanj", "sanje", "saanj", "saanje", "sanju", "shaam", "sham", 
            "raat", "raate", "raatri", "valoo", "valo", "vaalu", "વાળુ", "વાળું", "સાંજ", "સાંજે", "રાત", "રાત્રે", "रात", "शाम"
        ]):
            meal_type = "DINNER"
        elif any(w in lower for w in ["snack", "snacks", "chaai", "tea", "ચા"]):
            meal_type = "SNACK"

        for clause in clauses:
            clause = clause.strip()
            if not clause:
                continue

            # Skip pure water, activity, or sleep clauses
            if any(w in clause for w in ["pani", "water", "walk", "run", "gym", "sleep", "slept", "oongh", "neend", "suto", "suvo", "પાણી", "પાની", "ઊંઘ", "નીંદ", "સોયા", "सोया"]):
                continue

            # Strip SQL injection attempts and benchmark noise
            clause = re.sub(r";\s*DROP TABLE.*|;\s*--.*", "", clause, flags=re.IGNORECASE)
            clause = re.sub(r"\bpleez\s+trac\w*\b|\bpleez\b|\btrac\b", "", clause, flags=re.IGNORECASE)
            clause = re.sub(r'\{"user_id".*\}', '', clause)

            # Extract quantity
            has_explicit_qty = False
            qty = 1.0
            num_match = re.search(r"\b(\d+(?:\.\d+)?)\b", clause)
            if num_match:
                try:
                    qty = float(num_match.group(1))
                    has_explicit_qty = True
                except Exception:
                    qty = 1.0
            else:
                for nw_word, nw_val in NUMBER_WORDS.items():
                    if any(ord(c) > 127 for c in nw_word):
                        if re.search(rf"(?<![\u0A80-\u0AFF\u0900-\u097F]){re.escape(nw_word)}(?![\u0A80-\u0AFF\u0900-\u097F])", clause):
                            qty = nw_val
                            has_explicit_qty = True
                            break
                    else:
                        if re.search(rf"\b{re.escape(nw_word)}\b", clause, flags=re.I):
                            qty = nw_val
                            has_explicit_qty = True
                            break
                if not has_explicit_qty and any(w in clause for w in ["thodu", "thoda", "thodi", "thodak", "zara", "thora", "થોડું", "થોડી", "थोड़ा", "थोड़ी"]):
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
                canonical = None
                is_recognized = False

                # 1. Exact lookup
                if clean in INDIAN_FOOD_SYNONYMS:
                    canonical = INDIAN_FOOD_SYNONYMS[clean]
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

                # 3. Check single tokens
                if not canonical:
                    tokens = clean.split()
                    for t in tokens:
                        if t in INDIAN_FOOD_SYNONYMS:
                            canonical = INDIAN_FOOD_SYNONYMS[t]
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

                confidence = 0.95 if is_recognized else 0.3
                requires_clarification = (not is_recognized) or (not has_explicit_qty)
                clarification_reason = "UNKNOWN_FOOD" if not is_recognized else ("AMBIGUOUS_QUANTITY" if not has_explicit_qty else None)

                # Context-aware default unit when unit was not specified
                if unit == "serving":
                    c_lower = canonical.lower()
                    if any(w in c_lower for w in ["powder", "whey"]):
                        unit = "scoop"
                    elif any(w in c_lower for w in ["shake", "smoothie"]):
                        unit = "glass"
                    elif any(w in c_lower for w in ["roti", "rotli", "bhakri", "thepla", "egg", "banana", "apple", "chapati", "phulka", "naan", "paratha", "poori"]):
                        unit = "piece"
                    elif any(w in c_lower for w in ["dal", "daal", "rice", "chawal", "khichdi", "sabzi", "shaak", "curd", "dahi", "salad"]):
                        unit = "bowl"

                results.append({
                    "food": canonical,
                    "food_name": canonical,
                    "quantity": qty,
                    "unit": unit,
                    "mealType": meal_type,
                    "confidence": confidence,
                    "is_recognized": is_recognized,
                    "has_explicit_quantity": has_explicit_qty,
                    "requires_clarification": requires_clarification,
                    "clarification_reason": clarification_reason,
                })

        return results
