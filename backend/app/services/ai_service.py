import json
import re
import asyncio
import aiohttp
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from ..config import settings
from .agent_nlp import AgentNLP
from .fitness_advisory_service import FitnessAdvisoryService

logger = logging.getLogger("ai_service")

# ---------------------------------------------------------------------------
# FitBot system prompt — loaded once at import time from the prompts file.
# The file content can be swapped without code changes.
# ---------------------------------------------------------------------------
_PROMPT_FILE = Path(__file__).parent.parent.parent / "prompts" / "fitbot_system_prompt.txt"

def _load_fitbot_system_prompt() -> str:
    """Load the FitBot system prompt from disk, falling back to an inline stub."""
    try:
        text = _PROMPT_FILE.read_text(encoding="utf-8").strip()
        logger.info("FitBot system prompt loaded: %d characters from %s", len(text), _PROMPT_FILE)
        return text
    except Exception as exc:
        logger.warning("Could not load fitbot_system_prompt.txt (%s); using inline stub.", exc)
        return (
            "You are FitBot, a precise fitness assistant. "
            "Help users log food and exercise. Never invent kcal values."
        )

FITBOT_SYSTEM_PROMPT: str = _load_fitbot_system_prompt()

# Keep legacy name so any existing internal references still work
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

TEMPORAL / DATE CONTEXT RULE (CRITICAL — affects which date a log belongs to):
- PAST actions are completed logs. Resolve to the correct past date (Asia/Kolkata), NOT today.
  * Past markers: "yesterday", "kal maine ... khaya/kiya", "kale ... khadhi/kari" (with PAST verb), "gaya kale", "gai kale", "ગઈકાલે", "कल खाया". Example: "kal maine 2 roti khadhi" -> CREATE_FOOD_LOG dated YESTERDAY.
- FUTURE / PLANNED actions must NOT be logged as completed.
  * Future markers (verb conjugations): "khaysh", "khaish", "karish", "karis", "jaish", "piysh", "khaunga", "karunga", "jaunga", "will eat", "will do", "will go", "aavti kale", "આવતીકાલે", "कल करूंगा". Example: "kale hu gym karish" -> this is a PLAN, do NOT create an activity log.
  * For a future/planned statement, respond with intent "GENERAL_CHAT" and a replyText that acknowledges the plan without logging it.
- The word "kal"/"kale" alone is ambiguous. Decide PAST vs FUTURE from the verb tense in the same sentence. Do NOT assume "kal/kale" always means past.
- SUGGESTION QUESTIONS are never logs. "kale su khavu joiye?", "mare kale su exercise karvi?", "sanje su khavu?", "what should I eat tomorrow?" -> GENERAL_CHAT (suggestion), create NO log.
- Present/today actions (no date word, or "aaj"/"aaje"/"today") -> log on TODAY.

SPELLING CORRECTION & FOOD RECOGNITION:
- Correct typos to clean, canonical food names:
  * "protein shake", "protein drink" -> "Protein Shake"
  * "protein powder", "whey", "whey protein" -> "Whey Protein Powder"
  * "khapli rti", "khapli rotli", "khapli" -> "Khapli Wheat Rotli"
  * "rotli", "roti", "rotis", "rotlis" -> "Roti"
  * "chapati", "chapatis" -> "Chapati"
  * "phulka", "phulke" -> "Phulka"
  * "thepla", "theplas" -> "Methi Thepla"
  * "banaana", "kela", "keda", "kelu" -> "Banana"
  * "doodh", "dudh" -> "Cow Milk (Toned)"
  * "chaas", "chhas", "chach" -> "Spiced Buttermilk (Chaas)"
  * "chawal", "bhaat" -> "Cooked White Rice"
  * "pneer" -> "Paneer"
  * "chiken" -> "Chicken Breast"
  * "anda", "ande" -> "Boiled Egg"
  * "daal", "tuver dal" -> "Toor Dal"
  * "shak", "shaak", "sabzi" (vegetable curries only, NOT shakes) -> "Mixed Vegetable Sabzi"
  * If a food is completely unknown, DO NOT invent or guess random foods from the database.

PORTION & UNIT PARSING:
- "katori", "vatki", "bowl" -> unit: "bowl"
- "cup", "kapp" -> unit: "cup"
- "glass", "glaas" -> unit: "glass"
- "plate", "dish" -> unit: "plate"
- "scoop", "skup" -> unit: "scoop"
- "spoon", "chamach", "chamchi", "चम्मच", "ચમચી", "tablespoon", "tbsp" -> unit: "tbsp"
- "teaspoon", "tsp" -> unit: "tsp"
- "piece", "pcs", "nag", "roti", "rotli", "thepla", "slice" -> unit: "piece"
- Gujarati/Hindi number words: "ek"=1, "be"/"do"=2, "tran"/"tin"=3, "char"=4, "panch"=5, "aadha"/"adho"=0.5, "dedh"=1.5, "dhai"=2.5.
- Meal types: Only set mealType if user explicitly specifies meal/time context (BREAKFAST, LUNCH, DINNER, SNACK). If not specified by user, mealType MUST be "—". Never guess or use clock.

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
        "mealType": "—"
      }
    ],
    "targetFood": null,
    "newQuantity": null
  },
  "replyText": "Logged 2 pieces of Khapli Wheat Rotli."
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

For CREATE_MULTI_LOG (multiple foods, workouts, and/or water):
```json
{
  "intent": "CREATE_MULTI_LOG",
  "language": "en",
  "entities": {
    "foodItems": [
      {"food": "Khapli Wheat Rotli", "quantity": 3.0, "unit": "piece"},
      {"food": "Cow Milk (Toned)", "quantity": 1.0, "unit": "cup"}
    ],
    "activities": [
      {"activity": "Gym workout", "durationMinutes": 60.0},
      {"activity": "Walking", "durationMinutes": 20.0}
    ],
    "hydrationItems": [
      {"beverageName": "Lemon Water", "waterAmount": 250.0},
      {"beverageName": "Water", "waterAmount": 1000.0}
    ]
  },
  "replyText": "Logged 2 foods, 2 workouts, and 2 water entries."
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
        logger.info("process_message: lang=%s intent=%s msg_preview=%.80s", lang, detected_intent, message)

        # 1. Non-logging or Query intents: Handle immediately with zero latency and 100% precision
        if detected_intent == "WORKOUT_SUGGESTION" or FitnessAdvisoryService.is_workout_suggestion_query(message):
            sugg_text = FitnessAdvisoryService.generate_workout_suggestion_response(message, lang)
            return {
                "intent": "WORKOUT_SUGGESTION",
                "language": lang,
                "entities": {},
                "replyText": sugg_text,
            }

        if detected_intent == "FITNESS_ADVISORY" or (detected_intent == "GENERAL_CHAT" and FitnessAdvisoryService.is_fitness_query(message)):
            advisory_text = FitnessAdvisoryService.generate_advisory_response(message, lang)
            return {
                "intent": "FITNESS_ADVISORY",
                "language": lang,
                "entities": {},
                "replyText": advisory_text,
            }

        if detected_intent == "FOOD_SUGGESTION":
            return {
                "intent": "FOOD_SUGGESTION",
                "language": lang,
                "entities": {},
                "replyText": "Here are some healthy food suggestions tailored to your day.",
            }

        # FUTURE / PLANNED statement — pass intent straight through so route_intent
        # can acknowledge the plan WITHOUT creating any completed log.
        if detected_intent == "FUTURE_LOG":
            return {
                "intent": "FUTURE_LOG",
                "language": lang,
                "entities": {},
                "replyText": "Noted as a plan for later — not logging it as completed.",
            }

        if detected_intent == "DAILY_SUMMARY":
            return {
                "intent": "DAILY_SUMMARY",
                "language": lang,
                "entities": {},
                "replyText": "Here is your personalized daily health and fitness summary.",
            }

        if detected_intent == "QUERY_HYDRATION_LOG":
            return {
                "intent": "QUERY_HYDRATION_LOG",
                "language": lang,
                "entities": {},
                "replyText": "Here is your hydration progress for today.",
            }

        if detected_intent == "GENERAL_CHAT":
            lower_msg = message.lower()
            if any(w in lower_msg for w in ["hi", "hello", "hey", "kem chho", "namaste", "halo"]):
                reply = "Hello! I am your personal Fitness AI coach. I can help you log meals, track workouts and hydration, monitor sleep, and answer your fitness and nutrition questions!"
            else:
                reply = "I can help you track your fitness, log what you ate, record workouts, and reach your goals. Feel free to tell me what you did or ask any question!"
            return {
                "intent": "GENERAL_CHAT",
                "language": lang,
                "entities": {"foodItems": []},
                "replyText": reply,
            }

        if detected_intent == "QUERY_FOOD_LOG":
            return {
                "intent": "QUERY_FOOD_LOG",
                "language": lang,
                "entities": {},
                "replyText": "Here is your nutrition summary for today."
            }

        # 2. Extract candidate entities deterministically across all domains
        foods = AgentNLP.extract_food_entities_heuristically(message)
        acts = AgentNLP.extract_activity_entities(message)
        hyds = AgentNLP.extract_hydration_entities(message)

        # extract_activity_entities() always returns at least one fallback
        # "Workout" entry (requiresClarification=True) when no real exercise
        # keyword was found in the message, so a food-only message like
        # "2 roti ane dal khadhi" would otherwise be misclassified as
        # multi-domain. Only count activities as a genuine signal when they
        # don't need clarification (i.e. a real exercise was actually found).
        genuine_acts = [a for a in acts if not a.get("requiresClarification")]

        # Domain multi-signal check: If entities from 2+ distinct domains are present, enforce CREATE_MULTI_LOG
        domain_count = sum([bool(foods), bool(genuine_acts), bool(hyds)])
        if domain_count >= 2 and detected_intent not in ("QUERY_FOOD_LOG", "QUERY_HYDRATION_LOG", "GENERAL_CHAT"):
            detected_intent = "CREATE_MULTI_LOG"

        # Step 2: Evaluate Extraction Completeness & Confidence Routing
        decision = AgentNLP.evaluate_extraction_completeness(
            message, extracted_foods=foods, extracted_acts=acts, extracted_hyd=hyds, detected_intent=detected_intent
        )
        logger.info("Extraction completeness: decision=%s intent=%s foods=%d acts=%d hyds=%d", decision, detected_intent, len(foods), len(acts), len(hyds))

        # Fast path: High-confidence deterministic results
        if decision == "DETERMINISTIC_HIGH_CONFIDENCE":
            actions = AgentNLP.extract_structured_actions(message)

            if detected_intent == "CREATE_WEIGHT_LOG":
                w_ent = AgentNLP.extract_weight_entity(message)
                return {
                    "intent": "CREATE_WEIGHT_LOG",
                    "language": lang,
                    "entities": w_ent,
                    "replyText": f"Logged body weight of {w_ent['weightKg']} kg."
                }

            if detected_intent == "CREATE_HYDRATION_LOG":
                # A single message can contain MULTIPLE hydration items (e.g.
                # "1 scoop protein shake, 1 scoop whey protein powder, 1 scoop
                # whey protein powder with 300ml water" — three separate
                # supplement/drink entries). Returning only hyds[0] silently
                # dropped every entry after the first. When there's more than
                # one, report them all via hydrationItems (same shape the
                # CREATE_MULTI_LOG path uses) instead of a single h_ent.
                if len(hyds) > 1:
                    total_ml = sum(h.get("amount_ml", 0) for h in hyds)
                    return {
                        "intent": "CREATE_HYDRATION_LOG",
                        "language": lang,
                        "entities": {"hydrationItems": hyds, "hydration": hyds, "waterAmount": total_ml},
                        "replyText": f"Logged {len(hyds)} hydration entries ({int(total_ml)} ml total)."
                    }
                h_ent = hyds[0] if hyds else AgentNLP.extract_hydration_entity(message)
                return {
                    "intent": "CREATE_HYDRATION_LOG",
                    "language": lang,
                    "entities": h_ent,
                    "replyText": f"Logged {int(h_ent['amountMl'])} ml of Water."
                }

            if detected_intent == "CREATE_ACTIVITY_LOG":
                if acts and acts[0].get("requiresClarification"):
                    return {
                        "intent": "CREATE_ACTIVITY_LOG",
                        "language": lang,
                        "actions": actions,
                        "entities": {"activities": acts, "requiresClarification": True},
                        "requiresClarification": True,
                        "replyText": "Great job on being active! Could you please let me know how many minutes you exercised or how many reps and sets you completed, so I can accurately calculate your calories burned?",
                    }
                return {
                    "intent": "CREATE_ACTIVITY_LOG",
                    "language": lang,
                    "actions": actions,
                    "entities": {
                        "activities": acts,
                        "activity": acts[0]["activity"] if acts else "Workout",
                        "durationMinutes": acts[0]["durationMinutes"] if acts else 30.0,
                        "reps": acts[0].get("reps") if acts else None,
                        "sets": acts[0].get("sets") if acts else None,
                    },
                    "replyText": f"Logged {len(acts)} workout item(s).",
                }

            if detected_intent == "CREATE_SLEEP_LOG":
                s_ent = AgentNLP.extract_sleep_entity(message)
                return {
                    "intent": "CREATE_SLEEP_LOG",
                    "language": lang,
                    "entities": s_ent,
                    "replyText": f"Recorded {int(s_ent['durationMinutes']//60)}h of sleep."
                }

            if detected_intent == "CREATE_MULTI_LOG":
                # extract_activity_entities() always returns at least one fallback
                # "Workout" entry (requiresClarification=True) when no real
                # exercise keyword was found in the message. That fallback must
                # NEVER be silently logged as a completed workout just because
                # the message also contained food/hydration — only genuine,
                # recognized activities belong in a multi-log result.
                real_acts = [a for a in acts if not a.get("requiresClarification")]
                return {
                    "intent": "CREATE_MULTI_LOG",
                    "language": lang,
                    "actions": actions,
                    "entities": {
                        "foodItems": foods,
                        "activities": real_acts,
                        "activityItems": real_acts,
                        "hydrationItems": hyds,
                        "hydration": hyds,
                        "waterAmount": sum(h.get("amount_ml", 0) for h in hyds) if hyds else None,
                    },
                    "replyText": f"Logged {len(foods)} food item(s), {len(real_acts)} workout(s), and {len(hyds)} water entry(ies)."
                }

            if detected_intent == "CREATE_FOOD_LOG":
                return {
                    "intent": "CREATE_FOOD_LOG",
                    "language": lang,
                    "actions": actions,
                    "entities": {"foodItems": foods},
                    "replyText": f"Logged {len(foods)} food item(s)."
                }

        # Step 3: For Incomplete / Fuzzy / Ambiguous or Updates/Deletes: Call configured AI provider with RAW message
        logger.info(
            "LLM fallback triggered: lang=%s intent=%s decision=%s provider=%s msg_len=%d",
            lang, detected_intent, decision, settings.AI_PROVIDER or "auto", len(message)
        )
        result: Optional[Dict[str, Any]] = None
        provider = (settings.AI_PROVIDER or "auto").lower()

        if provider == "groq" and settings.GROQ_API_KEY:
            try:
                res = await AIService._call_groq(message, conversation_history)
                if res and res.get("intent"):
                    result = AIService._normalize_llm_result(res, message)
            except Exception as e:
                logger.warning(f"Groq AI failed: {e}")
        elif provider == "cloudflare" and settings.CF_ACCOUNT_ID and settings.CF_API_TOKEN:
            try:
                res = await AIService._call_cloudflare(
                    message, conversation_history, system_prompt=SYSTEM_PROMPT
                )
                if res and res.get("intent"):
                    result = AIService._normalize_llm_result(res, message)
                else:
                    logger.warning(
                        "Cloudflare returned non-JSON or missing intent; raw result: %s",
                        str(res)[:200],
                    )
            except Exception as e:
                logger.warning(f"Cloudflare AI failed: {e}")
        elif provider == "rule_based":
            result = AIService._rule_based_fallback(message, message)
        else:  # "auto" (default)
            if settings.CF_ACCOUNT_ID and settings.CF_API_TOKEN:
                try:
                    res = await AIService._call_cloudflare(
                        message, conversation_history, system_prompt=SYSTEM_PROMPT
                    )
                    if res and res.get("intent"):
                        result = AIService._normalize_llm_result(res, message)
                    else:
                        logger.warning(
                            "Cloudflare returned non-JSON or missing intent (auto); trying Groq. raw=%s",
                            str(res)[:200],
                        )
                except Exception as e:
                    logger.warning(f"Cloudflare AI failed: {e}. Falling back to Groq...")

            if not result and settings.GROQ_API_KEY:
                try:
                    res = await AIService._call_groq(message, conversation_history)
                    if res and res.get("intent"):
                        result = AIService._normalize_llm_result(res, message)
                except Exception as e:
                    logger.warning(f"Groq AI failed: {e}")

        # CRITICAL SAFETY GUARD: If deterministic extraction found multi-domain logs
        # or multiple recognized items (total >= 2), but LLM returned a single-domain
        # intent (e.g. only CREATE_HYDRATION_LOG, dropping food & workout), NEVER allow
        # the LLM to discard the user's multi-entry logs!
        total_deterministic = len(foods) + len(genuine_acts) + len(hyds)
        has_multi_deterministic = (
            (bool(foods) and bool(genuine_acts))
            or (bool(foods) and bool(hyds))
            or (bool(genuine_acts) and bool(hyds))
            or (total_deterministic >= 2 and detected_intent == "CREATE_MULTI_LOG")
        )

        llm_intent = (result or {}).get("intent", "")
        llm_foods = (result or {}).get("entities", {}).get("foodItems", [])
        llm_acts = (result or {}).get("entities", {}).get("activities", []) or (result or {}).get("entities", {}).get("activityItems", [])
        llm_hyds = (result or {}).get("entities", {}).get("hydrationItems", []) or (result or {}).get("entities", {}).get("hydration", [])
        llm_total = len(llm_foods) + len(llm_acts) + (len(llm_hyds) if isinstance(llm_hyds, list) else (1 if (result or {}).get("entities", {}).get("waterAmount") else 0))

        if has_multi_deterministic and (not result or not result.get("intent") or llm_intent != "CREATE_MULTI_LOG" or llm_total < total_deterministic):
            logger.info(
                "Multi-log precedence applied (llm_intent=%s llm_items=%d vs deterministic=%d). Preserving all extracted entries.",
                llm_intent, llm_total, total_deterministic
            )
            actions = AgentNLP.extract_structured_actions(message)
            # extract_activity_entities() always returns at least one fallback
            # "Workout" entry (requiresClarification=True) when no real
            # exercise keyword was found in the message. That fallback must
            # NEVER be silently logged as a completed workout just because
            # the message also contained food/hydration — only genuine,
            # recognized activities belong in a multi-log result. (Previously
            # this filtered on name != "Workout" only, and fell back to the
            # raw `acts` list when every item got filtered out, which let the
            # fallback entry slip right back in.)
            real_acts = [a for a in acts if not a.get("requiresClarification")]
            return {
                "intent": "CREATE_MULTI_LOG",
                "language": lang,
                "actions": actions,
                "entities": {
                    "foodItems": foods,
                    "activities": real_acts,
                    "activityItems": real_acts,
                    "hydrationItems": hyds,
                    "hydration": hyds,
                    "waterAmount": sum(h.get("amount_ml", 0) for h in hyds) if hyds else None,
                },
                "replyText": f"Logged {len(foods)} food item(s), {len(real_acts)} workout(s), and {len(hyds)} water entry(ies)."
            }

        if not result or not result.get("intent"):
            logger.info(
                "All LLM providers failed or returned no intent — using deterministic/rule-based fallback. "
                "message=%.80s", message,
            )
            # If deterministic foods/activities/hydration were found upstream
            # (foods/acts/hyds, computed before the LLM call), use ALL of them.
            # Previously this branch only checked `foods` and built a plain
            # CREATE_FOOD_LOG, which silently dropped any activities or
            # hydration items that had already been correctly extracted —
            # e.g. a multi-item routine message would lose its workout and
            # water entries whenever the LLM call failed or returned invalid
            # JSON, even though the deterministic parsers had found them fine.
            if foods or acts or hyds:
                actions = AgentNLP.extract_structured_actions(message)
                if (foods and acts) or (foods and hyds) or (acts and hyds) or detected_intent == "CREATE_MULTI_LOG":
                    # extract_activity_entities() always returns at least one fallback
                    # "Workout" entry (requiresClarification=True) when no real
                    # exercise keyword was found in the message. That fallback must
                    # NEVER be silently logged as a completed workout just because
                    # the message also contained food/hydration — only genuine,
                    # recognized activities belong in a multi-log result.
                    real_acts = [a for a in acts if not a.get("requiresClarification")]
                    result = {
                        "intent": "CREATE_MULTI_LOG",
                        "language": lang,
                        "actions": actions,
                        "entities": {
                            "foodItems": foods,
                            "activities": real_acts,
                            "activityItems": real_acts,
                            "hydrationItems": hyds,
                            "hydration": hyds,
                            "waterAmount": sum(h.get("amount_ml", 0) for h in hyds) if hyds else None,
                        },
                        "replyText": f"Logged {len(foods)} food item(s), {len(real_acts)} workout(s), and {len(hyds)} water entry(ies)."
                    }
                elif foods:
                    result = {
                        "intent": "CREATE_FOOD_LOG",
                        "language": lang,
                        "actions": actions,
                        "entities": {"foodItems": foods},
                        "replyText": f"Logged {len(foods)} food item(s)."
                    }
                elif acts:
                    result = {
                        "intent": "CREATE_ACTIVITY_LOG",
                        "language": lang,
                        "actions": actions,
                        "entities": {"activities": acts, "activityItems": acts},
                        "replyText": f"Logged {len(acts)} workout item(s)."
                    }
                else:
                    result = {
                        "intent": "CREATE_HYDRATION_LOG",
                        "language": lang,
                        "entities": hyds[0] if len(hyds) == 1 else {"hydrationItems": hyds, "hydration": hyds},
                        "replyText": f"Logged {len(hyds)} water entry(ies)."
                    }
            else:
                result = AIService._rule_based_fallback(message, message)

        return result

    @staticmethod
    async def _call_cloudflare(
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
        *,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 800,
        timeout_secs: int = 60,
    ) -> Optional[Dict[str, Any]]:
        """
        Call Cloudflare Workers AI (default: GLM 4.7 Flash).

        Supports both response shapes:
          - data["result"]["response"]                          (Workers AI text models)
          - data["result"]["choices"][0]["message"]["content"]  (OpenAI-compat models)

        Strips <think>...</think> reasoning blocks before JSON parsing.
        Retries once on transient errors (5xx, timeout, connection error).

        Args:
            message:      The user turn content to send.
            history:      Previous conversation turns (last 6 used).
            model:        Override CF_MODEL; defaults to settings.CF_MODEL which
                          should be set to @cf/zai-org/glm-4.7-flash in .env.
            system_prompt: Override the system prompt; defaults to FITBOT_SYSTEM_PROMPT.
            temperature:  Sampling temperature (default 0.2 for precision).
            max_tokens:   Max reply tokens (default 800).
            timeout_secs: Request timeout in seconds (default 60).

        Returns:
            Parsed dict from the JSON response, or None on failure.
        """
        active_model = model or settings.CF_MODEL
        active_system = system_prompt or FITBOT_SYSTEM_PROMPT

        url = (
            f"https://api.cloudflare.com/client/v4/accounts/"
            f"{settings.CF_ACCOUNT_ID}/ai/run/{active_model}"
        )
        headers = {
            "Authorization": f"Bearer {settings.CF_API_TOKEN}",
            "Content-Type": "application/json",
        }

        messages = [{"role": "system", "content": active_system}]
        if history:
            for h in history[-6:]:
                messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
        messages.append({"role": "user", "content": message})

        payload = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        last_exc: Optional[Exception] = None
        for attempt in range(2):   # one retry on failure
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        url,
                        headers=headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=timeout_secs),
                    ) as res:
                        if res.status >= 500:
                            body = await res.text()
                            logger.warning(
                                "Cloudflare %s attempt %d: HTTP %d — %s",
                                active_model, attempt + 1, res.status, body[:200],
                            )
                            last_exc = RuntimeError(f"HTTP {res.status}")
                            if attempt == 0:
                                await asyncio.sleep(1)
                            continue
                        if res.status != 200:
                            body = await res.text()
                            logger.warning(
                                "Cloudflare %s: HTTP %d — %s",
                                active_model, res.status, body[:200],
                            )
                            return None

                        data = await res.json()
                        raw_reply = AIService._extract_cf_response_text(data)
                        if raw_reply is None:
                            logger.warning("Cloudflare response had no text content: %s", str(data)[:300])
                            return None
                        return AIService._parse_json(raw_reply)

            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                logger.warning(
                    "Cloudflare %s attempt %d failed: %s", active_model, attempt + 1, exc
                )
                last_exc = exc
                if attempt == 0:
                    await asyncio.sleep(1)

        logger.error("Cloudflare call failed after 2 attempts: %s", last_exc)
        return None

    @staticmethod
    def _normalize_llm_result(res: Dict[str, Any], raw_message: str) -> Dict[str, Any]:
        """Post-process LLM structured output to ensure canonical food names and valid units."""
        if not res or not isinstance(res, dict):
            return res
        entities = res.get("entities", {})
        if "foodItems" in entities and isinstance(entities["foodItems"], list):
            from .agent_nlp import INDIAN_FOOD_SYNONYMS
            for item in entities["foodItems"]:
                food_name = item.get("food") or item.get("food_name", "")
                if food_name:
                    fn_low = food_name.lower().strip()
                    if fn_low in INDIAN_FOOD_SYNONYMS:
                        canonical = INDIAN_FOOD_SYNONYMS[fn_low]
                        item["food"] = canonical
                        item["food_name"] = canonical
                    else:
                        try:
                            from .food_matcher import match_food
                            m = match_food(food_name)
                            if m.status == "matched" and m.matched_name:
                                item["food"] = m.matched_name
                                item["food_name"] = m.matched_name
                        except Exception:
                            pass
        return res

    @staticmethod
    def _extract_cf_response_text(data: Dict[str, Any]) -> Optional[str]:
        """
        Extract the text content from a Cloudflare Workers AI response.

        Handles both response shapes (choices[0].message.content, message.reasoning,
        and result.response) and strips <think>...</think> blocks.
        """
        result_data = data.get("result", {})

        if isinstance(result_data, dict):
            # Shape 1: OpenAI-compat — choices[0].message.content or choices[0].message.reasoning
            choices = result_data.get("choices") or []
            if choices and isinstance(choices[0], dict):
                msg = choices[0].get("message", {})
                raw = msg.get("content") or ""
                if not raw and (msg.get("reasoning") or msg.get("reasoning_content")):
                    raw = msg.get("reasoning") or msg.get("reasoning_content") or ""
                if raw:
                    return AIService._strip_reasoning(raw)

            # Shape 2: Workers AI text — result.response
            raw = result_data.get("response", "")
            if raw:
                return AIService._strip_reasoning(raw)

        elif isinstance(result_data, str) and result_data:
            return AIService._strip_reasoning(result_data)

        return None

    @staticmethod
    def _strip_reasoning(text: str) -> str:
        """
        Remove <think>...</think> reasoning blocks emitted by GLM / DeepSeek models.

        Args:
            text: Raw LLM output string.

        Returns:
            Cleaned string with reasoning blocks removed and whitespace trimmed.
        """
        cleaned = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE)
        return cleaned.strip()

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
        """
        Extract and parse the first JSON object from a raw LLM response.

        Delegates to food_matcher.parse_llm_json which handles:
          - <think>...</think> stripping
          - ```json fences
          - First { ... } extraction
          - Safe json.loads with fallback to None

        Args:
            raw: Raw string output from the LLM.

        Returns:
            Parsed dict, or None on failure.
        """
        from .food_matcher import parse_llm_json  # avoid circular import at module level
        result = parse_llm_json(raw)
        if result is None:
            logger.warning(
                "parse_llm_json returned None — LLM may have produced non-JSON prose. "
                "raw_preview=%.200s", raw or ""
            )
        return result

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
            acts = AgentNLP.extract_activity_entities(original_message)
            return {
                "intent": "CREATE_ACTIVITY_LOG",
                "language": lang,
                "entities": {
                    "activities": acts,
                    "activity": acts[0]["activity"],
                    "durationMinutes": acts[0]["durationMinutes"],
                    "reps": acts[0].get("reps"),
                    "sets": acts[0].get("sets"),
                },
                "replyText": f"Logged {len(acts)} workout item(s).",
            }

        # 6. MULTI_LOG fallback
        if intent == "CREATE_MULTI_LOG":
            foods = AgentNLP.extract_food_entities_heuristically(original_message)
            acts = AgentNLP.extract_activity_entities(original_message)
            hydrations = AgentNLP.extract_hydration_entities(original_message)
            actions = AgentNLP.extract_structured_actions(original_message)
            # extract_activity_entities() always returns at least one fallback
            # "Workout" entry (requiresClarification=True) when no real
            # exercise keyword was found in the message. That fallback must
            # NEVER be silently logged as a completed workout just because
            # the message also contained food/hydration — only genuine,
            # recognized activities belong in a multi-log result. (Previously
            # this filtered on name != "Workout" only, and fell back to the
            # raw `acts` list when every item got filtered out, which let the
            # fallback entry slip right back in.)
            real_acts = [a for a in acts if not a.get("requiresClarification")]
            return {
                "intent": "CREATE_MULTI_LOG",
                "language": lang,
                "actions": actions,
                "entities": {
                    "foodItems": foods,
                    "activities": real_acts,
                    "activityItems": real_acts,
                    "hydrationItems": hydrations,
                    "hydration": hydrations,
                    "waterAmount": sum(h.get("amount_ml", 0) for h in hydrations) if hydrations else None,
                },
                "replyText": f"Logged {len(foods)} food item(s), {len(real_acts)} workout(s), and {len(hydrations)} water entry(ies)."
            }

        # 7. FOOD_LOG fallback
        if intent == "CREATE_FOOD_LOG":
            food_items = AgentNLP.extract_food_entities_heuristically(pre_processed)
            if food_items:
                return {
                    "intent": "CREATE_FOOD_LOG",
                    "language": lang,
                    "entities": {"foodItems": food_items},
                    "replyText": f"Logged {len(food_items)} food items.",
                }

        # 7. FITNESS_ADVISORY or fitness query fallback
        if intent == "FITNESS_ADVISORY" or FitnessAdvisoryService.is_fitness_query(original_message):
            return {
                "intent": "FITNESS_ADVISORY",
                "language": lang,
                "entities": {},
                "replyText": FitnessAdvisoryService.generate_advisory_response(original_message, lang),
            }

        # 8. GENERAL_CHAT fallback
        return {
            "intent": "GENERAL_CHAT",
            "language": lang,
            "entities": {},
            "replyText": "I am here to help you log meals, track your workouts, and reach your fitness goals.",
        }
