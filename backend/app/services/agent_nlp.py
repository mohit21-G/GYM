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
    "one": 1.0, "a": 1.0, "an": 1.0, "two": 2.0, "three": 3.0, "four": 4.0,
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
    "spoon": "tbsp", "spoons": "tbsp", "chamchi": "tbsp", "chammach": "tbsp",
    "tbsp": "tbsp", "tsp": "tsp", "ml": "ml", "liter": "l", "litre": "l",
    "l": "l", "ltr": "l", "gram": "g", "grams": "g", "g": "g", "kg": "kg",
    "bottle": "bottle", "bottles": "bottle", "botle": "bottle",
    "serving": "serving", "servings": "serving",
    # Gujarati script units
    "વાટકી": "bowl", "કટોરી": "bowl", "ગ્લાસ": "glass", "કપ": "cup", "પ્લેટ": "plate", "ડીશ": "plate", "નંગ": "piece", "ટુકડો": "piece",
    # Hindi / Devanagari script units
    "कटोरी": "bowl", "कटोरा": "bowl", "ग्लास": "glass", "कप": "cup", "प्लेट": "plate", "टुकड़ा": "piece",
}

FOOD_NOUNS = [
    "roti", "rotli", "khapli", "apple", "banana", "kela", "milk", "doodh", "dudh",
    "dal", "daal", "rice", "chawal", "poha", "upma", "egg", "anda", "bread",
    "salad", "sabzi", "shaak", "shak", "thepla", "paratha", "chaas", "chhas", "chach", "dahi", "bhakri", "bhakhri",
    "chai", "chay", "tea", "coffee", "lassi", "paneer", "pneer", "pneeeer", "almonds", "whey", "protein powder",
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
    # Devanagari script food nouns
    "रोटी", "दाल", "चावल", "दूध", "छाछ", "केला", "सब्जी", "खीचड़ी", "पनीर", "समोसा", "इडली", "डोसा",
    "पोहा", "उपमा", "राजमा", "भिंडी", "बासुंदी", "सेव टमाटर", "पराठा", "अंडा", "अंडे", "कढ़ी", "कढ़ी",
    "खाखरा", "पाव भाजी", "पावभाजी", "नान", "छोले", "रायता", "सेब", "उत्पम", "उत्तपम", "मुठिया",
    "पात्रा", "श्रीखंड", "मोहनथाल", "फाफड़ा", "जलेबी", "दही", "पूरी",
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
    r"\bgym\b", r"\bworkout\b", r"\bexercise\b", r"\bcycling\b", r"\bpushups?\b",
    r"\byoga\b", r"\bbadminton\b", r"\bcricket\b", r"\bswimming\b", r"\bfootball\b",
    r"\bjump rope\b", r"\bhiit\b", r"\bpilates\b", r"\bzumba\b", r"\bdance\b",
    r"\bsquats\b", r"\bbench press\b", r"\bstretching\b", r"\bdhodhyo\b", r"\bkasrat\b", r"\bchalyo\b",
    r"દૌડ્યા", r"દૌડ્યો", r"દોડ્યો", r"ચાલ્યો", r"કસરત", r"વર્કઆઉટ", r"યોગા",
    r"दौड़ा", r"दौड़ी", "कसरत", "वर्कआउट", "योगा", "व्यायाम"
]

# Common food spelling corrections & slang aliases
INDIAN_FOOD_SYNONYMS: Dict[str, str] = {
    # Roti / Breads / Grains
    "khapli rti": "Khapli Wheat Rotli",
    "khapli roti": "Khapli Wheat Rotli",
    "khapli rotli": "Khapli Wheat Rotli",
    "khapli": "Khapli Wheat Rotli",
    "rotli": "Roti",
    "roti": "Roti",
    "chapati": "Roti",
    "chapatis": "Roti",
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
    "protein shake": "Whey Protein Shake",

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

    # Native Devanagari Script
    "रोटी": "Roti",
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
        """Replaces written number words (e.g. 'two', 'be', 'do', 'aadha') with numeric strings."""
        tokens = text.split()
        out = []
        for t in tokens:
            cleaned = re.sub(r"[^\w\.]", "", t.lower())
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
            "is it healthy", "is roti healthy", "is healthy", "should i eat", "what should i eat",
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

        if is_hypothetical or is_negative or is_advisory or is_question:
            return "GENERAL_CHAT"

        # 3. Query / Summary intent
        if any(w in lower for w in [
            "what did i eat", "show my food", "today's calories", "todays calories", "remaining",
            "how many calories did i eat", "how many calories today", "how many calories left", "how many calories do i have",
            "how much protein did i eat", "protein did i eat", "how much protein today", "protein today",
            "ketli calories", "ketlu khadhu", "aaj nu summary", "forgot what i ate",
            "aaj ka summary", "show logs", "show summary", "kya khaya", "batao",
            "my lunch calories", "remaining calories", "baki calories", "ketli calories thai", "calories thai",
            "daily food summary",
            "શું ખાધું", "કેટલી કેલરી", "આજનું સમરી", "સમરી", "क्या खाया", "कितनी कैलोरी", "आज का सारांश"
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
    def extract_activity_entity(text: str) -> Dict[str, Any]:
        """Extracts exercise activity name and duration."""
        norm = AgentNLP.normalize_text(text)
        lower = norm.lower()
        mins = 30
        m = re.search(r"\b(\d+)\s*(?:minute|minutes|min|mins|મિનિટ|मिनट)\b", lower)
        if m:
            mins = int(m.group(1))
        else:
            m2 = re.search(r"\b(\d+)\b", lower)
            if m2:
                mins = int(m2.group(1))
                
        activity = "Walking"
        if "run" in lower or "running" in lower or "ran" in lower or "દોડ" in lower or "दौड़" in lower:
            activity = "Running"
        elif "cycling" in lower or "cycle" in lower:
            activity = "Cycling"
        elif "gym" in lower or "workout" in lower or "વર્કઆઉટ" in lower or "वर्कआउट" in lower:
            activity = "Gym Workout"
        elif "yoga" in lower or "યોગા" in lower or "योगा" in lower:
            activity = "Yoga"
        elif "swim" in lower:
            activity = "Swimming"
        elif "badminton" in lower:
            activity = "Badminton"
        elif "cricket" in lower:
            activity = "Cricket"
        elif "pushup" in lower:
            activity = "Pushups"

        return {"activity": activity, "durationMinutes": mins, "intensity": "MEDIUM"}

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
            qty = 1.0
            num_match = re.search(r"\b(\d+(?:\.\d+)?)\b", clause)
            if num_match:
                try:
                    qty = float(num_match.group(1))
                except Exception:
                    qty = 1.0
            elif any(w in clause for w in ["thodu", "thoda", "thodi", "thodak", "zara", "thora", "થોડું", "થોડી", "थोड़ा", "थोड़ी"]):
                qty = 0.5

            # Extract unit safely with word boundaries for short keys
            unit = "serving"
            for u_raw, u_norm in UNIT_MAP.items():
                if len(u_raw) <= 2:
                    if re.search(rf"\b{re.escape(u_raw)}\b", clause):
                        unit = u_norm
                        break
                else:
                    if u_raw in clause:
                        unit = u_norm
                        break

            # Clean food phrase by stripping numbers, units, verbs, and filler words
            clean = clause
            clean = re.sub(r"^\d+(\.\d+)?", "", clean)
            clean = re.sub(r"\b\d+(\.\d+)?\b", "", clean)
            for u_raw in sorted(UNIT_MAP.keys(), key=len, reverse=True):
                if len(u_raw) <= 2:
                    clean = re.sub(rf"\b{re.escape(u_raw)}\b", " ", clean)
                else:
                    clean = clean.replace(u_raw, " ")

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
                # 1. Exact lookup
                if clean in INDIAN_FOOD_SYNONYMS:
                    canonical = INDIAN_FOOD_SYNONYMS[clean]

                # 2. Check multi-word phrase keys first (longest first)
                if not canonical:
                    for food_key in sorted(INDIAN_FOOD_SYNONYMS.keys(), key=len, reverse=True):
                        if " " in food_key or any(ord(c) > 127 for c in food_key):
                            if len(food_key) >= 3 and (food_key in clean or re.search(rf"\b{re.escape(food_key)}\b", clean, flags=re.I)):
                                canonical = INDIAN_FOOD_SYNONYMS[food_key]
                                break

                # 3. Check single tokens
                if not canonical:
                    tokens = clean.split()
                    for t in tokens:
                        if t in INDIAN_FOOD_SYNONYMS:
                            canonical = INDIAN_FOOD_SYNONYMS[t]
                            break

                # 4. Fallback substring
                if not canonical:
                    for food_key in sorted(INDIAN_FOOD_SYNONYMS.keys(), key=len, reverse=True):
                        if len(food_key) >= 3 and food_key in clean:
                            canonical = INDIAN_FOOD_SYNONYMS[food_key]
                            break

                if not canonical:
                    canonical = clean.title()

                if unit == "serving" and any(w in canonical.lower() for w in ["roti", "rotli", "bhakri", "banana", "egg", "thepla", "apple"]):
                    unit = "piece"

                results.append({
                    "food": canonical,
                    "quantity": qty,
                    "unit": unit,
                    "mealType": meal_type,
                })

        return results
