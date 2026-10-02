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
    "vaatki": "bowl", "bowl": "bowl", "bowls": "bowl", "katora": "bowl", "bwl": "bowl", "bwll": "bowl",
    "ktori": "bowl", "vtk": "bowl",
    "cup": "cup", "cups": "cup", "kapp": "cup", "kap": "cup",
    "glass": "glass", "glasses": "glass", "glaas": "glass", "gllass": "glass", "gls": "glass", "pyala": "glass",
    "plate": "plate", "plates": "plate", "dish": "plate", "thaali": "plate", "plet": "plate", "plt": "plate",
    "piece": "piece", "pieces": "piece", "pcs": "piece", "pc": "piece", "pice": "piece", "pices": "piece",
    "nag": "piece", "tukda": "piece",
    "slice": "slice", "slices": "slice", "scoop": "scoop", "scoops": "scoop", "scp": "scoop", "skup": "scoop",
    "spoon": "tbsp", "spoons": "tbsp", "spoonful": "tbsp",
    "chamach": "tbsp", "chamacha": "tbsp", "chamchi": "tbsp", "chammach": "tbsp", "chamcho": "tbsp",
    "tablespoon": "tbsp", "tablespoons": "tbsp", "teaspoon": "tsp", "teaspoons": "tsp",
    "tbsp": "tbsp", "tsp": "tsp", "ml": "ml", "mll": "ml", "liter": "l", "litre": "l",
    "l": "l", "ltr": "l", "gram": "g", "grams": "g", "gm": "g", "gms": "g", "g": "g", "kg": "kg",
    "bottle": "bottle", "bottles": "bottle", "botle": "bottle", "btl": "bottle",
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
    "salad", "sabzi", "shaak", "shak", "sabji", "subji", "thepla", "theplas", "paratha", "chaas", "chhas", "chach", "dahi", "bhakri", "bhakhri",
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
    "khakhra", "rajma", "bhindi", "pav bhaji", "pavbhaji", "vedmi", "mohanthal", "papad",
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
    "khadha", "khadhi", "khadhu", "khadho", "khado", "khaye", "khaya", "khayi", "khalo",
    "lidhi", "lidhu", "lidho", "lido", "leedhi", "leedhu", "leedho", "liya", "li",
    "karyu", "karya", "kari", "kri",
    "ખાધી", "ખાધું", "ખાધા", "લીધું", "લીધી", "કર્યું", "કર્યા",
    "खाया", "खाई", "खाए", "लिया", "ली", "किया"
]

DRINKING_VERBS = [
    "pidhi", "pidhu", "pidha", "pidho", "pido", "pitu", "pithi", "piya", "piyi", "peeli", "peena", "drink", "drank", "drunk", "peeya",
    "પીધું", "પીધી", "पिया", "पी"
]

WORKOUT_PATTERNS = [
    r"\bwalk\b", r"\bwalked\b", r"\bwalking\b", r"\bwlak\b", r"\bwlaked\b", r"\bwlkng\b", r"\bwalkng\b", r"\bwaking\b",
    r"\brun\b", r"\brunning\b", r"\bran\b", r"\bjog\b", r"\bjogged\b", r"\bjogging\b",
    r"\bgym\b", r"(?<!pre[-\s])\bworkout\b", r"\bexercise\b", r"\bexersise\b", r"\bexcersise\b",
    r"\bcycl(?:e|ed|ing)?\b", r"\bcycld\b", r"\bbike\b", r"\bpush-?ups?\b", r"\bpusups?\b", r"\bpushupz\b", r"\bpull-?ups?\b",
    r"\bback\b(?!\s+(?:tea|coffee))", r"\bbiceps?\b", r"\btriceps?\b", r"\bchest\b", r"\blegs?\b", r"\bshoulders?\b", r"\babs\b",
    r"\byoga\b", r"\byga\b", r"\bbadminton\b", r"\bcricket\b", r"\bswim(?:ming)?\b", r"\bswam\b", r"\bswm\b", r"\bfootball\b",
    r"\bjump rope\b", r"\bskipping\b", r"\bskipped\b", r"\bhiit\b", r"\bpilates\b", r"\bzumba\b", r"\bdance\b",
    r"\bsquats?\b", r"\bsqats?\b", r"\bskwats?\b", r"\blunges?\b", r"\bcrunches?\b", r"\bplanks?\b", r"\bburpees?\b",
    r"\bbench press\b", r"\bbnk\s*prss\b", r"\bbnch\s*prss\b", r"\bbnch\b", r"\bdeadlifts?\b", r"\belliptical\b", r"\btreadmill\b",
    r"\bstretching\b", r"\bstrength\s*training\b", r"\bdhodhyo\b", r"\bkasrat\b", r"\bchalyo\b",
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
    "khaply": "Khapli Wheat Rotli",
    "khaply rwtli": "Khapli Wheat Rotli",
    "rotli": "Roti",
    "rotlis": "Roti",
    "roti": "Roti",
    "rotis": "Roti",
    "rti": "Roti",
    "rotliyo": "Roti",
    "rotlee": "Roti",       # phonetic variant: rotlee sounds like rotli
    "rotlii": "Roti",       # double-i phonetic variant
    "rwtli": "Roti",
    "chapati": "Chapati",
    "chapatis": "Chapati",
    "phulka": "Phulka",
    "phulke": "Phulka",
    "phulkas": "Phulka",
    "theplas": "Methi Thepla",
    "theple": "Methi Thepla",
    "mthii thepla": "Methi Thepla",
    "rotlo": "Rotlo",
    "rotla": "Rotlo",
    "rotlu": "Rotlo",
    "bajra rotlo": "Rotlo",
    "bajri rotla": "Rotlo",
    "bajra rotla": "Rotlo",
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
    "bakhrii": "Bhakri",
    "whole wheat bhakri": "Bhakri",
    "thepla": "Methi Thepla",
    "methi thepla": "Methi Thepla",
    "paratha": "Plain Paratha",
    "prtha": "Plain Paratha",
    "parotha": "Plain Paratha",
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
    "tea with milk": "Tea With Milk",
    "tea milk": "Tea With Milk",
    "chai with milk": "Tea With Milk",
    "chai milk": "Tea With Milk",
    "masala chai": "Tea With Milk",
    "masala tea": "Tea With Milk",
    "coffee": "Coffee With Milk",
    "cofee": "Coffee With Milk",
    "coffee with milk": "Coffee With Milk",
    "coffee milk": "Coffee With Milk",
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
    "chawl": "Cooked White Rice",
    "bhaat": "Cooked White Rice",
    "bhat": "Cooked White Rice",
    "rice": "Cooked White Rice",
    "rce": "Cooked White Rice",
    "brwn rce": "Cooked White Rice",
    "brown rice": "Cooked White Rice",
    "jeera rice": "Cooked White Rice",
    "steamed rice": "Cooked White Rice",
    "khichdi": "Moong Dal Khichdi",
    "khichdo": "Moong Dal Khichdi",
    "moong dal khichdi": "Moong Dal Khichdi",
    "poha": "Poha",
    "upma": "Upma",
    "idli": "Idli",
    "idly": "Idli",
    "idlii": "Idli",
    "dosa": "Plain Dosa",
    "plain dosa": "Plain Dosa",
    "masala dosa": "Masala Dosa",

    # Dairy
    "doodh": "Cow Milk (Toned)",
    "dhooodh": "Cow Milk (Toned)",
    "dudh": "Cow Milk (Toned)",
    "milk": "Cow Milk (Toned)",
    "cow milk": "Cow Milk (Toned)",
    "chaas": "Spiced Buttermilk (Chaas)",
    "chhas": "Spiced Buttermilk (Chaas)",
    "chach": "Spiced Buttermilk (Chaas)",
    "buttermilk": "Spiced Buttermilk (Chaas)",
    "dahi": "Curd (Dahi)",
    "curd": "Curd (Dahi)",
    "curd rice": "Curd (Dahi)",
    "dahi bhat": "Curd (Dahi)",
    "yogurt": "Curd (Dahi)",
    "paneer": "Paneer",
    "pneer": "Paneer",
    "pneeeer": "Paneer",
    "paneeeer": "Paneer",
    "paneer bhurji": "Paneer Bhurji",
    "paneeeer bhurjii": "Paneer Bhurji",
    "paneer makhani": "Paneer",
    "paneer tikka": "Paneer Tikka",
    "ghee": "Desi Ghee",
    "butter": "Butter",
    "cheese": "Cheese",
    "lassi": "Sweet Lassi",

    # Dals & Pulses
    "dal": "Toor Dal",
    "daal": "Toor Dal",
    "daaal": "Toor Dal",
    "dahl": "Toor Dal",
    "dl": "Toor Dal",
    "toor dal": "Toor Dal",
    "tuver dal": "Toor Dal",
    "yellow dal": "Toor Dal",
    "yellow toor dal": "Toor Dal",
    "moong dal": "Yellow Moong Dal",
    "mug dal": "Yellow Moong Dal",
    "chana dal": "Chana Dal",
    "kadhi": "Gujarati Kadhi",
    "kdhi": "Gujarati Kadhi",
    "sambhar": "Sambar",
    "sambar": "Sambar",
    "smbar": "Sambar",
    "chole": "Chole Chana Masala",
    "chole chana": "Chole Chana Masala",
    "chole masala": "Chole Chana Masala",
    "chana masala": "Chole Chana Masala",
    "chna masla": "Chole Chana Masala",
    "chna": "Chole Chana Masala",
    "chnaa": "Chole Chana Masala",
    "rajma": "Rajma",
    "rajmah": "Rajma",
    "rajmah chawl": "Rajma",
    "rajma curry": "Rajma",
    "kidney bean": "Rajma",
    "kidney beans": "Rajma",
    "chana": "Boiled Chickpeas",
    "sprouts": "Mixed Sprouts",
    "sprouts salad": "Mixed Sprouts",
    "papad": "Papad",
    "nartyal chtny": "Coconut Chutney",
    "coconut chutney": "Coconut Chutney",

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
    "sabji": "Mixed Vegetable Sabzi",
    "subji": "Mixed Vegetable Sabzi",
    "shaak": "Mixed Vegetable Sabzi",
    "shak": "Mixed Vegetable Sabzi",
    "mug nu shak": "Mixed Vegetable Sabzi",
    "sprouts salad": "Mixed Sprouts",
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
    "egss": "Boiled Egg",
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
    "chkn": "Chicken Breast",
    "bresst": "Chicken Breast",
    "chkn bresst": "Chicken Breast",
    "chikn": "Chicken Breast",
    "chicken breast": "Chicken Breast",
    "chicken tikka": "Chicken Tikka",
    "fish": "Grilled Fish",
    "whey": "Whey Protein Powder",
    "whye": "Whey Protein Powder",
    "whye prtein": "Whey Protein Powder",
    "whey protein": "Whey Protein Powder",
    "whey protein powder": "Whey Protein Powder",
    "protein powder": "Whey Protein Powder",
    "protin powder": "Whey Protein Powder",
    "protien powder": "Whey Protein Powder",
    "protein shake": "Protein Shake",
    "protein shakes": "Protein Shake",
    "protin shake": "Protein Shake",
    "protien shake": "Protein Shake",
    "protn": "Protein Shake",
    "prtein": "Protein Shake",
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
    "chole bhature": "Chole Chana Masala",
    "dahi bhat": "Curd (Dahi)",
    "water": "Water",
    "paani": "Water",
    "pani": "Water",
    "pni": "Water",
    "panu": "Water",
    "apple": "Apple",
    "aplle": "Apple",
    "toast": "Toast",
    "tosst": "Toast",

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

        # Number words normalization (e.g., 'ek rotli', 'be apple', 'tran anda')
        num_words = {
            r"\bek\b": "1",
            r"(?<!\bto\s)(?<!\bwill\s)(?<!\bcan\s)(?<!\bshould\s)(?<!\bmust\s)(?<!\bcould\s)(?<!\bwould\s)(?<!\bmay\s)(?<!\bmight\s)(?<!\blet\s)\bbe\b": "2",
            r"\btran\b": "3",
            r"\btraan\b": "3",
            r"\bteen\b": "3",
            r"\btin\b": "3",
            r"\bchaar\b": "4",
            r"\bchar\b": "4",
            r"\bpaanch\b": "5",
            r"\bpanch\b": "5",
            r"\bchheh\b": "6",
            r"\bchhe\b": "6",
            r"\bsaat\b": "7",
            r"\bsat\b": "7",
            r"\baath\b": "8",
            r"\bnau\b": "9",
            r"\bnav\b": "9",
            r"\bdus\b": "10",
            r"\bdas\b": "10",
        }
        for pat, repl in num_words.items():
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
            r"\bexercize\b": "exercise",
            r"\bexercize\b": "exercise",
            r"\bexersize\b": "exercise",
            r"\bexcersize\b": "exercise",
            # Food & supplements
            r"\bprotien\b": "protein",
            r"\bprotin\b": "protein",
            r"\bprotn\b": "protein",
            r"\bprtein\b": "protein",
            r"\bwhye\b": "whey",
            r"\bpowdr\b": "powder",
            r"\bpawder\b": "powder",
            r"\bkhapali\b": "khapli",
            r"\bkhaply\b": "khapli",
            r"\brti\b": "roti",
            r"\brwtli\b": "roti",
            r"\brotlii\b": "roti",
            r"\bpice\b": "piece",
            r"\bpices\b": "pieces",
            r"\bplet\b": "plate",
            r"\bplt\b": "plate",
            r"\bbwl\b": "bowl",
            r"\bbwll\b": "bowl",
            r"\bktori\b": "katori",
            r"\bvtk\b": "vatki",
            r"\bgls\b": "glass",
            r"\bglaas\b": "glass",
            r"\bgllass\b": "glass",
            r"\bbotle\b": "bottle",
            r"\bbtl\b": "bottle",
            r"\bchaye\b": "chai",
            r"\bpneer\b": "paneer",
            r"\bpneeeer\b": "paneer",
            r"\bpaneeeer\b": "paneer",
            r"\bpanner\b": "paneer",
            r"\bpoh\b": "poha",
            r"\bmakni\b": "makhani",
            r"\beggz\b": "eggs",
            r"\begss\b": "eggs",
            r"\baplle\b": "apple",
            r"\btosst\b": "toast",
            r"\bsamose\b": "samosa",
            r"\bidlee\b": "idli",
            r"\bidlii\b": "idli",
            r"\bsambher\b": "sambar",
            r"\bsmbar\b": "sambar",
            r"\bparotha\b": "paratha",
            r"\bprtha\b": "paratha",
            r"\bdaal\b": "dal",
            r"\bdaaal\b": "dal",
            r"\bdahl\b": "dal",
            r"\bdl\b": "dal",
            r"\bkdhi\b": "kadhi",
            r"\bchna\b": "chana",
            r"\bchnaa\b": "chana",
            r"\bmasla\b": "masala",
            r"\bmthii\b": "methi",
            r"\bbakhrii\b": "bhakhri",
            r"\bnartyal\b": "nariyal",
            r"\bchtny\b": "chutney",
            r"\bdhooodh\b": "doodh",
            r"\bchkn\b": "chicken",
            r"\bbresst\b": "breast",
            r"\bbrwn\b": "brown",
            r"\brce\b": "rice",
            r"\bchawl\b": "chawal",
            r"\bbanaana\b": "banana",
            r"\bchiken\b": "chicken",
            r"\blitr\b": "litre",
            r"\blieter\b": "litre",
            r"\bskoop\b": "scoop",
            r"\bscop\b": "scoop",
            r"\bskup\b": "scoop",
            r"\bscp\b": "scoop",
            r"\bpanu\b": "pani",
            r"\bpni\b": "pani",
            r"\bpitu\b": "pidhu",
            r"\bpithi\b": "pidhi",
            r"\bsqats?\b": "squats",
            r"\bskwats?\b": "squats",
            r"\bpusups?\b": "pushups",
            r"\bpushupz\b": "pushups",
            r"\bbnk\s*prss\b": "bench press",
            r"\bbnch\s*prss\b": "bench press",
            r"\bbnch\b": "bench press",
            r"\bwlaked\b": "walked",
            r"\bwlkng\b": "walking",
            r"\byga\b": "yoga",
            r"\bcycld\b": "cycled",
            r"\bswm\b": "swim",
            r"\bminutss\b": "minutes",
            r"\bmnts\b": "minutes",
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
        lines = norm.splitlines()
        repaired_lines = []
        for line in lines:
            words = line.split(" ")
            corrected_words = []
            for w in words:
                w_clean = re.sub(r"^[^\w]+|[^\w]+$", "", w.lower())
                if len(w_clean) >= 4 and w_clean not in fuzzy_vocab and not w_clean.isdigit():
                    matches = difflib.get_close_matches(w_clean, fuzzy_vocab, n=1, cutoff=0.85)
                    if matches:
                        prefix = re.match(r"^[^\w]+", w)
                        suffix = re.search(r"[^\w]+$", w)
                        p_str = prefix.group(0) if prefix else ""
                        s_str = suffix.group(0) if suffix else ""
                        corrected_words.append(p_str + matches[0] + s_str)
                        continue
                corrected_words.append(w)
            repaired_lines.append(" ".join(corrected_words))
        return "\n".join(repaired_lines)

    @staticmethod
    def normalize_text(text: str) -> str:
        return AgentNLP.repair_missing_spaces_and_typos(text)

    @classmethod
    def detect_intent(cls, message: str) -> str:
        """Detect primary intent using hierarchical rules.
        
        Resolution order:
        1. Contextual continuation phrases -> CREATE_FOOD_LOG
        2. Explicit summary / query requests -> DAILY_SUMMARY, QUERY_FOOD_LOG, etc.
        3. Domain nouns (Food, Workout, Hydration, Sleep, Weight)
        4. Verbs
        5. Severe fuzzy keywords with numbers / units
        6. General chat fallback
        """
        if not message or not message.strip():
            return "GENERAL_CHAT"

        cleaned_text = cls.repair_missing_spaces_and_typos(message)
        lower = cleaned_text.lower().strip()

        # 0. LOGGING-PRIORITY GUARD (runs before any query/summary classification)
        # ---------------------------------------------------------------------
        # A multi-item logging message (often multi-line, e.g. a morning routine
        # with timestamps) can accidentally contain words like "water" plus a
        # weak query fragment, which previously misrouted the whole message to
        # QUERY_HYDRATION_LOG and dropped every logged item.
        #
        # If the message clearly contains logged DATA — several quantity+unit
        # tokens, or multiple timestamped entries — and it is NOT phrased as a
        # question, treat it as a creation/multi log, never a query.
        if "?" not in lower:
            # Count "<number> <unit/food>" style tokens (e.g. "400 ml", "3 roti",
            # "1 scoop", "1 glass", "1 cup", "1 litre").
            qty_unit_hits = len(re.findall(
                r"\d+(?:\.\d+)?\s*(?:ml|l|litre|liter|g|kg|glass|glasses|cup|cups|bowl|bowls|katori|vatki|"
                r"scoop|scoops|plate|plates|piece|pieces|roti|rotli|rotis|slice|slices|spoon|tbsp|tsp|"
                r"min|mins|minute|minutes)\b",
                lower,
            ))
            # Count clock timestamps like "6:45", "7:00 am", "10:00 am".
            time_hits = len(re.findall(r"\b\d{1,2}:\d{2}\b", lower))
            # Does it have an eating/drinking/activity signal?
            has_log_verb = (
                any(v in lower for v in EATING_VERBS)
                or any(v in lower for v in DRINKING_VERBS)
                or any(re.search(p, lower) for p in WORKOUT_PATTERNS)
                or bool(re.search(r"\b(ate|had|drank|did|logged|took|ran|walked|ran|workout|gym)\b", lower))
            )
            # Strong logging evidence: 2+ measured items, OR 2+ timestamps, OR a
            # measured item together with a log verb.
            if qty_unit_hits >= 2 or time_hits >= 2 or (qty_unit_hits >= 1 and has_log_verb):
                has_food = bool(cls.extract_food_entities_heuristically(message))
                has_act = any(re.search(p, lower) for p in WORKOUT_PATTERNS)
                has_water = bool(re.search(r"\b\d+(?:\.\d+)?\s*(?:ml|l|litre|liter|glass|glasses)\b", lower)) and \
                    ("water" in lower or "pani" in lower or "paani" in lower)
                signal_count = sum([bool(has_food), bool(has_act), bool(has_water)])
                if signal_count >= 2:
                    return "CREATE_MULTI_LOG"
                if has_act and not has_food:
                    return "CREATE_ACTIVITY_LOG"
                if has_water and not has_food:
                    return "CREATE_HYDRATION_LOG"
                if has_food:
                    return "CREATE_FOOD_LOG"

        # 1. Contextual continuation phrases
        is_contextual_continuation = any(w in lower for w in [
            "sathe", "lidhu", "lidhi", "khadhu", "khadha", "khadhi", "khau chhu", "jamyo", "jami", "jamya",
            "khatam", "patavyu", "pityu", "patais", "bija", "biji", "sathe sathe", "jode", "bapor na", "savare",
            "ek biju", "ek biji", "have", "nasta ma", "thodu", "thoda", "thodi", "vadhu", "sath ma",
            "saath me", "saath", "liye", "liya", "khaya", "khayi", "khaye", "piya", "aur", "ek aur", "dusra",
            "dusri", "bhi", "khatam kiya", "bhi khaya", "kuch aur", "saath sath", "or bhi",
            "with", "and also", "had", "ate", "also ate", "also had", "plus", "along with", "one more", "more",
            "finished", "done with", "took", "drank", "consumed", "some more",
            "સાથે", "લીધું", "લીધી", "ખાધું", "ખાધા", "ખાધી", "જમ્યો", "જમી", "જમ્યા", "બીજું", "બીજી", "બીજા", "સાથે સાથે", "જોડે", "ખતમ",
            "साथ", "साथ में", "लिया", "ली", "खाया", "खाई", "खाए", "पिया", "और", "एक और", "दूसरा", "दूसरी", "भी", "खत्म किया", "भी खाया"
        ])
        if lower in ["sathe", "saath me", "with", "and", "plus", "aur"]:
            return "GENERAL_CHAT"

        # 1. Food Suggestions intent
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
            # ── Future-day food suggestions (kale/kal/tomorrow + question word) ──
            "kale su khavu", "kale shu khavu", "kale su khau", "kale su jamvu",
            "kale mare su khavu", "kale mare su khau", "kal su khana", "kal kya khau",
            "kal kya khaunga", "tomorrow what to eat", "tomorrow what should i eat",
            "tomorrow su khavu joiye", "aavti kale su khavu",
            # ── Current-time / next-meal suggestions ──
            "have su khavu", "have su khau", "have kya khau", "abhi kya khau",
            "haju su khavu", "haju su khau",
            "sanje su khavu", "sanje su khau", "sanje mare su khavu",
            "ratre su khavu", "raat ma su khavu",
            "savare su khavu joiye", "nasta ma su le", "breakfast ma su khau",
            "શું ખાવા જોઈએ", "શું ખાવું", "શું ખાઉં", "ડિનરમાં શું બનાવવું", "લંચમાં શું ખાવું", "નાસ્તામાં શું લેવું", "સ્વસ્થ ખોરાક", "શું જમવું",
            "क्या खाना चाहिए", "क्या खाऊं", "क्या खाएं", "डिनर में क्या बनाऊं", "लंच में क्या खाऊं", "नाश्ते में क्या लें", "हेल्दी खाना"
        ])
        if is_food_suggestion:
            return "FOOD_SUGGESTION"

        # 2. Workout Suggestions intent
        is_workout_suggestion = any(w in lower for w in [
            "suggest exercise", "suggest workout", "suggest an exercise", "suggest a workout",
            "what exercise should i do", "what workout should i do", "exercise suggestions",
            "workout suggestions", "give me exercise", "give me workout", "recommend exercise",
            "recommend workout", "which exercise should i do", "exercise suggest karo",
            "workout suggest karo", "kai exercise karu", "kai kasrat karu", "kasrat suggest karo",
            "koi exercise batao", "koi workout batao", "aaj kaunsa workout", "aaje kai kasrat",
            "kai exercise karvi joiye", "kai kasrat karvi joiye", "suggest workout for",
            # ── Future-day / today workout suggestions ("mare kale su exercise karvi joiye?") ──
            "kale su exercise", "kale su exercise karvi", "kale su exercise karu",
            "kale kai exercise", "kale kai kasrat", "kale su workout",
            "kale mare su exercise", "kal kya exercise", "kal kaunsa workout",
            "tomorrow what exercise", "tomorrow what workout", "tomorrow which exercise",
            "mare kale su exercise karvi joiye", "aavti kale su exercise",
            "mare aaje su exercise", "mare aaje su exercise karvi", "aaje su exercise karvi",
            "aaje kai exercise karu", "have su exercise", "have kai exercise karu",
            "કઈ કસરત કરું", "કસરત સજેસ્ટ", "વર્કઆઉટ સજેસ્ટ", "કોઈ કસરત બતાવો",
            "कौन सी एक्सरसाइज करूं", "एक्सरसाइज सजेस्ट करो", "वर्कआउट सजेस्ट करो", "कोई एक्सरसाइज बताओ"
        ])
        if is_workout_suggestion:
            return "WORKOUT_SUGGESTION"

        # 3. Fitness & Workout Question / Recommendation Check -> FITNESS_ADVISORY (DO NOT LOG)
        has_q_word = bool(re.search(r"\b(?:what|how|which|why|give me|suggest|batao|aapo|kya|kaise|kaunse|shu|kem|kaya|kai)\b", lower)) or "?" in lower or any(ch in lower for ch in ["કયા", "શું", "કેમ", "કેવી રીતે", "ફાયદા", "ફાયદો", "क्या", "कैसे", "कौनसे", "फायदे"])
        is_fitness_advisory = any(w in lower for w in [
            "benefits of", "benefit of", "fayda", "fayde", "faida", "faide", "લાભ", "ફાયદા", "ફાયદો", "ફायदे", "लाभ",
            "workout plan", "routine plan", "exercise plan", "beginner workout", "beginner plan", "workout for beginner",
            "stamina", "endurance", "સ્ટેમિના", "સ્ટિમિના", "दम", "improve my stamina", "improve stamina", "increase stamina",
            "stamina kem", "stamina kaise", "badhaye", "vadharvu", "target the legs", "target legs", "leg exercise", "leg workout",
            "exercises for", "exercise for", "exercises target", "which exercises", "which exercise", "kaya exercise",
            "kaunse exercise", "calories does", "calories burn", "burn calories", "calorie burn", "ketli calories burn",
            "kitni calories burn", "give me a beginner", "how to improve", "how can i", "how do i improve",
            "how to build stamina", "best exercise", "exercises target", "legs mate"
        ]) or (
            has_q_word and any(bool(re.search(pat, lower)) for pat in WORKOUT_PATTERNS)
        )
        if is_fitness_advisory:
            return "FITNESS_ADVISORY"

        # 4. Query Hydration Log
        is_water_query = any(w in lower for w in [
            "how much water did i drink", "how much water today", "how much water have i drank",
            "water intake today", "did i drink enough water", "water status", "how much water is left",
            "how much water left", "water goal reached", "water target", "how many glasses of water",
            "ketlu pani baki", "pani baki chhe", "pani baki hai",
            "કેટલું પાણી પીધું", "કેટલું પાણી", "પાણી કેટલું", "કેટલા ગ્લાસ પાણી",
            "कितना पानी पिया", "पानी कितना पिया", "कितना पानी बाकी"
        ]) or (
            ("water" in lower or "pani" in lower or "paani" in lower or "પાણી" in lower or "पानी" in lower) and
            any(w in lower for w in ["how much", "status", "goal", "target", "ketlu", "kitna", "baki", "left so far", "reach", "did i drink", "did i have", "ketla glass"])
        )
        if is_water_query:
            return "QUERY_HYDRATION_LOG"

        # 5. Daily Overall Summary intent
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

        # 6. Daily Nutrition Summary & Queries
        is_summary = any(w in lower for w in [
            "total calories", "calories total", "how many calories today", "calorie count",
            "today's intake", "daily progress", "macro summary", "nutrition summary",
            "ketli calories", "ketlu khadhu", "aaj nu ketlu thayu", "ketlu baki chhe",
            "ketli baki chhe", "aaj ni summary", "aaj nu summary",
            "aaj ka total", "kitni calories", "kitna khaya", "aaj ka kitna hua", "kitna baki hai",
            "kitni baki hai", "kitna bacha hai",
            "આજનું ટોટલ", "કેટલી કેલરી", "કેટલું ખાધું", "કેટલું બાકી છે",
            "आज का टोटल", "कितनी कैलोरी", "कितना खाया", "कितना बाकी है", "कितना बचा है"
        ])
        if is_summary:
            return "QUERY_FOOD_LOG"

        # 0. Question / Advisory / Negative / Hypothetical / 3rd-party check -> GENERAL_CHAT (DO NOT LOG)
        is_third_party = any(w in lower for w in [
            "my friend", "my brother", "my sister", "my mom", "my dad", "my father", "my mother",
            "my cousin", "my wife", "my husband", "someone else", "my roommate", "maro bhai", "mari ben",
            "maro dost", "maro mitra", "mera dost", "mera bhai", "meri behen", "dost ne"
        ])
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
        ]) or bool(re.search(r"\b(?:ate|drank|had|khadhu|pidhu|khaya|piya)\s+0\b|\b0\s*(?:ml|gram|gms|g|glass|bowl|plate|piece|pcs|roti|rotli|basundi|water|pani|paani)\b", lower))
        
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

        # Future planned action (statement, not a question): "kale hu gym karish",
        # "kale aa khaysh", "tomorrow I will eat...".  These must NOT be logged as
        # completed.  Suggestion questions were already handled above (they return
        # FOOD_SUGGESTION / WORKOUT_SUGGESTION), so a message reaching here with a
        # future conjugation is a planned statement, not a question or suggestion.
        #
        # This check runs BEFORE the hypothetical/question gate because phrases like
        # "will eat" would otherwise be swallowed by is_hypothetical and lost.
        _FUTURE_CONJUGATIONS = (
            "khaysh", "khais", "khaish", "khayish", "khaunga", "khaungi", "khayega",
            "karish", "karis", "karaish", "karunga", "karungi", "karega",
            "jais", "jaish", "jayish", "jaunga", "jaungi", "jayega",
            "piysh", "piish", "piyish",
            "will eat", "will have", "will drink", "will do", "will go to gym",
            "karvano chhu", "khavano chhu", "javano chhu",
            "કરીશ", "ખાઈશ", "જઈશ", "પીશ", "करूंगा", "खाऊंगा", "जाऊंगा",
        )
        has_future_conjugation = any(fc in lower for fc in _FUTURE_CONJUGATIONS)
        if has_future_conjugation and not is_question:
            # Planned future action → do not log as completed.
            return "FUTURE_LOG"

        if is_third_party or is_hypothetical or is_negative or is_advisory or is_question:
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

        # Domain terms detection.
        # "lemon water"/"nimbu pani" (flavored water) and "pre workout"/"preworkout"
        # are hydration items now, not food — exclude their synonym targets and
        # literal FOOD_NOUNS entries so they don't register as has_explicit_food
        # and get double-counted as both food and hydration.
        _HYDRATION_ONLY_TARGETS = {"Lemon Water", "Coconut Water", "Jeera Water", "Pre Workout"}
        _HYDRATION_ONLY_LITERALS = {"water", "pani", "paani", "lemon water", "nimbu pani", "pre workout", "preworkout", "pre-workout"}
        has_explicit_food = any(w in lower for w in FOOD_NOUNS if w not in _HYDRATION_ONLY_LITERALS) or any(
            bool(re.search(rf"\b{re.escape(k)}\b", lower))
            for k, v in INDIAN_FOOD_SYNONYMS.items()
            if v not in _HYDRATION_ONLY_TARGETS
        )
        has_eating_verb = any(
            bool(re.search(rf"\b{re.escape(v)}\b", lower)) for v in EATING_VERBS
        )
        has_drinking_verb = any(
            bool(re.search(rf"\b{re.escape(v)}\b", lower)) for v in DRINKING_VERBS
        )
        has_workout = any(bool(re.search(pat, lower)) for pat in WORKOUT_PATTERNS)
        
        # Check water (water or paani in non pani puri context).
        # Pre-workout is also a hydration item even with no "water" word in the
        # message (e.g. "had 1 scoop pre workout") since it's logged as a 250ml
        # default hydration entry.
        has_water = (any(w in lower for w in ["water", "paani", "pani", "pni", "panu", "પાણી", "पानी"]) or 
                     (re.search(r"\bpani\b", lower) and "pani puri" not in lower) or
                     bool(re.search(r"\bpre[-\s]?workout\b", lower)))

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
            "ઊંઘ", "સુઈ ગયો", "સુતો", "સુતી", "સોયા", "नींद"
        ])

        # Multi-log check (food + workout, food + water, or workout + water)
        if sum([bool(has_explicit_food), bool(has_workout), bool(has_water)]) >= 2:
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
            # Container/tiffin guard
            _CONTAINER_WORDS = {"dabbu", "dabba", "tiffin", "lunchbox", "lunch box", "ડબ્બો"}
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

        # Fuzzy intent detection for corrupted logging keywords with quantities / units / verbs
        has_fuzzy_workout = any(
            bool(re.search(pat, lower)) for pat in [
                r"\b(?:sqats?|skwats?|pusups?|pushupz|bnk\s*prss|bnch\s*prss|wlaked|wlkng|walkng|waking|yga|cycld|swm)\b",
                r"\b\d+\s*(?:reps?|sets?|mins?|minutes?|minutss|mnts|km)\b"
            ]
        )
        has_fuzzy_water = bool(re.search(r"\b(?:panu|pni|wtr|watr|watwr)\b", lower))
        has_fuzzy_food = any(
            bool(re.search(rf"\b{re.escape(k)}\b", lower))
            for k in [
                "chkn", "bresst", "brwn", "rce", "dahl", "daaal", "dl", "rti", "rwtli",
                "khaply", "chna", "masla", "whye", "prtein", "protn", "dhooodh",
                "egss", "aplle", "tosst", "smbar", "nartyal", "kdhi", "bakhrii", "mthii"
            ]
        ) or bool(re.search(r"\b\d+\s*(?:bowl|bowls|bwl|bwll|katori|ktori|vatki|vtk|plate|plt|plet|glass|gls|gllass|cup|scoop|scp|skup|piece|pcs|pc|pice|gm|gms|g|kg)\b", lower))

        if sum([bool(has_fuzzy_food), bool(has_fuzzy_workout), bool(has_fuzzy_water)]) >= 2:
            return "CREATE_MULTI_LOG"
        if has_fuzzy_water and not has_fuzzy_food:
            return "CREATE_HYDRATION_LOG"
        if has_fuzzy_workout and not has_fuzzy_food:
            return "CREATE_ACTIVITY_LOG"
        if has_fuzzy_food:
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
        - "lemon water", "1 glass lemon water" (flavored water -> hydration only)
        - "1 scoop pre-workout with 300ml water" -> single 300ml "Pre Workout" entry
        - "1 scoop pre workout" (no water mentioned) -> defaults to 250ml "Pre Workout"
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

            # ── Supplement (scoop) + water special-case ─────────────────────
            # Pre-workout and whey/protein-powder scoops mixed into water are
            # logged as a SINGLE hydration entry carrying BOTH the water
            # volume AND the supplement's nutrition (kcal/protein/carbs/fat/
            # fiber) — never as a separate food item plus a generic "Water"
            # entry. Handle this BEFORE the generic "with"-splitting below, so
            # "1 scoop pre-workout with 300 ml water" becomes exactly ONE
            # entry of 300 ml — not a separate plain-water entry.
            #
            # Pre-workout: the water mention is OPTIONAL (defaults to 250 ml
            # if omitted, e.g. "had 1 scoop pre workout").
            # Whey/protein powder: the water mention is REQUIRED here — if no
            # water is mentioned, protein stays a normal food item (handled by
            # extract_food_entities_heuristically), since protein is just as
            # often eaten dry / with milk / as a shake.
            line_for_clauses = line
            from .food_service import CANONICAL_INDIAN_FOOD_PROFILES  # lazy import avoids circular import

            def _supplement_water_ml(amt_str, unit_str):
                unit_str = (unit_str or "").lower()
                amt_val = float(amt_str)
                if unit_str in ("l", "litre", "liter", "liters", "litres"):
                    return amt_val * 1000.0
                if unit_str in ("glass", "glasses"):
                    return amt_val * 250.0
                if unit_str in ("cup", "cups"):
                    return amt_val * 200.0
                if unit_str == "bottle":
                    return amt_val * 750.0
                return amt_val  # bare "ml" or unitless number

            # NOTE: longer unit alternatives MUST come before shorter ones in the
            # alternation ("litre" before "l", "ml" before "l") — regex tries
            # alternatives left-to-right, so "l" would otherwise match the first
            # letter of "litre" and leave "itre water" unconsumed, causing the
            # water volume to leak out as a separate plain-water entry.
            _UNIT_ALT = r"ml|litre|liter|liters|litres|l|glass|glasses|cup|cups|bottle"

            supplement_specs = [
                # (compiled regex, beverage_name, canonical profile key)
                (
                    re.compile(
                        r"(?:(?P<qty>\d+(?:\.\d+)?)\s*scoops?\s*(?:of\s*)?)?pre[-\s]?workout\b"
                        rf"(?:\s+with\s+(?P<amt>\d+(?:\.\d+)?)\s*(?P<unit>{_UNIT_ALT})?"
                        r"(?:\s*(?:water|pani|paani|પાણી|पानी))?)?",
                        re.I,
                    ),
                    "Pre Workout", "Pre Workout",
                ),
                (
                    re.compile(
                        r"(?:(?P<qty>\d+(?:\.\d+)?)\s*scoops?\s*(?:of\s*)?)?(?:whey\s*protein|protein\s*powder|whey|protein)\b"
                        rf"\s+with\s+(?P<amt>\d+(?:\.\d+)?)\s*(?P<unit>{_UNIT_ALT})?"
                        r"\s*(?:water|pani|paani|પાણી|पानी)\b",
                        re.I,
                    ),
                    "Whey Protein Powder", "Whey Protein Powder",
                ),
            ]

            for pattern, bev_name, profile_key in supplement_specs:
                for sm in pattern.finditer(line):
                    gd = sm.groupdict()
                    qty = float(gd.get("qty") or 1.0)
                    if gd.get("amt"):
                        sup_amount = _supplement_water_ml(gd["amt"], gd.get("unit"))
                    else:
                        sup_amount = 250.0  # default serving when no water volume given (pre-workout only)

                    profile = CANONICAL_INDIAN_FOOD_PROFILES.get(profile_key, {})
                    sup_cal = round(float(profile.get("calories", 0.0)) * qty, 1)
                    sup_p = round(float(profile.get("protein_g", 0.0)) * qty, 1)
                    sup_c = round(float(profile.get("carbs_g", 0.0)) * qty, 1)
                    sup_f = round(float(profile.get("fat_g", 0.0)) * qty, 1)
                    sup_fib = round(float(profile.get("fiber_g", 0.0)) * qty, 1)

                    results.append({
                        "beverage_name": bev_name,
                        "beverageName": bev_name,
                        "waterAmount": sup_amount,
                        "amountMl": sup_amount,
                        "amount_ml": sup_amount,
                        "unit": "ml",
                        "quantity": qty,
                        "scoopUnit": "scoop",
                        "calories": sup_cal,
                        "proteinG": sup_p,
                        "carbsG": sup_c,
                        "fatG": sup_f,
                        "fiberG": sup_fib,
                        "logged_at": effective_dt.isoformat(),
                        "has_explicit_time": has_line_time,
                        "time_formatted": TimeService.format_time(effective_dt) if has_line_time else "",
                        "raw_text": sm.group(0).strip(),
                    })
                    # Remove the matched span so the generic clause loop below
                    # never re-processes the same "...ml water" fragment as
                    # plain water.
                    line_for_clauses = line_for_clauses.replace(sm.group(0), " ", 1)
            # ──────────────────────────────────────────────────────────────

            clauses = re.split(r",| and | ane | aur | અને | और | with | along with | sathe | સાથે | ساتھ میں | साथ में |\+", line_for_clauses, flags=re.I)
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
            (r"\bsquats?\b|\bsqats?\b|\bskwats?\b|સ્ક્વોટ્સ?|સ્કવોટ્સ?|स्क्वैट्स?", "Squats", 5.0, True),
            (r"\bpush-?ups?\b|\bpusups?\b|\bpushupz?\b|પુશઅપ્સ?|पुशअप્સ?|\bદંડ\b", "Push-ups", 4.5, True),
            (r"\bpull-?ups?\b|પુલઅપ્સ?|पुलअप्स?|ચિનઅપ", "Pull-ups", 5.0, True),
            (r"\blunges?\b|લંજીસ?|લંજ", "Lunges", 4.5, True),
            (r"\bcrunches?\b|sit-?ups?|ક્રંચ|क्रंचेस", "Crunches", 3.8, True),
            (r"\bplanks?\b|પ્લેન્ક|પ્લેંક|प्लैंक", "Plank", 3.5, False),
            (r"\bburpees?\b|બર્પી|बर्पी", "Burpees", 8.0, True),
            (r"\bjump(?:ing)?\s*jacks?\b|જમ્પિંગ\s*જેક", "Jumping Jacks", 8.0, True),
            (r"\bjump\s*rope\b|skipping|દોરડા\s*કૂદવા|रस्सी\s*कूद", "Jump Rope", 10.0, False),
            (r"\bbench\s*press\b|\bbnk\s*prss\b|\bbnch\s*prss\b|\bbnch\b|બેન્ચ\s*પ્રેસ|बेंच\s*प्रेस", "Bench Press", 5.5, True),
            (r"\bdeadlifts?\b|ડેડલિફ્ટ|डेडલિफ्ट", "Deadlift", 6.0, True),
            (r"\belliptical(?:\s*trainer)?\b", "Elliptical", 6.0, False),
            (r"\btreadmill\b", "Running", 8.0, False),
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
            clauses = re.split(r"[,;()&+]|\b(?:and|ane|aur|ne|nd|n|amd|with|wth|wid|then|pachi|pachhi|sathe|sath me|sath mein|તથા|અને|ને|સાથે|પછી|और|साथ में)\b", line_processed, flags=re.I)
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
                m_sets = re.search(r"(\d+)\s*(?:sets?|sts?|st\b|સેટ|सेट)", clause)
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
            # Protein/whey mixed WITH WATER is logged purely as a hydration
            # entry (see extract_hydration_entities' supplement_specs) and must
            # NOT also become a separate food item here. Replace the whole
            # matched span with a sentinel token BEFORE clause-splitting so the
            # later `with`-split clause ends up being exactly the sentinel,
            # which the skip-check below recognizes and discards.
            line = re.sub(
                r"\b(?:\d+(?:\.\d+)?\s*scoops?\s*(?:of\s*)?)?(?:whey\s*protein|protein\s*powder|whey|protein)\b"
                r"\s+with\s+\d+(?:\.\d+)?\s*(?:ml|litre|liter|liters|litres|l|glass|glasses|cup|cups|bottle)?"
                r"\s*(?:water|pani|paani|પાણી|पानी)\b",
                " \x00PROTEIN_WATER_SKIP\x00 ",
                line,
                flags=re.I,
            )
            
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

            # Split message into clauses using separators and Gujarati/English conjunctions
            clauses = re.split(
                r"[,;()&+]|\b(?:and|ane|aur|ne|nd|n|amd|with|wth|wid|then|pachi|pachhi|sathe|sath me|sath mein|તથા|અને|ને|સાથે|પછી|और|साथ में)\b",
                line,
                flags=re.I
            )

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

                # Foods that merely CONTAIN the word "water"/"pani" but are not
                # water at all (pani puri, watermelon) must still be treated as food.
                is_food_despite_water_word = any(w in c_low for w in [
                    "pani puri", "water melon", "watermelon",
                    "પાણીપુરી", "પાણી પૂરી", "પાની પુરી", "पानी पुरी"
                ])

                # Flavored "waters" (lemon/coconut/jeera/detox) are tracked purely
                # as hydration — extract_hydration_entities() captures them with
                # the correct amount/beverage name. Logging them here too would
                # double-count the same drink as both a food card and a hydration
                # entry (the duplicate-lemon-water bug).
                is_flavored_water = any(w in c_low for w in [
                    "lemon water", "lamon water", "nimbu pani", "nimbu paani", "leembu pani", "limbu pani",
                    "coconut water", "nariyal pani", "nariyal paani",
                    "jeera water", "jeera pani", "detox water",
                    "લીંબુ પાણી", "નીંબુ પાની", "નાળિયેર પાણી", "નારિયલ પાની", "જીરું પાણી",
                ])

                # Skip pure water clauses
                is_pure_water = (
                    any(w in c_low for w in ["pani", "water", "watwr", "paani", "પાણી", "પાની", "पानी"])
                    and not is_food_despite_water_word
                )
                if is_pure_water or is_flavored_water:
                    continue

                # Pre-workout supplement: tracked as hydration (scoop mixed into
                # water), never as a separate food/calorie entry. Skip it here;
                # extract_hydration_entities() creates the "Pre Workout" entry.
                is_pre_workout = bool(re.search(r"\bpre[-\s]?workout\b", c_low))
                if is_pre_workout:
                    continue

                # Whey/protein powder mixed WITH WATER is also tracked as a
                # single hydration entry carrying the supplement's nutrition
                # (flagged by the line-level pre-pass below, which marks the
                # exact clause span with a sentinel so we never double-count
                # it as a separate food item). Protein eaten WITHOUT water
                # (dry scoop, with milk, as a pre-made shake, etc.) is left
                # untouched here and stays a normal food item.
                if clause.strip() == "\x00PROTEIN_WATER_SKIP\x00":
                    continue

                # Skip exercise, muscle groups, or sleep
                is_activity_or_sleep = (
                    any(bool(re.search(pat, c_low)) for pat in [
                        r"\b(?:walk|walked|walking|run|running|ran|gym|cycling|swimming|yoga|badminton|cricket)\b",
                        r"\b(?:kasrat|vyayam|cardio|stretching|aerobics|hiit)\b",
                        r"(?<!pre[-\s])\bworkout\b",
                        r"\b(?:biceps?|triceps?|delts?|quads?|hamstrings?|glutes?|calves|abs|core|chest|shoulders?|lats?|forearms?)\b",
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
                    if clean.lower() in [
                        "aa badhu", "badhu", "ye sab", "sab", "log", "all", "today", "aaj", "aaje", "badhu j",
                        # Common non-food filler/verb leftovers that must never
                        # become a food entity (e.g. "Today I did in morning").
                        "did", "do", "done", "doing", "karyu", "karya", "kari", "kर्या",
                        "i", "me", "my", "was", "is", "am", "the", "a", "an", "to", "then",
                        "morning", "afternoon", "evening", "night", "day", "time",
                    ]:
                        continue

                    # Multi-item sub-segmentation: If clean contains multiple space-separated food items
                    # (e.g. "roti paneer dal rice"), detect if tokens can be separated into multiple entities
                    sub_items = [clean]
                    clean_words = clean.split()
                    clean_low = clean.lower()
                    is_compound_phrase = (clean_low in INDIAN_FOOD_SYNONYMS) or any(
                        re.search(rf"\b{re.escape(k)}\b", clean_low) for k in INDIAN_FOOD_SYNONYMS if " " in k
                    )
                    if len(clean_words) >= 2 and not is_compound_phrase:
                        # Check if all or multiple words are distinct food items
                        matched_words = []
                        for cw in clean_words:
                            cw_low = cw.lower()
                            if cw_low in INDIAN_FOOD_SYNONYMS:
                                matched_words.append(cw)
                            elif cw_low in [f.lower() for f in FOOD_NOUNS]:
                                matched_words.append(cw)
                        if len(matched_words) >= 2 and len(matched_words) == len(clean_words):
                            sub_items = matched_words

                    for sub_clean in sub_items:
                        canonical = None
                        is_recognized = False

                        # 1. Exact lookup
                        if sub_clean.lower() in INDIAN_FOOD_SYNONYMS:
                            canonical = INDIAN_FOOD_SYNONYMS[sub_clean.lower()]
                            is_recognized = True

                        # 2. Check multi-word phrase keys first (longest first) with strict boundaries
                        if not canonical:
                            for food_key in sorted(INDIAN_FOOD_SYNONYMS.keys(), key=len, reverse=True):
                                if any(ord(c) > 127 for c in food_key):
                                    if food_key == sub_clean or food_key in sub_clean.split() or f" {food_key} " in f" {sub_clean} ":
                                        canonical = INDIAN_FOOD_SYNONYMS[food_key]
                                        is_recognized = True
                                        break
                                else:
                                    if re.search(rf"\b{re.escape(food_key)}\b", sub_clean, flags=re.I):
                                        canonical = INDIAN_FOOD_SYNONYMS[food_key]
                                        is_recognized = True
                                        break

                        # 3. Check single tokens
                        if not canonical:
                            tokens = sub_clean.split()
                            for t in tokens:
                                if t.lower() in INDIAN_FOOD_SYNONYMS:
                                    canonical = INDIAN_FOOD_SYNONYMS[t.lower()]
                                    is_recognized = True
                                    break

                        # 4. Check known FOOD_NOUNS with strict boundaries
                        if not canonical:
                            for noun in sorted(FOOD_NOUNS, key=len, reverse=True):
                                if any(ord(c) > 127 for c in noun):
                                    if noun == sub_clean or noun in sub_clean.split() or f" {noun} " in f" {sub_clean} ":
                                        canonical = noun.title()
                                        is_recognized = True
                                        break
                                else:
                                    if re.search(rf"\b{re.escape(noun)}\b", sub_clean, flags=re.I):
                                        canonical = noun.title()
                                        is_recognized = True
                                        break

                        # 5. Connect to RapidFuzz match_food from food_matcher
                        if not canonical:
                            try:
                                from .food_matcher import match_food
                                m_res = match_food(sub_clean)
                                if m_res.status == "matched" and m_res.matched_name:
                                    canonical = m_res.matched_name
                                    is_recognized = True
                            except Exception:
                                pass

                        # If unrecognized, preserve user's exact food name; do NOT invent or guess random foods
                        if not canonical:
                            canonical = sub_clean.title()

                        # Context-aware default unit when unit was not specified or quantity was not explicitly given
                        item_unit = unit
                        if not has_explicit_qty or item_unit == "serving":
                            c_lower = canonical.lower()
                            if any(w in c_lower for w in ["powder", "whey", "pre workout", "preworkout"]):
                                item_unit = "scoop"
                            elif any(w in c_lower for w in ["shake", "smoothie"]):
                                item_unit = "scoop"
                            elif any(w in c_lower for w in ["coffee", "tea", "chai"]):
                                item_unit = "cup"
                            elif any(w in c_lower for w in ["milk", "doodh", "dudh", "chaas", "chhas", "lassi", "juice"]):
                                item_unit = "glass"
                            elif any(w in c_lower for w in ["roti", "rotli", "bhakri", "thepla", "egg", "banana", "apple", "chapati", "phulka", "naan", "paratha", "poori", "toast", "papad"]):
                                item_unit = "piece"
                            elif any(w in c_lower for w in ["dal", "daal", "rice", "chawal", "khichdi", "sabzi", "shaak", "curd", "dahi", "salad", "kadhi", "sambar", "chole", "rajma"]):
                                item_unit = "bowl"

                        item_qty = qty if has_explicit_qty else 1.0
                        confidence = 0.95 if is_recognized else 0.3
                        requires_clarification = not is_recognized
                        clarification_reason = "UNKNOWN_FOOD" if not is_recognized else None

                        results.append({
                            "food": canonical,
                            "food_name": canonical,
                            "quantity": item_qty,
                            "unit": item_unit,
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

    @staticmethod
    def evaluate_extraction_completeness(
        message: str,
        extracted_foods: Optional[Any] = None,
        extracted_acts: Optional[Any] = None,
        extracted_hyd: Optional[Any] = None,
        detected_intent: Optional[str] = None,
    ) -> str:
        """
        Calculates extraction completeness and explicit routing decision:
          - DETERMINISTIC_HIGH_CONFIDENCE
          - DETERMINISTIC_LOW_CONFIDENCE
          - FUZZY_FALLBACK_REQUIRED
          - LLM_REQUIRED
          - AMBIGUOUS
        """
        # Handle flexible argument orders
        if isinstance(extracted_foods, str) and detected_intent is None:
            detected_intent = extracted_foods
            extracted_foods = extracted_acts if isinstance(extracted_acts, list) else None
            extracted_acts = extracted_hyd if isinstance(extracted_hyd, list) else None
            extracted_hyd = None

        foods = [f for f in (extracted_foods or []) if isinstance(f, dict)]
        acts = [a for a in (extracted_acts or []) if isinstance(a, dict)]
        hyds = [h for h in (extracted_hyd or []) if isinstance(h, dict)]
        intent = detected_intent or AgentNLP.detect_intent(message)

        # 1. Non-logging queries or advisory -> deterministic high confidence
        if intent in ("GENERAL_CHAT", "FITNESS_ADVISORY", "FOOD_SUGGESTION", "WORKOUT_SUGGESTION", "DAILY_SUMMARY", "QUERY_FOOD_LOG", "QUERY_HYDRATION_LOG"):
            return "DETERMINISTIC_HIGH_CONFIDENCE"

        # 2. Simple single measurement logs (Weight, Sleep)
        if intent == "CREATE_WEIGHT_LOG":
            return "DETERMINISTIC_HIGH_CONFIDENCE"
        if intent == "CREATE_SLEEP_LOG":
            return "DETERMINISTIC_HIGH_CONFIDENCE"

        # 3. Hydration log
        if intent == "CREATE_HYDRATION_LOG":
            if hyds and len(hyds) > 0:
                return "DETERMINISTIC_HIGH_CONFIDENCE"
            return "FUZZY_FALLBACK_REQUIRED"

        # 4. Activity log
        if intent == "CREATE_ACTIVITY_LOG":
            if acts and len(acts) > 0:
                if any(a.get("activity") and a["activity"] != "Workout" for a in acts):
                    return "DETERMINISTIC_HIGH_CONFIDENCE"
                if acts[0].get("activity") == "Workout" and not acts[0].get("requiresClarification"):
                    return "DETERMINISTIC_HIGH_CONFIDENCE"
            return "FUZZY_FALLBACK_REQUIRED"

        # 5. Food / Multi logging
        if intent in ("CREATE_FOOD_LOG", "CREATE_MULTI_LOG"):
            total_extracted = len(foods) + len(acts) + len(hyds)
            if total_extracted == 0:
                return "LLM_REQUIRED"

            # Check for unrecognized / low confidence food items
            unrecognized_count = sum(1 for f in foods if not f.get("is_recognized", True) or f.get("confidence", 1.0) < 0.8)
            if unrecognized_count > 0:
                return "FUZZY_FALLBACK_REQUIRED"

            # Check if multi-domain items were cleanly extracted with high confidence
            domain_count = sum([bool(foods), bool(acts), bool(hyds)])
            if domain_count >= 2 and total_extracted >= 2 and unrecognized_count == 0:
                return "DETERMINISTIC_HIGH_CONFIDENCE"

            # Common conversational prefixes and section headers to ignore when counting clauses
            _HEADER_PATTERNS = re.compile(
                r"^(today|yesterday|tomorrow|aaj|aaje|kal|kale|morning|savar|savare|evening|sanje|afternoon|bapore|night|ratre|subah|shaam|dophar|raat|routine|schedule|summary|here is|my|i did|i had|i ate|done in|logged in|diet|meals?|plan)\b",
                re.I
            )

            # Estimate likely clauses/items in raw message
            raw_clauses = re.split(
                r"[,;()&+]|\b(?:and|ane|aur|ne|nd|n|amd|with|wth|wid|then|pachi|pachhi|sathe|sath me|sath mein|તથા|અને|ને|સાથે|પછી|और|साथ में)\b|\n+",
                message,
                flags=re.I
            )
            # Filter out non-item clauses (e.g. greetings, time words, pure numbers, headers)
            meaningful_clauses = [
                c.strip() for c in raw_clauses
                if c.strip() and len(re.sub(r"[^\w\u0A80-\u0AFF\u0900-\u097F]", "", c)) >= 2
                and not c.strip().lower() in ["aa badhu", "badhu", "ye sab", "sab log", "log kari do", "log kar do", "log this", "please"]
                and not (not re.search(r"\d", c) and _HEADER_PATTERNS.search(c.strip()))
            ]

            # If meaningful clauses exceed extracted items significantly -> partial extraction
            if len(meaningful_clauses) > total_extracted + 1:
                return "FUZZY_FALLBACK_REQUIRED"

            return "DETERMINISTIC_HIGH_CONFIDENCE"

        return "AMBIGUOUS"
