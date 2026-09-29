"""
Fitness Advisory Service
Provides comprehensive, expert-level, multilingual fitness and workout answers.
Supports English, Hindi, Gujarati, Hinglish, Gujlish, and Roman-script inputs.
"""
import re
from typing import Dict, Any, Optional

class FitnessAdvisoryService:
    @staticmethod
    def is_fitness_query(text: str) -> bool:
        lower = text.lower()
        
        # Explicit fitness/exercise question indicators
        triggers = [
            "benefit", "benefits", "fayda", "fayde", "faida", "faide", "લાભ", "ફાયદા", "ફાયદો", "फायदे", "लाभ",
            "workout plan", "routine plan", "exercise plan", "beginner workout", "beginner plan",
            "stamina", "endurance", "સ્ટેમિના", "स्टैमिना", "दम",
            "target the legs", "target legs", "leg exercise", "leg workout", "quads", "hamstrings", "calves",
            "chest exercise", "back exercise", "shoulder exercise", "abs exercise", "core exercise", "biceps", "triceps",
            "calories does", "calories burn", "burn calories", "calorie burn", "ketli calories burn", "kitni calories burn",
            "how to squat", "how to pushup", "how to run", "how to exercise", "which exercise", "kaya exercise",
            "improve my stamina", "improve stamina", "increase stamina", "stamina kem", "stamina kaise",
            "walking", "running", "jogging", "swimming", "cycling", "pushup", "squat", "yoga"
        ]
        
        has_trigger = any(t in lower for t in triggers)
        is_question = any(q in lower for q in ["?", "what", "how", "which", "give me", "suggest", "shu", "kem", "kaya", "kai", "kya", "kaise", "kaunse", "batao", "aapo"])
        
        return has_trigger and (is_question or "plan" in lower or "benefit" in lower or "fayda" in lower or "stamina" in lower)

    @staticmethod
    def generate_advisory_response(text: str, lang: str = "en") -> str:
        lower = text.lower()
        has_guj = any('\u0A80' <= ch <= '\u0AFF' for ch in text) or bool(re.search(r"\b(?:shu|kem|chhe|mate|aapo|kaya|fayda|thay|ma|karya|kari)\b", lower))
        has_hi = any('\u0900' <= ch <= '\u097F' for ch in text) or bool(re.search(r"\b(?:kya|kaise|hai|hain|ke\s+liye|batao|kaunse|fayde|fayda|kiya|kiye)\b", lower))

        is_guj = (lang in ["gu", "gu-Latn"] or has_guj) and not (lang == "en" and not has_guj)
        is_hi = (lang in ["hi", "hi-Latn"] or has_hi) and not (lang == "en" and not has_hi)

        # 1. Benefits of Walking
        if any(w in lower for w in ["walk", "chalne", "chalna", "chalo", "chalyo", "ચાલ", "टहल"]) and any(w in lower for w in ["benefit", "benefits", "fayda", "fayde", "faida", "લાભ", "ફાયદા", "फायदे", "good"]):
            if is_guj:
                return (
                    "🚶 **ચાલવાના મુખ્ય ફાયદા (Benefits of Walking)**:\n\n"
                    "* **હૃદયનું સ્વાસ્થ્ય**: નિયમિત ચાલવાથી બ્લડ પ્રેશર કંટ્રોલમાં રહે છે અને હૃદય મજબૂત બને છે.\n"
                    "* **કેલરી બર્ન & વજન નિયંત્રણ**: 30 મિનિટ ઝડપી ચાલવાથી આશરે 120–150 કેલરી બર્ન થાય છે.\n"
                    "* **સાંધા અને સ્નાયુઓ**: સાંધા પર ભારે દબાણ નાખ્યા વગર પગના સ્નાયુઓ મજબૂત થાય છે.\n"
                    "* **માનસિક શાંતિ & ઊંઘ**: સ્ટ્રેસ અને ચિંતા ઓછી થાય છે, તથા રાત્રે સારી ઊંઘ આવે છે.\n"
                    "* **બ્લડ સુગર કંટ્રોલ**: જમ્યા પછી 10-15 મિનિટ સામાન્ય ચાલવાથી ડાયાબિટીસ અને સુગર સ્પાઇક્સ નિયંત્રિત રહે છે.\n\n"
                    "💡 *ટિપ: રોજ 30 થી 45 મિનિટ brisk walk (ઝડપી ચાલવું) શ્રેષ્ઠ પરિણામ આપે છે!*"
                )
            if is_hi:
                return (
                    "🚶 **टहलने / वॉकिंग के मुख्य फायदे (Benefits of Walking)**:\n\n"
                    "* **दिल की सेहत**: रोजाना वॉक करने से ब्लड प्रेशर नियंत्रित रहता है और हार्ट अटैक का खतरा कम होता है।\n"
                    "* **वजन नियंत्रण**: 30 मिनट तेज चलने से लगभग 120–150 कैलोरी बर्न होती है।\n"
                    "* **जोड़ों और हड्डियों के लिए सुरक्षित**: बिना जोड़ों पर तनाव डाले पैरों की मांसपेशियां मजबूत होती हैं।\n"
                    "* **मानसिक तनाव से राहत**: एंडोर्फिन रिलीज होता है जिससे मूड बेहतर होता है और तनाव घटता है।\n"
                    "* **ब्लड शुगर नियंत्रण**: भोजन के बाद 15 मिनट टहलने से शुगर लेवल स्थिर रहता है।\n\n"
                    "💡 *सुझाव: हफ्ते में कम से कम 5 दिन 30 मिनट ब्रिस्क वॉक जरूर करें!*"
                )
            return (
                "🚶 **Key Benefits of Walking**:\n\n"
                "* **Cardiovascular Health**: Strengthens your heart, improves circulation, and lowers resting blood pressure.\n"
                "* **Weight Management**: Burns ~120–160 kcal per 30 minutes of brisk walking (approx. 5 km/h).\n"
                "* **Joint Mobility & Muscle Tone**: Low-impact aerobic movement that lubricates joints and tones legs.\n"
                "* **Mental Clarity & Stress Relief**: Stimulates endorphin release, lowers cortisol, and promotes restful sleep.\n"
                "* **Blood Sugar Regulation**: A 15-minute post-meal walk significantly blunts glycemic spikes.\n\n"
                "💡 *Recommendation: Aim for at least 7,000 to 10,000 steps (or 30–45 mins of brisk walking) daily.*"
            )

        # 2. Calories burned running (30 minutes running)
        if any(w in lower for w in ["run", "running", "jog", "jogging", "દોડ", "દૌડ", "दौड़", "daud"]) and any(w in lower for w in ["calorie", "calories", "burn", "ketli", "kitni"]):
            # Extract duration if mentioned
            m = re.search(r"(\d+)\s*(?:min|minute|mins)", lower)
            mins = int(m.group(1)) if m else 30
            # MET of running is ~8.5. 70kg -> ~10 kcal per minute
            approx_cal = int(mins * 9.5)
            
            if is_guj:
                return (
                    f"🏃 **દોડવાથી બર્ન થતી કેલરી ({mins} મિનિટ Running)**:\n\n"
                    f"* **સરેરાશ કેલરી બર્ન**: {mins} મિનિટ દોડવાથી આશરે **{approx_cal - 30} થી {approx_cal + 50} કેલરી** બર્ન થાય છે (લગભગ 70 કિલો વજન ધરાવનાર વ્યક્તિ માટે).\n"
                    f"* **ઝડપ અનુસાર વિગત**:\n"
                    f"  * ધીમી જોગિંગ (8 km/h): ~{int(mins * 8.0)} kcal\n"
                    f"  * મધ્યમ ગતિ (10 km/h): ~{int(mins * 10.0)} kcal\n"
                    f"  * ઝડપી દોડ / સ્પ્રિન્ટ્સ (12+ km/h): ~{int(mins * 12.0)} kcal\n\n"
                    f"💡 *નોંધ: તમારા શરીરનું વજન, દોડવાની ઝડપ અને ઇન્ક્લાઇન મુજબ વાસ્તવિક કેલરીમાં થોડો ફેરફાર થઈ શકે છે.*"
                )
            if is_hi:
                return (
                    f"🏃 **दौड़ने से बर्न होने वाली कैलोरी ({mins} मिनट Running)**:\n\n"
                    f"* **औसत कैलोरी खर्च**: {mins} मिनट दौड़ने पर लगभग **{approx_cal - 30} से {approx_cal + 50} कैलोरी** बर्न होती है (70 किग्रा औसत वजन के लिए)।\n"
                    f"* **स्पीड के अनुसार विवरण**:\n"
                    f"  * धीमी जॉगिंग (8 किमी/घंटा): ~{int(mins * 8.0)} kcal\n"
                    f"  * मध्यम गति (10 किमी/घंटा): ~{int(mins * 10.0)} kcal\n"
                    f"  * तेज दौड़ (12+ किमी/घंटा): ~{int(mins * 12.0)} kcal\n\n"
                    f"💡 *टिप: दौड़ने से पहले 5 मिनट वार्म-अप और बाद में स्ट्रेचिंग जरूर करें!*"
                )
            return (
                f"🏃 **Calorie Burn for {mins} Minutes of Running**:\n\n"
                f"* **Estimated Total**: Approximately **{approx_cal - 30} to {approx_cal + 50} calories** for an average 70 kg (154 lbs) individual.\n"
                f"* **Breakdown by Pace**:\n"
                f"  * Light Jogging (8 km/h / 5 mph): ~{int(mins * 8.0)} kcal\n"
                f"  * Moderate Pace (10 km/h / 6.2 mph): ~{int(mins * 10.0)} kcal\n"
                f"  * Fast / Interval Running (12+ km/h / 7.5 mph): ~{int(mins * 12.0)} kcal\n\n"
                f"💡 *Key Factors: Body weight, running cadence, elevation, and metabolic rate influence exact expenditure.*"
            )

        # 3. Beginner Workout Plan
        if "workout plan" in lower or "routine plan" in lower or "beginner" in lower or ("plan" in lower and any(w in lower for w in ["workout", "exercise", "kasrat", "gym"])):
            if is_guj:
                return (
                    "🏋️ **બિગિનર વર્કઆઉટ પ્લાન (Beginner 3-Day Plan)**:\n\n"
                    "* **દિવસ 1 (Full Body Basics)**:\n"
                    "  * બોડીવેઇટ સ્ક્વોટ્સ (Squats): 3 સેટ × 12 રેપ્સ\n"
                    "  * પુશ-અપ્સ (Push-ups અથવા Knee Push-ups): 3 સેટ × 8–10 રેપ્સ\n"
                    "  * પ્લેન્ક (Plank): 3 સેટ × 20–30 સેકન્ડ\n"
                    "  * 15 મિનિટ બ્રિસ્ક વોક\n\n"
                    "* **દિવસ 2 (Active Recovery)**:\n"
                    "  * 30 મિનિટ લાઇટ વૉકિંગ અથવા હળવા યોગા અને સ્ટ્રેચિંગ\n\n"
                    "* **દિવસ 3 (Strength & Core)**:\n"
                    "  * લંજીસ (Lunges): 3 સેટ × 10 રેપ્સ (દરેક પગ)\n"
                    "  * ગ્લૂટ બ્રિજ (Glute Bridges): 3 સેટ × 12 રેપ્સ\n"
                    "  * માઉન્ટેન ક્લાઇમ્બર્સ: 3 સેટ × 15 રેપ્સ\n\n"
                    "💡 *નિયમ: કસરત શરૂ કરતા પહેલા 5 મિનિટ વોર્મઅપ અને પૂરતું પાણી પીવું જરૂરી છે.*"
                )
            if is_hi:
                return (
                    "🏋️ **शुरुआती लोगों के लिए वर्कआउट प्लान (Beginner 3-Day Plan)**:\n\n"
                    "* **दिन 1 (फुल बॉडी स्ट्रेंथ)**:\n"
                    "  * बॉडीवेट स्क्वैट्स (Squats): 3 सेट × 12 रेप्स\n"
                    "  * पुश-अप्स (Knee Push-ups): 3 सेट × 8–10 रेप्स\n"
                    "  * प्लैंक (Plank): 3 सेट × 30 सेकंड\n"
                    "  * 15 मिनट तेज चलना (Brisk Walk)\n\n"
                    "* **दिन 2 (एक्टिव रेस्ट)**:\n"
                    "  * 30 मिनट हल्की वॉक या स्ट्रेचिंग / योग\n\n"
                    "* **दिन 3 (लोअर बॉडी & कोर)**:\n"
                    "  * लंजेस (Lunges): 3 सेट × 10 रेप्स प्रति पैर\n"
                    "  * ग्लूट ब्रिज (Glute Bridges): 3 सेट × 12 रेप्स\n"
                    "  * क्रंचेस (Crunches): 3 सेट × 12 रेप्स\n\n"
                    "💡 *सलाह: फॉर्म पर ध्यान दें, धीरे-धीरे रेप्स और इंटेंसिटी बढ़ाएं!*"
                )
            return (
                "🏋️ **Beginner Full-Body Workout Plan (3-Day Split)**:\n\n"
                "* **Day 1: Full-Body Foundation**\n"
                "  * Bodyweight Squats: 3 sets × 12 reps\n"
                "  * Standard or Knee Push-ups: 3 sets × 8–10 reps\n"
                "  * Glute Bridges: 3 sets × 12 reps\n"
                "  * Forearm Plank: 3 sets × 30-second hold\n\n"
                "* **Day 2: Active Recovery**\n"
                "  * 30 minutes brisk walking or gentle mobility & yoga\n\n"
                "* **Day 3: Lower Body & Core**\n"
                "  * Reverse Lunges: 3 sets × 10 reps per leg\n"
                "  * Incline / Wall Push-ups: 3 sets × 12 reps\n"
                "  * Bird-Dog Exercise: 3 sets × 10 reps\n"
                "  * Bicycle Crunches: 3 sets × 15 reps\n\n"
                "💡 *Key Rule: Prioritize clean form over speed. Rest 60–90 seconds between sets.*"
            )

        # 4. Improve Stamina
        if "stamina" in lower or "endurance" in lower or any(w in lower for w in ["સ્ટેમિના", "स्टैमिना", "दम"]):
            if is_guj:
                return (
                    "⚡ **સ્ટેમિના વધારવાના શ્રેષ્ઠ ઉપાયો (How to Improve Stamina)**:\n\n"
                    "* **પ્રોગ્રેસિવ કાર્ડિયો (Progressive Aerobic Exercise)**: અઠવાડિયે 4–5 દિવસ રનિંગ, સાયકલિંગ અથવા સ્વિમિંગ કરો. દર અઠવાડિયે સમય 10% વધારો.\n"
                    "* **HIIT (ઇન્ટરવલ ટ્રેનિંગ)**: 1 મિનિટ ઝડપી દોડવું અને 2 મિનિટ ચાલવું. આ રીતે 20 મિનિટ ટ્રેનિંગ કરવાથી ફેફસાંની ક્ષમતા વધે છે.\n"
                    "* **સ્ટ્રેન્થ ટ્રેનિંગ**: સ્ક્વોટ્સ, પુશઅપ્સ અને પ્લેન્ક જેવા વ્યાયામથી સ્નાયુઓની સહનશક્તિ વધે છે.\n"
                    "* **યોગ્ય આહાર & હાઇડ્રેશન**: વર્કઆઉટના 1 કલાક પહેલા કેળા અથવા ઓટ્સ જેવા જટિલ કાર્બોહાઇડ્રેટ લો અને દિવસમાં 2.5–3 લીટર પાણી પીવો.\n"
                    "* **ઊંઘ & રિકવરી**: શરીરને દરરોજ રાત્રે 7–8 કલાકની ગાઢ ઊંઘ આપો જેથી મસલ્સ રિકવર થાય.\n\n"
                    "💡 *ધ્યાન રાખો: સ્ટેમિના 2–3 અઠવાડિયાના સતત પ્રયાસથી નોંધપાત્ર રીતે વધે છે!*"
                )
            if is_hi:
                return (
                    "⚡ **स्टैमिना और एनर्जी बढ़ाने के 5 असरदार तरीके**:\n\n"
                    "* **प्रोग्रेसिव कार्डियो**: रनिंग, साइकलिंग या रस्सी कूदना शुरू करें और हर हफ्ते 10% समय बढ़ाएं।\n"
                    "* **हाई-इंटेंसिटी इंटरवल ट्रेनिंग (HIIT)**: 1 मिनट तेज स्प्रिंट और 2 मिनट वॉक। इससे फेफड़ों और दिल की क्षमता बढ़ती है।\n"
                    "* **स्ट्रेंथ ट्रेनिंग शामिल करें**: हफ्ते में 3 दिन बॉडीवेट स्क्वैट्स, पुश-अप्स और कोर वर्कआउट करें।\n"
                    "* **पोषण और पानी**: वर्कआउट से पहले केला या ओट्स लें, प्रोटीन भरपूर खाएं और रोजाना 3 लीटर पानी पिएं।\n"
                    "* **पर्याप्त नींद**: 7–8 घंटे की गहरी नींद मसल्स रिपेयर और स्टेमिना के लिए अनिवार्य है।\n\n"
                    "💡 *नियमितता ही सफलता की कुंजी है — 3 हफ्ते में आपको खुद फर्क दिखेगा!*"
                )
            return (
                "⚡ **How to Effectively Build and Improve Stamina**:\n\n"
                "* **1. Progressive Overload in Cardio**: Gradually increase your workout duration or pace by ~10% each week (running, cycling, swimming, or brisk walking).\n"
                "* **2. High-Intensity Interval Training (HIIT)**: Alternate between 30–60 seconds of max effort and 60–90 seconds of active recovery for 20 minutes.\n"
                "* **3. Compound Strength Exercises**: Integrate squats, lunges, and push-ups to condition muscular endurance alongside cardiovascular capacity.\n"
                "* **4. Optimize Hydration & Nutrition**: Consume complex carbs before workouts, adequate electrolytes, and balanced protein for recovery.\n"
                "* **5. Quality Rest & Breathing**: Practice diaphragmatic breathing during aerobic exercise and ensure 7–8 hours of consistent sleep nightly.\n\n"
                "💡 *Consistency matters most: 4–5 targeted sessions per week yield noticeable improvements within 2 to 3 weeks.*"
            )

        # 5. Exercises for Legs
        if "leg" in lower or "legs" in lower or any(w in lower for w in ["પગ", "પગની", "पैर", "पैरों"]):
            if is_guj:
                return (
                    "🦵 **પગના સ્નાયુઓ મજબૂત કરવા માટે શ્રેષ્ઠ કસરતો (Exercises for Legs)**:\n\n"
                    "* **સ્ક્વોટ્સ (Squats)**: જાંઘ (Quads) અને નિતંબ (Glutes) માટે શ્રેષ્ઠ વ્યાયામ (3 સેટ × 12–15 રેપ્સ).\n"
                    "* **લંજીસ (Walking / Reverse Lunges)**: દરેક પગનું સંતુલન અને શક્તિ વધારે છે (3 સેટ × 10 રેપ્સ પ્રતિ પગ).\n"
                    "* **ગ્લૂટ બ્રિજ (Glute Bridges)**: હિપ્સ અને હેમસ્ટ્રિંગ્સ માટે અત્યંત અસરકારક (3 સેટ × 15 રેપ્સ).\n"
                    "* **કાફ રેઇઝીસ (Calf Raises)**: પિંડીઓના સ્નાયુઓ (Calves) મજબૂત કરવા માટે (3 સેટ × 20 રેપ્સ).\n"
                    "* **વોલ સીટ (Wall Sit)**: જાંઘના સ્નાયુઓની સહનશક્તિ વધારવા 45 સેકન્ડ હોલ્ડ કરો.\n\n"
                    "💡 *ટિપ: યોગ્ય ફોર્મ જાળવો — સ્ક્વોટ કરતી વખતે ઘૂંટણ પંજાની આગળ ન જાય તેનું ધ્યાન રાખો.*"
                )
            if is_hi:
                return (
                    "🦵 **पैरों (Legs) को मजबूत और टोंड करने की बेहतरीन एक्सरसाइज**:\n\n"
                    "* **स्क्वैट्स (Squats)**: जांघों (Quads) और हिप्स के लिए सबसे असरदार बुनियादी एक्सरसाइज (3 सेट × 12–15 रेप्स)।\n"
                    "* **लंजेस (Lunges)**: दोनों पैरों का संतुलन और ताकत बढ़ाने के लिए (3 सेट × 10 रेप्स प्रति पैर)।\n"
                    "* **ग्लूट ब्रिज (Glute Bridges)**: हैमस्ट्रिंग्स और ग्लूट्स को टोन करने के लिए (3 सेट × 15 रेप्स)।\n"
                    "* **काफ रेज (Calf Raises)**: पिंडलियों (Calves) को मजबूत बनाने के लिए (3 सेट × 20 रेप्स)।\n"
                    "* **वॉल सिट (Wall Sit)**: जांघों की ताकत और एंड्योरेंस के लिए 30–45 सेकंड होल्ड करें।\n\n"
                    "💡 *सलाह: वार्म-अप के बाद करें और घुटनों को पंजों की सीध में रखें।* "
                )
            return (
                "🦵 **Top Exercises Targeting the Legs**:\n\n"
                "* **Quadriceps & Glutes**:\n"
                "  * **Bodyweight or Goblet Squats**: 3 sets × 12–15 reps (primary mass & power builder).\n"
                "  * **Walking Lunges**: 3 sets × 10 reps per leg (unilateral strength & stability).\n"
                "  * **Wall Sits**: 3 sets × 30–45 sec hold (isometric endurance).\n\n"
                "* **Hamstrings & Posterior Chain**:\n"
                "  * **Romanian Deadlifts (RDLs)**: 3 sets × 10–12 reps (targets hamstrings & lower back).\n"
                "  * **Glute Bridges / Hip Thrusts**: 3 sets × 15 reps (glute activation and hip extension).\n\n"
                "* **Calves**:\n"
                "  * **Standing Calf Raises**: 3 sets × 20 reps (strengthens lower legs & ankles).\n\n"
                "💡 *Form Tip: Keep chest proud, core engaged, and track your knees in line with your toes.*"
            )

        # Generic Fitness / Workout Question Fallback
        return (
            "💪 **Fitness & Workout Guidance**:\n\n"
            "* For optimal fitness, combine **aerobic cardio** (e.g. 150 mins weekly of brisk walking, jogging, or cycling) with **resistance training** (2–3 full-body sessions weekly).\n"
            "* Always begin with a 5-minute dynamic warm-up and end with static stretching.\n"
            "* Fuel your workouts with adequate protein, hydration, and 7–8 hours of restorative sleep.\n\n"
            "Tell me your specific fitness goal (weight loss, muscle gain, stamina, or home workouts) and I can tailor a custom plan for you!"
        )

    @staticmethod
    def is_workout_suggestion_query(text: str) -> bool:
        lower = text.lower()
        triggers = [
            "suggest exercise", "suggest workout", "suggest an exercise", "suggest a workout",
            "what exercise should i do", "what workout should i do", "exercise suggestions",
            "workout suggestions", "give me exercise", "give me workout", "recommend exercise",
            "recommend workout", "which exercise should i do", "exercise suggest karo",
            "workout suggest karo", "kai exercise karu", "kai kasrat karu", "kasrat suggest karo",
            "koi exercise batao", "koi workout batao", "aaj kaunsa workout", "aaje kai kasrat",
            "કઈ કસરત કરું", "કસરત સજેસ્ટ", "વર્કઆઉટ સજેસ્ટ", "કોઈ કસરત બતાવો",
            "कौन सी एक्सरसाइज करूं", "एक्सरसाइज सजेस्ट करो", "वर्कआउट सजेस्ट करो", "कोई एक्सरसाइज बताओ"
        ]
        return any(t in lower for t in triggers)

    @staticmethod
    def generate_workout_suggestion_response(
        text: str,
        lang: str = "en",
        logged_activities_summary: Optional[str] = None
    ) -> str:
        lower = text.lower()
        has_guj = any('\u0A80' <= ch <= '\u0AFF' for ch in text) or bool(re.search(r"\b(?:shu|kem|chhe|mate|aapo|kaya|kasrat|karyu|aaje)\b", lower))
        has_hi = any('\u0900' <= ch <= '\u097F' for ch in text) or bool(re.search(r"\b(?:kya|kaise|hai|hain|ke\s+liye|batao|kaunse|karein|aaj)\b", lower))
        is_guj = (lang in ["gu", "gu-Latn"] or has_guj) and not (lang == "en" and not has_guj)
        is_hi = (lang in ["hi", "hi-Latn"] or has_hi) and not (lang == "en" and not has_hi)

        context_note_guj = f"\n* આજની સ્થિતિ: {logged_activities_summary}\n" if logged_activities_summary else ""
        context_note_hi = f"\n* आज की स्थिति: {logged_activities_summary}\n" if logged_activities_summary else ""
        context_note_en = f"\n* Today's Logged Activity: {logged_activities_summary}\n" if logged_activities_summary else ""

        if is_guj:
            return (
                "🏃 **તમારા માટે ઉત્તમ કસરત વિકલ્પો (Exercise Suggestions)**:"
                f"{context_note_guj}\n"
                "* **1. બ્રિસ્ક વૉકિંગ (Brisk Walking)**\n"
                "  * સૂચવેલ સમય: **30 મિનિટ**\n"
                "  * અંદાજિત કેલરી બર્ન: ~**120–150 kcal**\n"
                "  * લાભ: હૃદય માટે સુરક્ષિત, સાંધા પર દબાણ વગર કેલરી બર્ન કરે છે.\n\n"
                "* **2. બોડીવેઇટ સ્ક્વોટ્સ & લંજીસ (Squats & Lunges)**\n"
                "  * સૂચવેલ સેટ્સ: **3 સેટ × 12–15 રેપ્સ** (~15 મિનિટ)\n"
                "  * અંદાજિત કેલરી બર્ન: ~**70–90 kcal**\n"
                "  * લાભ: પગ અને હિપ્સના સ્નાયુઓ મજબૂત થાય છે, મેટાબોલિઝમ ઝડપી બને છે.\n\n"
                "* **3. લાઇટ કાર્ડિયો / જમ્પિંગ જેક્સ & સ્કીપિંગ (Jumping Jacks)**\n"
                "  * સૂચવેલ સમય: **15 મિનિટ**\n"
                "  * અંદાજિત કેલરી બર્ન: ~**100–120 kcal**\n"
                "  * લાભ: ઝડપથી સ્ટેમિના અને હાર્ટ રેટ વધારે છે.\n\n"
                "* **4. સૂર્ય નમસ્કાર / યોગાસન (Surya Namaskar)**\n"
                "  * સૂચવેલ રાઉન્ડ્સ: **10–12 રાઉન્ડ** (~20 મિનિટ)\n"
                "  * અંદાજિત કેલરી બર્ન: ~**80–100 kcal**\n"
                "  * લાભ: સંપૂર્ણ શરીરનું સ્ટ્રેચિંગ, ફ્લેક્સિબિલિટી અને માનસિક શાંતિ.\n\n"
                "⚠️ *નોંધ: દર્શાવેલ બર્ન થયેલી કેલરી અંદાજિત (estimates) છે. વાસ્તવિક કેલરી તમારા શરીરના વજન, ઝડપ અને પ્રયાસ પર આધાર રાખે છે.*"
            )
        elif is_hi:
            return (
                "🏃 **आपके लिए बेहतरीन एक्सरसाइज सुझाव (Exercise Suggestions)**:"
                f"{context_note_hi}\n"
                "* **1. तेज चलना / ब्रिस्क वॉक (Brisk Walking)**\n"
                "  * सुझाई गई अवधि: **30 मिनट**\n"
                "  * अनुमानित कैलोरी बर्न: ~**120–150 kcal**\n"
                "  * लाभ: दिल के लिए सुरक्षित, जोड़ों पर दबाव डाले बिना फैट बर्न करता है।\n\n"
                "* **2. बॉडीवेट स्क्वैट्स और लंजेस (Squats & Lunges)**\n"
                "  * सुझाई गई मात्रा: **3 सेट × 12–15 रेप्स** (~15 मिनट)\n"
                "  * अनुमानित कैलोरी बर्न: ~**70–90 kcal**\n"
                "  * लाभ: पैरों और कोर की मांसपेशियों को मजबूती देता है, मेटाबॉलिज्म बढ़ाता है।\n\n"
                "* **3. जंपिंग जैक्स और स्किपिंग (Jumping Jacks / Skip Rope)**\n"
                "  * सुझाई गई अवधि: **15 मिनट**\n"
                "  * अनुमानित कैलोरी बर्न: ~**100–120 kcal**\n"
                "  * लाभ: स्टैमिना बढ़ाता है और कम समय में अधिक कैलोरी खर्च करता है।\n\n"
                "* **4. सूर्य नमस्कार और योग (Surya Namaskar & Yoga)**\n"
                "  * सुझाई गई मात्रा: **10–12 राउंड** (~20 मिनट)\n"
                "  * अनुमानित कैलोरी बर्न: ~**80–100 kcal**\n"
                "  * लाभ: पूरे शरीर का लचीलापन, रीढ़ की मजबूती और मानसिक शांति।\n\n"
                "⚠️ *नोट: दी गई कैलोरी बर्न संख्या अनुमानित (estimates) है। वास्तविक कैलोरी आपके वजन, इंटेंसिटी और गति पर निर्भर करती है।* "
            )
        else:
            return (
                "🏃 **Recommended Workout & Exercise Suggestions**:"
                f"{context_note_en}\n"
                "* **1. Brisk Walking / Moderate Cardio**\n"
                "  * Suggested Duration: **30 minutes**\n"
                "  * Estimated Calorie Burn: ~**120–150 kcal**\n"
                "  * Benefits: Low-impact aerobic baseline that boosts cardiovascular health without joint strain.\n\n"
                "* **2. Bodyweight Squats & Reverse Lunges**\n"
                "  * Suggested Volume: **3 sets × 12–15 reps** (~15 minutes)\n"
                "  * Estimated Calorie Burn: ~**70–90 kcal**\n"
                "  * Benefits: Activates major lower-body muscle groups and stimulates metabolic rate.\n\n"
                "* **3. High-Intensity Interval Cardio (Jumping Jacks / Jump Rope)**\n"
                "  * Suggested Duration: **15 minutes** (work:rest ratio 30s:30s)\n"
                "  * Estimated Calorie Burn: ~**100–120 kcal**\n"
                "  * Benefits: Rapid stamina development and efficient calorie expenditure in short time.\n\n"
                "* **4. Surya Namaskar (Sun Salutations) / Flow Yoga**\n"
                "  * Suggested Volume: **10–12 rounds** (~20 minutes)\n"
                "  * Estimated Calorie Burn: ~**80–100 kcal**\n"
                "  * Benefits: Full-body mobility, core stabilization, and active recovery.\n\n"
                "⚠️ *Note: Calorie expenditure values are estimates based on standard MET averages. Individual results vary with body weight, pace, and intensity.*"
            )
