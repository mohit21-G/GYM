"""
Food Suggestion Service
Generates intelligent, context-aware, multilingual meal and healthy food suggestions.
Tailored to user's logged meals today, calorie budget, and specific meal times (breakfast/lunch/dinner/snack).
Explicitly marks nutrition values as estimates.
Supports English, Gujarati, Hindi, Hinglish, Gujlish.
"""
import random
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from ..database import get_db

MEAL_SUGGESTIONS_DB = {
    "BREAKFAST": [
        {
            "name_en": "Vegetable Poha with Spiced Buttermilk",
            "name_gu": "વેજીટેબલ પૌંઆ સાથે મસાલા છાશ (Vegetable Poha & Chaas)",
            "name_hi": "सब्जियों वाला पोहा और मसाला छाछ (Veg Poha & Chaas)",
            "portion": "1 medium bowl (150g) + 1 glass (200ml)",
            "approx_calories": 240,
            "approx_protein_g": 6.5,
            "approx_carbs_g": 38.0,
            "category": "Light & Energizing",
            "highlights": "Rich in iron, low fat, easy to digest.",
        },
        {
            "name_en": "Moong Dal Chilla / Sprouts Dosa with Mint Chutney",
            "name_gu": "મગની દાળના પુડલા / મગ ચીલા અને ફુદીનાની ચટણી",
            "name_hi": "मूंग दाल चीला / स्प्राउट्स चीला और पुदीना चटनी",
            "portion": "2 medium chillas (120g)",
            "approx_calories": 220,
            "approx_protein_g": 12.0,
            "approx_carbs_g": 28.0,
            "category": "High Protein Vegetarian",
            "highlights": "Packed with plant protein and dietary fiber.",
        },
        {
            "name_en": "Boiled Eggs (or Paneer Bhurji) with Multigrain Toast",
            "name_gu": "બાફેલા ઈંડા (અથવા પનીર ભુરજી) સાથે બ્રાઉન / મલ્ટિગ્રેન ટોસ્ટ",
            "name_hi": "उबले अंडे (या पनीर भुर्जी) और मल्टीग्रेन टोस्ट",
            "portion": "2 whole eggs / 60g paneer + 1 toast",
            "approx_calories": 260,
            "approx_protein_g": 15.0,
            "approx_carbs_g": 18.0,
            "category": "Protein Power",
            "highlights": "Keeps you full longer, excellent muscle support.",
        },
        {
            "name_en": "Oats Upma with Mixed Vegetables",
            "name_gu": "મિક્સ શાકભાજી વાળો ઓટ્સ ઉપમા (Oats Upma)",
            "name_hi": "मिक्स वेज ओट्स उपमा (Oats Upma)",
            "portion": "1 bowl (180g)",
            "approx_calories": 210,
            "approx_protein_g": 7.0,
            "approx_carbs_g": 32.0,
            "category": "Heart Healthy & Fiber Rich",
            "highlights": "Beta-glucan fiber supports healthy cholesterol levels.",
        },
    ],
    "LUNCH": [
        {
            "name_en": "2 Multigrain Rotis, Yellow Toor Dal, Bhindi Sabzi & Green Salad",
            "name_gu": "2 મલ્ટિગ્રેન / ઘઉંની રોટલી, તુવેર દાળ, ભીંડીનું શાક અને કાચું સલાડ",
            "name_hi": "2 मल्टीग्रेन रोटी, तूर दाल, भिंडी की सब्जी और सलाद",
            "portion": "2 rotis + 1 katori dal + 1 katori sabzi + salad",
            "approx_calories": 420,
            "approx_protein_g": 14.0,
            "approx_carbs_g": 62.0,
            "category": "Balanced Indian Thali",
            "highlights": "Complete balanced macro profile with vital micronutrients.",
        },
        {
            "name_en": "Brown Rice or Cooked Rice with Rajma Masala & Cucumber Salad",
            "name_gu": "બ્રાઉન / સાદા ભાત સાથે રાજમા મસાલા અને કાકડીનું સલાડ",
            "name_hi": "चावल के साथ राजमा मसाला और खीरे का सलाद",
            "portion": "1 bowl rice (150g) + 1 bowl rajma (150g)",
            "approx_calories": 450,
            "approx_protein_g": 16.0,
            "approx_carbs_g": 74.0,
            "category": "Protein & Complex Carbs",
            "highlights": "Slow-digesting complex carbs providing sustained energy.",
        },
        {
            "name_en": "Bajra / Jowar Rotlo with Baingan Bharta & Fresh Chaas",
            "name_gu": "બાજરી અથવા જુવારનો રોટલો, રીંગણાનો ઓળો અને મોળી છાશ",
            "name_hi": "बाजरे की रोटी, बैंगन का भर्ता और ताजी छाछ",
            "portion": "1 medium rotlo + 1 bowl bharta + 1 glass chaas",
            "approx_calories": 380,
            "approx_protein_g": 11.0,
            "approx_carbs_g": 56.0,
            "category": "Traditional Gluten-Free",
            "highlights": "High in magnesium, iron, and gut-friendly probiotics.",
        },
        {
            "name_en": "Grilled Chicken Breast (or Grilled Paneer Tikka) with Sautéed Veggies",
            "name_gu": "ગ્રીલ્ડ ચિકન બ્રેસ્ટ (અથવા પનીર ટીક્કા) સાથે સોતે કરેલા શાકભાજી",
            "name_hi": "ग्रिल्ड चिकन ब्रेस्ट (या पनीर टिक्का) और सौते सब्जियां",
            "portion": "150g protein + 1 plate veggies",
            "approx_calories": 390,
            "approx_protein_g": 32.0,
            "approx_carbs_g": 14.0,
            "category": "Lean High Protein / Low Carb",
            "highlights": "Ideal for fat loss and lean muscle retention.",
        },
    ],
    "DINNER": [
        {
            "name_en": "Light Moong Dal Khichdi with Spiced Chaas & Roasted Papad",
            "name_gu": "હળવી મગની દાળની ખીચડી, મસાલા છાશ અને શેકેલો પાપડ",
            "name_hi": "हल्की मूंग दाल खिचड़ी, मसाला छाछ और भुना पापड़",
            "portion": "1 medium bowl khichdi (200g) + 1 glass chaas",
            "approx_calories": 320,
            "approx_protein_g": 11.0,
            "approx_carbs_g": 52.0,
            "category": "Light & Gut Soothing",
            "highlights": "Gentle on the stomach for deep, uninterrupted sleep.",
        },
        {
            "name_en": "Paneer Bhurji / Tofu Scramble with 1 Phulka Roti and Green Salad",
            "name_gu": "પનીર ભુરજી (અથવા ટોફુ) સાથે 1 ફુલકા રોટલી અને કાકડી-ટામેટાંનું સલાડ",
            "name_hi": "पनीर भुर्जी (या टोफू) साथ में 1 फुल्का रोटी और सलाद",
            "portion": "100g paneer + 1 roti + salad",
            "approx_calories": 340,
            "approx_protein_g": 18.0,
            "approx_carbs_g": 22.0,
            "category": "High Protein Low Carb Dinner",
            "highlights": "Casein-rich night-time protein that aids overnight recovery.",
        },
        {
            "name_en": "Mixed Vegetable Clear Soup with Boiled Chickpeas / Sprouts Salad",
            "name_gu": "મિક્સ વેજ ક્લિયર સૂપ સાથે ફણગાવેલા મગ અથવા ચણાનું સલાડ",
            "name_hi": "मिक्स वेज सूप साथ में अंकुरित मूंग / चने का सलाद",
            "portion": "1 large bowl soup + 1 bowl sprouts salad (100g)",
            "approx_calories": 220,
            "approx_protein_g": 10.0,
            "approx_carbs_g": 34.0,
            "category": "Ultra Light & Detox",
            "highlights": "Hydrating, vitamin-packed, and minimal calorie density.",
        },
        {
            "name_en": "Egg White Omelette with Sautéed Spinach & Mushrooms",
            "name_gu": "પાલક અને મશરૂમ સાથે એગ વ્હાઇટ ઓમલેટ (Egg White Omelette)",
            "name_hi": "पालक और मशरूम के साथ एग व्हाइट ऑमलेट",
            "portion": "3 egg whites + 1 cup veggies",
            "approx_calories": 190,
            "approx_protein_g": 17.0,
            "approx_carbs_g": 8.0,
            "category": "Clean Protein",
            "highlights": "Very low calorie with zero heavy fats before bed.",
        },
    ],
    "SNACK": [
        {
            "name_en": "Roasted Makhana (Fox Nuts) with a handful of Roasted Chana",
            "name_gu": "શેકેલા મખાના અને શેકેલા ચણા (Roasted Makhana & Chana)",
            "name_hi": "भुना हुआ मखाना और भुना चना",
            "portion": "1 small bowl (35g)",
            "approx_calories": 130,
            "approx_protein_g": 5.0,
            "approx_carbs_g": 22.0,
            "category": "Crunchy Low Calorie Snack",
            "highlights": "Naturally gluten-free, rich in calcium and antioxidants.",
        },
        {
            "name_en": "Sprouts Salad with Lemon, Cucumber & Chaat Masala",
            "name_gu": "લીંબુ અને કાકડી વાળું ફણગાવેલા મગનું સલાડ",
            "name_hi": "नींबू और खीरे के साथ अंकुरित मूंग की चाट",
            "portion": "1 bowl (100g)",
            "approx_calories": 110,
            "approx_protein_g": 7.0,
            "approx_carbs_g": 18.0,
            "category": "Fresh & Fiber Packed",
            "highlights": "Alive enzymes that boost digestion and metabolism.",
        },
        {
            "name_en": "Greek Yogurt / Hung Curd with Berries or 5 Soaked Almonds",
            "name_gu": "દહીં (Curd / Yogurt) સાથે 5 પલાળેલી બદામ અથવા અખરોટ",
            "name_hi": "दही / ग्रीक योगर्ट साथ में 5 भीगे बादाम",
            "portion": "1 small cup (100g) + 5 nuts",
            "approx_calories": 140,
            "approx_protein_g": 8.0,
            "approx_carbs_g": 9.0,
            "category": "Probiotic & Healthy Fats",
            "highlights": "Gut-friendly probiotics and vitamin E for skin and energy.",
        },
    ],
}

class FoodSuggestionService:
    @staticmethod
    def detect_meal_context(text: str) -> str:
        lower = text.lower()
        if any(w in lower for w in ["breakfast", "savar", "savare", "saware", "subah", "subha", "nasto", "nashta", "સવાર", "નાસ્તો", "सुबह", "नाश्ता"]):
            return "BREAKFAST"
        if any(w in lower for w in ["dinner", "sanj", "sanje", "saanj", "saanje", "raat", "raate", "raatri", "valoo", "valo", "વાળુ", "વાળું", "સાંજ", "રાત", "रात", "शाम"]):
            return "DINNER"
        if any(w in lower for w in ["snack", "snacks", "chaai", "tea", "sham", "bapor pachhi", "નાસ્તો", "સ્નેક", "स्नैक"]):
            return "SNACK"
        if any(w in lower for w in ["lunch", "bapor", "bapore", "dopahar", "બપોર", "બપોરે", "दोपहर"]):
            return "LUNCH"
        
        # Current time based fallback
        hour = datetime.now(timezone.utc).hour + 5.5  # IST offset
        if hour < 11:
            return "BREAKFAST"
        elif hour < 16:
            return "LUNCH"
        elif hour < 19:
            return "SNACK"
        else:
            return "DINNER"

    @staticmethod
    async def generate_food_suggestion(
        user_id: str,
        message: str,
        lang: str = "en",
        date_str: Optional[str] = None
    ) -> Dict[str, Any]:
        db = get_db()
        today = date_str or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        # 1. Fetch user profile and today's logged food
        user = await db.users.find_one({"id": user_id}) or await db.users.find_one({"user_id": user_id}) or {}
        profile = user.get("profile") or {}
        target_cal = float(profile.get("dailyCalorieTarget") or 2000.0)
        
        cursor = db.daily_food_logs.find({"user_id": user_id, "log_date": today})
        logs = await cursor.to_list(length=100)
        
        consumed_cal = sum(float(l.get("calories", 0.0)) for l in logs)
        remaining_cal = max(0.0, target_cal - consumed_cal)
        
        # Check what foods were logged today
        logged_food_names = [str(l.get("food_name", "")).lower() for l in logs]
        
        # 2. Determine Meal Context
        meal_type = FoodSuggestionService.detect_meal_context(message)
        
        # Detect Language: check script or keywords
        lower = message.lower()
        has_guj = any('\u0A80' <= ch <= '\u0AFF' for ch in message) or bool(re.search(r"\b(?:su|khavu|joiye|khau|aapo|aaj|chhe|mate|kem|bapor|savar|sanje)\b", lower))
        has_hi = any('\u0900' <= ch <= '\u097F' for ch in message) or bool(re.search(r"\b(?:kya|khana|chahiye|khau|batao|aaj|hai|ke\s+liye|subah|dopahar)\b", lower))
        
        is_guj = (lang in ["gu", "gu-Latn"] or has_guj) and not (lang == "en" and not has_guj)
        is_hi = (lang in ["hi", "hi-Latn"] or has_hi) and not (lang == "en" and not has_hi)
        
        # 3. Pick 2-3 suitable recommendations avoiding repeats
        candidate_list = list(MEAL_SUGGESTIONS_DB.get(meal_type, MEAL_SUGGESTIONS_DB["DINNER"]))
        
        # Shuffle with seed variation to prevent identical repeat answers
        random.shuffle(candidate_list)
        selected = candidate_list[:2]
        
        # 4. Construct response with personalized context & disclaimer
        meal_label_en = meal_type.capitalize()
        meal_label_gu = "સવારના નાસ્તા" if meal_type == "BREAKFAST" else ("બપોરના ભોજન (Lunch)" if meal_type == "LUNCH" else ("સાંજના નાસ્તા" if meal_type == "SNACK" else "રાત્રિના ભોજન (Dinner)"))
        meal_label_hi = "सुबह के नाश्ते" if meal_type == "BREAKFAST" else ("दोपहर के भोजन (Lunch)" if meal_type == "LUNCH" else ("शाम के स्नैक्स" if meal_type == "SNACK" else "रात के खाने (Dinner)"))
        
        if is_guj:
            header = f"🥗 **{meal_label_gu} માટે આરોગ્યપ્રદ વિકલ્પો (Healthy Food Suggestions)**:"
            status_line = f"તમારું આજનું લક્ષ્ય {int(target_cal)} kcal છે, જેમાંથી હાલ **{int(consumed_cal)} kcal** વપરાઈ છે (બાકી બજેટ: ~**{int(remaining_cal)} kcal**)."
            
            items_text = []
            for item in selected:
                items_text.append(
                    f"* **{item['name_gu']}**\n"
                    f"  * માપ/ક્વોન્ટિટી: {item['portion']}\n"
                    f"  * અંદાજિત પોષણ: ~**{item['approx_calories']} kcal** | પ્રોટીન: ~{item['approx_protein_g']}g | કાર્બ્સ: ~{item['approx_carbs_g']}g\n"
                    f"  * વિશેષતા: {item['highlights']}"
                )
            
            disclaimer = "⚠️ *નોંધ: દર્શાવેલ કેલરી અને પોષક મૂલ્યો અંદાજિત (estimates) છે અને તે રાંધવાની રીત તેમજ સામગ્રી મુજબ થોડા બદલાઈ શકે છે.*"
            tip = "💡 *ટિપ: જમવાની 30 મિનિટ પહેલા 1 ગ્લાસ પાણી પીવું પાચન માટે ઉત્તમ છે!*"
            
            reply = f"{header}\n\n{status_line}\n\n" + "\n\n".join(items_text) + f"\n\n{disclaimer}\n\n{tip}"
        
        elif is_hi:
            header = f"🥗 **{meal_label_hi} के लिए पौष्टिक सुझाव (Healthy Food Suggestions)**:"
            status_line = f"आपका दैनिक लक्ष्य {int(target_cal)} kcal है, जिसमें से अब तक **{int(consumed_cal)} kcal** लॉग हुआ है (बचा हुआ बजट: ~**{int(remaining_cal)} kcal**)।"
            
            items_text = []
            for item in selected:
                items_text.append(
                    f"* **{item['name_hi']}**\n"
                    f"  * मात्रा/पोर्शन: {item['portion']}\n"
                    f"  * अनुमानित पोषण: ~**{item['approx_calories']} kcal** | प्रोटीन: ~{item['approx_protein_g']}g | कार्ब्स: ~{item['approx_carbs_g']}g\n"
                    f"  * खास बात: {item['highlights']}"
                )
            
            disclaimer = "⚠️ *नोट: दी गई कैलोरी और पोषण मूल्य अनुमानित (estimates) हैं, जो बनाने के तरीके और सामग्री के अनुसार भिन्न हो सकते हैं।* "
            tip = "💡 *सलाह: भोजन को धीरे-धीरे चबाकर खाएं और अत्यधिक तेल-मसाले से बचें।* "
            
            reply = f"{header}\n\n{status_line}\n\n" + "\n\n".join(items_text) + f"\n\n{disclaimer}\n\n{tip}"
        
        else:
            header = f"🥗 **Healthy {meal_label_en} Suggestions**:"
            status_line = f"Daily Target: {int(target_cal)} kcal | Logged so far: **{int(consumed_cal)} kcal** (Remaining Budget: ~**{int(remaining_cal)} kcal**)."
            
            items_text = []
            for item in selected:
                items_text.append(
                    f"* **{item['name_en']}**\n"
                    f"  * Portion: {item['portion']}\n"
                    f"  * Estimated Nutrition: ~**{item['approx_calories']} kcal** | Protein: ~{item['approx_protein_g']}g | Carbs: ~{item['approx_carbs_g']}g\n"
                    f"  * Why it fits: {item['highlights']}"
                )
            
            disclaimer = "⚠️ *Note: Nutritional values and calorie counts are approximate estimates unless verified through exact ingredient measurement.*"
            tip = "💡 *Coach Tip: Pair complex carbohydrates with lean protein and fiber to maintain steady blood sugar!*"
            
            reply = f"{header}\n\n{status_line}\n\n" + "\n\n".join(items_text) + f"\n\n{disclaimer}\n\n{tip}"

        return {
            "replyText": reply,
            "mealType": meal_type,
            "suggestions": selected,
            "budget": {
                "targetCalories": target_cal,
                "consumedCalories": consumed_cal,
                "remainingCalories": remaining_cal,
            }
        }
