# -*- coding: utf-8 -*-
with open('backend/app/services/agent_nlp.py', 'r', encoding='utf-8') as f:
    text = f.read()

start_marker = "        fuzzy_vocab = ["
end_marker = "    @staticmethod\n    def extract_weight_entity(text: str) -> Dict[str, Any]:"

start_pos = text.find(start_marker)
end_pos = text.find(end_marker)

print(f"start_pos: {start_pos}, end_pos: {end_pos}")

replacement = '''        fuzzy_vocab = [
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
                matches = difflib.get_close_matches(w_clean, fuzzy_vocab, n=1, cutoff=0.85)
                if matches:
                    prefix = re.match(r"^[^\w]+", w)
                    suffix = re.search(r"[^\w]+$", w)
                    p_str = prefix.group(0) if prefix else ""
                    s_str = suffix.group(0) if suffix else ""
                    corrected_words.append(p_str + matches[0] + s_str)
                    continue
            corrected_words.append(w)
        return " ".join(corrected_words)

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

        # 2. Daily Nutrition Summary intent
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

        # 3. Query Hydration Log
        is_water_query = any(w in lower for w in [
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

        # 4. Daily Overall Summary intent
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

        # 5. Food Suggestions intent
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
            "શું ખાવા જોઈએ", "શું ખાવું", "શું ખાઉં", "ડિનરમાં શું બનાવવું", "લંચમાં શું ખાવું", "નાસ્તામાં શું લેવું", "સ્વસ્થ ખોરાક", "શું જમવું",
            "क्या खाना चाहिए", "क्या खाऊं", "क्या खाएं", "डिनर में क्या बनाऊं", "लंच में क्या खाऊं", "नाश्ते में क्या लें", "हेल्दी खाना"
        ])
        if is_food_suggestion:
            return "FOOD_SUGGESTION"

        # 6. Workout Suggestions intent
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
        has_q_word = bool(re.search(r"\\b(?:what|how|which|why|give me|suggest|batao|aapo|kya|kaise|kaunse|shu|kem|kaya|kai)\\b", lower)) or "?" in lower or any(ch in lower for ch in ["કયા", "શું", "કેમ", "કેવી રીતે", "ફાયદા", "ફાયદો", "क्या", "कैसे", "कौनसे", "फायदे"])
        is_fitness_advisory = any(w in lower for w in [
            "benefits of", "benefit of", "fayda", "fayde", "faida", "faide", "લાભ", "ફાયદા", "ફાયદો", "ફायदे", "लाभ",
            "workout plan", "routine plan", "exercise plan", "beginner workout", "beginner plan", "workout for beginner",
            "stamina", "endurance", "સ્ટેમિના", "સ્ટિમિના", "दम", "improve my stamina", "improve stamina", "increase stamina",
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

        # Domain terms detection
        has_explicit_food = any(w in lower for w in FOOD_NOUNS if w not in ("water", "pani", "paani")) or any(
            bool(re.search(rf"\\b{re.escape(k)}\\b", lower))
            for k, v in INDIAN_FOOD_SYNONYMS.items()
            if v not in ("Water",)
        )
        has_eating_verb = any(
            bool(re.search(rf"\\b{re.escape(v)}\\b", lower)) for v in EATING_VERBS
        )
        has_drinking_verb = any(
            bool(re.search(rf"\\b{re.escape(v)}\\b", lower)) for v in DRINKING_VERBS
        )
        has_workout = any(bool(re.search(pat, lower)) for pat in WORKOUT_PATTERNS)
        
        # Check water (water or paani in non pani puri context)
        has_water = (any(w in lower for w in ["water", "paani", "pani", "pni", "panu", "પાણી", "पानी"]) or 
                     (re.search(r"\\bpani\\b", lower) and "pani puri" not in lower))

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
            # Container/tiffin guard
            _CONTAINER_WORDS = {"dabbu", "dabba", "tiffin", "lunchbox", "lunch box", "ડબ્બો"}
            _CONTAINER_ACTIONS = {
                "khali", "saaf", "bharo", "lai", "muki", "rakh", "dho", "pack",
                "empty", "clean", "fill", "खाली", "साफ",
            }
            has_container = any(
                bool(re.search(rf"\\b{re.escape(cw)}\\b", lower)) for cw in _CONTAINER_WORDS
            )
            has_container_action = any(
                bool(re.search(rf"\\b{re.escape(ca)}\\b", lower)) for ca in _CONTAINER_ACTIONS
            )
            if has_container and has_container_action and not has_explicit_food:
                return "GENERAL_CHAT"
            return "CREATE_FOOD_LOG"

        # Fuzzy intent detection for corrupted logging keywords with quantities / units / verbs
        has_fuzzy_workout = any(
            bool(re.search(pat, lower)) for pat in [
                r"\\b(?:sqats?|skwats?|pusups?|pushupz|bnk\\s*prss|bnch\\s*prss|wlaked|wlkng|walkng|waking|yga|cycld|swm)\\b",
                r"\\b\\d+\\s*(?:reps?|sets?|mins?|minutes?|minutss|mnts|km)\\b"
            ]
        )
        has_fuzzy_water = bool(re.search(r"\\b(?:panu|pni|wtr|watr|watwr)\\b", lower))
        has_fuzzy_food = any(
            bool(re.search(rf"\\b{re.escape(k)}\\b", lower))
            for k in [
                "chkn", "bresst", "brwn", "rce", "dahl", "daaal", "dl", "rti", "rwtli",
                "khaply", "chna", "masla", "whye", "prtein", "protn", "dhooodh",
                "egss", "aplle", "tosst", "smbar", "nartyal", "kdhi", "bakhrii", "mthii"
            ]
        ) or bool(re.search(r"\\b\\d+\\s*(?:bowl|bowls|bwl|bwll|katori|ktori|vatki|vtk|plate|plt|plet|glass|gls|gllass|cup|scoop|scp|skup|piece|pcs|pc|pice|gm|gms|g|kg)\\b", lower))

        if (has_fuzzy_food and has_fuzzy_workout) or (has_fuzzy_food and has_fuzzy_water):
            return "CREATE_MULTI_LOG"
        if has_fuzzy_water and not has_fuzzy_food:
            return "CREATE_HYDRATION_LOG"
        if has_fuzzy_workout and not has_fuzzy_food:
            return "CREATE_ACTIVITY_LOG"
        if has_fuzzy_food:
            return "CREATE_FOOD_LOG"

        return "GENERAL_CHAT"\n\n'''

if start_pos != -1 and end_pos != -1:
    new_text = text[:start_pos] + replacement + text[end_pos:]
    with open('backend/app/services/agent_nlp.py', 'w', encoding='utf-8') as f:
        f.write(new_text)
    print("Replacement success!")
else:
    print("Could not find markers.")
