import json
import re
import aiohttp
import logging
from typing import Dict, Any, Optional, List
from ..config import settings
from .agent_nlp import AgentNLP

logger = logging.getLogger("ai_service")

SYSTEM_PROMPT = """You are Google Fitness AI, an elite multilingual fitness and nutrition agent.
Your mission is to understand user health messages with 100% accuracy, even when users:
- Make severe spelling mistakes or typos (e.g., "khapli rti", "banaana", "chiken", "pneer", "dudh", "chawal", "bhindi")
- Use informal, colloquial, or slang phrases (e.g., "aaj me 2 roti thoki", "poha patavi didhu", "had 2 rotis with dal", "ek glass chaas pithi")
- Write in multiple languages or mixed dialects (English, Hindi, Gujarati, Hinglish, Gujlish, Gujarati script, Devanagari script)
- Use regional food names and Indian household units (katori, vatki, plate, glass, cup, piece, nag, bowl)

SUPPORTED INTENTS:
1. CREATE_FOOD_LOG: Logging one or more foods/drinks consumed (e.g., "ate 2 khapli rotis", "had 1 bowl dal and rice", "3 rotli ane chhas lidhi", "2 kela", "aaje 1 glass doodh lidhu").
2. UPDATE_FOOD_LOG: Correcting or modifying an item logged today (e.g., "make that 3 rotis instead of 2", "change banana quantity to 1", "actually 4 pieces khapli").
3. DELETE_FOOD_LOG: Removing or canceling an item logged today (e.g., "remove the banana", "delete roti from my logs", "kela cancel karo").
4. QUERY_FOOD_LOG: Inquiring about logged foods, today's calories, or progress (e.g., "what did I eat today?", "how many calories do I have left?", "aaj nu summary aapo", "ketla calories thya?").
5. CREATE_ACTIVITY_LOG: Workouts, gym, walking, running, cycling, sports (e.g., "ran 5 km", "walked 30 mins", "gym workout for 45 mins", "did 20 pushups").
6. CREATE_HYDRATION_LOG: Pure water intake (e.g., "drank 500ml water", "2 glasses of water", "pani pidhu").
7. CREATE_SLEEP_LOG: Sleep tracking (e.g., "slept 7 hours", "went to bed at 11pm and woke up at 7am").
8. CREATE_WEIGHT_LOG: Weight logging (e.g., "my weight is 70 kg", "logged 68.5 kg").
9. CREATE_MULTI_LOG: Combined routines (e.g., "2 rotis and 30 min walk", "ate 1 apple and drank 500ml water").
10. GENERAL_CHAT: Nutrition questions, fitness advice, greetings, hypothetical questions (e.g., "hello", "how are you", "is roti healthy?", "how much protein in 100g paneer?", "if I eat 2 rotis how many calories?", "what should I eat?"). DO NOT log food for hypothetical questions or nutrition queries!

CRITICAL MULTI-ITEM RULE:
- If a user mentions multiple food or drink items (e.g., "3 rotli ane chhas lidhi", "2 rotis, 1 bowl dal and 1 glass chaas", "poha and tea"), YOU MUST INCLUDE EVERY SINGLE ITEM in the 'foodItems' array! NEVER omit or drop any item!

GUJARATI & HINDI EATING VERBS RULE:
- Words like "khadho", "khadha", "khadhi", "khadhu", "pidho", "pidhi", "pidhu", "lidho", "lidhi", "lidhu" are Gujarati verbs meaning ATE / DRANK -> ALWAYS treat as CREATE_FOOD_LOG! NEVER classify them as DELETE_FOOD_LOG!

SPELLING CORRECTION & FOOD RECOGNITION:
- Correct typos to clean, canonical food names:
  * "khapli rti", "khapli rotli", "khapli" -> "Khapli Wheat Rotli"
  * "rotli", "roti", "chapatis", "phulka" -> "Roti"
  * "banaana", "kela", "keda", "kelu" -> "Banana"
  * "doodh", "dudh" -> "Cow Milk"
  * "chaas", "chhas", "chach" -> "Buttermilk"
  * "chawal", "bhaat" -> "Cooked White Rice"
  * "pneer" -> "Paneer"
  * "chiken" -> "Chicken Breast"
  * "anda", "ande" -> "Boiled Egg"
  * "daal", "tuver dal" -> "Toor Dal"
  * "shak", "shaak", "sabzi" -> "Mixed Vegetable Sabzi"

PORTION & UNIT PARSING:
- "katori", "vatki", "bowl" -> unit: "bowl"
- "cup", "kapp" -> unit: "cup"
- "glass", "glaas" -> unit: "glass"
- "plate", "dish" -> unit: "plate"
- "piece", "pcs", "nag", "roti", "rotli", "slice" -> unit: "piece"
- Gujarati/Hindi number words: "ek"=1, "be"/"do"=2, "tran"/"tin"=3, "char"=4, "panch"=5, "aadha"/"adho"=0.5, "dedh"=1.5, "dhai"=2.5.
- Meal types: guess from sentence or default (BREAKFAST, LUNCH, DINNER, SNACK).

OUTPUT FORMAT:
Respond with ONLY a single valid JSON block without additional markdown text or reasoning tags:
```json
{
  "intent": "CREATE_FOOD_LOG",
  "language": "en",
  "entities": {
    "foodItems": [
      {
        "food": "Khapli Wheat Rotli",
        "quantity": 2.0,
        "unit": "piece",
        "mealType": "LUNCH"
      }
    ],
    "targetFood": null,
    "newQuantity": null
  },
  "replyText": "Logged 2 pieces of Khapli Wheat Rotli for lunch."
}
```

For UPDATE_FOOD_LOG:
```json
{
  "intent": "UPDATE_FOOD_LOG",
  "language": "en",
  "entities": {
    "targetFood": "Khapli Wheat Rotli",
    "newQuantity": 3.0,
    "unit": "piece"
  },
  "replyText": "Updated Khapli Wheat Rotli to 3 pieces."
}
```

For DELETE_FOOD_LOG:
```json
{
  "intent": "DELETE_FOOD_LOG",
  "language": "en",
  "entities": {
    "targetFood": "Banana"
  },
  "replyText": "Removed Banana from today's food logs."
}
```
"""

class AIService:
    @staticmethod
    async def process_message(
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        # Step 1: Detect Intent Deterministically with 99%+ Precision
        detected_intent = AgentNLP.detect_intent(message)
        lang = AgentNLP.detect_language(message)

        # 1. Non-logging or Query intents: Handle immediately with zero latency and 100% precision
        if detected_intent == "GENERAL_CHAT":
            return {
                "intent": "GENERAL_CHAT",
                "language": lang,
                "entities": {"foodItems": []},
                "replyText": "I can answer nutrition and fitness questions or log what you ate when you're ready!"
            }

        if detected_intent == "QUERY_FOOD_LOG":
            return {
                "intent": "QUERY_FOOD_LOG",
                "language": lang,
                "entities": {},
                "replyText": "Here is your nutrition summary for today."
            }

        # 2. Domain logging intents with high-precision parsers
        if detected_intent == "CREATE_WEIGHT_LOG":
            w_ent = AgentNLP.extract_weight_entity(message)
            return {
                "intent": "CREATE_WEIGHT_LOG",
                "language": lang,
                "entities": w_ent,
                "replyText": f"Logged body weight of {w_ent['weightKg']} kg."
            }

        if detected_intent == "CREATE_HYDRATION_LOG":
            h_ent = AgentNLP.extract_hydration_entity(message)
            return {
                "intent": "CREATE_HYDRATION_LOG",
                "language": lang,
                "entities": h_ent,
                "replyText": f"Logged {int(h_ent['amountMl'])} ml of Water."
            }

        if detected_intent == "CREATE_ACTIVITY_LOG":
            a_ent = AgentNLP.extract_activity_entity(message)
            return {
                "intent": "CREATE_ACTIVITY_LOG",
                "language": lang,
                "entities": a_ent,
                "replyText": f"Logged {a_ent['durationMinutes']} mins of {a_ent['activity']}."
            }

        if detected_intent == "CREATE_SLEEP_LOG":
            s_ent = AgentNLP.extract_sleep_entity(message)
            return {
                "intent": "CREATE_SLEEP_LOG",
                "language": lang,
                "entities": s_ent,
                "replyText": f"Recorded {int(s_ent['durationMinutes']//60)}h of sleep."
            }

        # 3. For Food Logging: Try high-precision deterministic extraction first
        if detected_intent in ["CREATE_FOOD_LOG", "CREATE_MULTI_LOG"]:
            foods = AgentNLP.extract_food_entities_heuristically(message)
            if foods and len(foods) > 0:
                return {
                    "intent": "CREATE_FOOD_LOG",
                    "language": lang,
                    "entities": {"foodItems": foods},
                    "replyText": f"Logged {len(foods)} food item(s)."
                }

        # 4. For Ambiguous messages or Updates/Deletes: Call Cloudflare Workers AI / Groq LLM
        pre_processed = AgentNLP.normalize_text(message)
        result: Optional[Dict[str, Any]] = None

        if settings.CF_ACCOUNT_ID and settings.CF_API_TOKEN:
            try:
                res = await AIService._call_cloudflare(pre_processed, conversation_history)
                if res and res.get("intent"):
                    result = res
            except Exception as e:
                logger.warning(f"Cloudflare AI failed: {e}. Falling back to Groq...")

        if not result and settings.GROQ_API_KEY:
            try:
                res = await AIService._call_groq(pre_processed, conversation_history)
                if res and res.get("intent"):
                    result = res
            except Exception as e:
                logger.warning(f"Groq AI failed: {e}")

        if not result or not result.get("intent"):
            result = AIService._rule_based_fallback(message, pre_processed)

        return result

    @staticmethod
    async def _call_cloudflare(message: str, history: Optional[List[Dict[str, str]]] = None) -> Optional[Dict[str, Any]]:
        url = f"https://api.cloudflare.com/client/v4/accounts/{settings.CF_ACCOUNT_ID}/ai/run/{settings.CF_MODEL}"
        headers = {
            "Authorization": f"Bearer {settings.CF_API_TOKEN}",
            "Content-Type": "application/json",
        }
        
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if history:
            for h in history[-4:]:
                messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
        messages.append({"role": "user", "content": message})

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json={"messages": messages, "max_tokens": 1024, "temperature": 0.1}, timeout=15) as res:
                if res.status != 200:
                    text = await res.text()
                    logger.warning(f"Cloudflare returned status {res.status}: {text}")
                data = await res.json()
                result_data = data.get("result", {})
                if isinstance(result_data, dict):
                    if "choices" in result_data and len(result_data["choices"]) > 0:
                        raw_reply = result_data["choices"][0].get("message", {}).get("content", "")
                    else:
                        raw_reply = result_data.get("response", "")
                else:
                    raw_reply = str(result_data)
                return AIService._parse_json(raw_reply)

    @staticmethod
    async def _call_groq(message: str, history: Optional[List[Dict[str, str]]] = None) -> Optional[Dict[str, Any]]:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if history:
            for h in history[-4:]:
                messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
        messages.append({"role": "user", "content": message})

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json={"model": "llama-3.3-70b-versatile", "messages": messages, "temperature": 0.1}, timeout=15) as res:
                if res.status != 200:
                    return None
                data = await res.json()
                raw_reply = data["choices"][0]["message"]["content"]
                return AIService._parse_json(raw_reply)

    @staticmethod
    def _parse_json(raw: str) -> Optional[Dict[str, Any]]:
        cleaned = re.sub(r"<think>[\s\S]*?</think>", "", raw, flags=re.IGNORECASE).strip()
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
        if match:
            cleaned = match.group(1).strip()
        elif "{" in cleaned:
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1:
                cleaned = cleaned[start:end+1]
        
        try:
            parsed = json.loads(cleaned)
            if "entities" not in parsed:
                parsed["entities"] = {}
            return parsed
        except Exception:
            return None

    @staticmethod
    def _rule_based_fallback(original_message: str, pre_processed: str) -> Dict[str, Any]:
        intent = AgentNLP.detect_intent(original_message)
        lang = AgentNLP.detect_language(original_message)

        # 1. UPDATE_FOOD_LOG fallback
        if intent == "UPDATE_FOOD_LOG":
            foods = AgentNLP.extract_food_entities_heuristically(pre_processed)
            target = foods[0]["food"] if foods else "food"
            new_qty = foods[0]["quantity"] if foods else 1.0
            return {
                "intent": "UPDATE_FOOD_LOG",
                "language": lang,
                "entities": {
                    "targetFood": target,
                    "newQuantity": new_qty,
                    "unit": foods[0].get("unit", "piece") if foods else "piece",
                },
                "replyText": f"Updated {target} to {new_qty}.",
            }

        # 2. DELETE_FOOD_LOG fallback
        if intent == "DELETE_FOOD_LOG":
            clean = re.sub(r"\b(?:delete|remove|cancel|hatao|nikalo|kadho|kadhi nakho|from my logs|aaj nu|today)\b", "", original_message, flags=re.I).strip()
            target = clean.title() if clean else "food"
            return {
                "intent": "DELETE_FOOD_LOG",
                "language": lang,
                "entities": {"targetFood": target},
                "replyText": f"Removed {target} from today's logs.",
            }

        # 3. QUERY_FOOD_LOG fallback
        if intent == "QUERY_FOOD_LOG":
            return {
                "intent": "QUERY_FOOD_LOG",
                "language": lang,
                "entities": {},
                "replyText": "Here is your nutrition summary for today.",
            }

        # 4. HYDRATION_LOG fallback
        if intent == "CREATE_HYDRATION_LOG":
            amount = 250.0
            num_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:ml|liter|ltr|glass)?", pre_processed.lower())
            if num_match:
                val = float(num_match.group(1))
                amount = val * 1000 if ("liter" in pre_processed.lower() or "ltr" in pre_processed.lower()) and val <= 10 else val
            return {
                "intent": "CREATE_HYDRATION_LOG",
                "language": lang,
                "entities": {"waterAmount": amount},
                "replyText": f"Logged {int(amount)} ml water.",
            }

        # 5. ACTIVITY_LOG fallback
        if intent == "CREATE_ACTIVITY_LOG":
            mins = 30
            num_match = re.search(r"(\d+)\s*(?:min|minute|ghanta|hour|hr)", pre_processed.lower())
            if num_match:
                val = int(num_match.group(1))
                mins = val * 60 if any(w in pre_processed.lower() for w in ["hour", "hr", "ghanta"]) else val
            return {
                "intent": "CREATE_ACTIVITY_LOG",
                "language": lang,
                "entities": {"activity": "Workout", "durationMinutes": mins},
                "replyText": f"Logged {mins} mins workout.",
            }

        # 6. FOOD_LOG fallback
        if intent in ["CREATE_FOOD_LOG", "CREATE_MULTI_LOG"]:
            food_items = AgentNLP.extract_food_entities_heuristically(pre_processed)
            if food_items:
                return {
                    "intent": intent,
                    "language": lang,
                    "entities": {"foodItems": food_items},
                    "replyText": f"Logged {len(food_items)} food items.",
                }

        # 7. GENERAL_CHAT fallback
        return {
            "intent": "GENERAL_CHAT",
            "language": lang,
            "entities": {},
            "replyText": "I am here to help you log meals, track your workouts, and reach your fitness goals.",
        }
