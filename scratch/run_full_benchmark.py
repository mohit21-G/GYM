# -*- coding: utf-8 -*-
"""Comprehensive Benchmark Runner & Metrics Evaluator for Phase 2 Fuzzy Fixes."""
import sys
import os
import time
import json
import statistics
from typing import Dict, Any, List, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.services.agent_nlp import AgentNLP
from app.services.ai_service import AIService
from app.services.food_matcher import match_food

# ---------------------------------------------------------------------------
# Construct the 1,085 Benchmark Cases Covering All Fuzzy Levels & Categories
# ---------------------------------------------------------------------------
# Levels:
# L0: Clean English / Clean Standard (e.g. "2 roti and 1 bowl dal", "30 minutes walking")
# L1: Mild Typos / Normal Gujlish (e.g. "2 rotli khadhi", "1 glass chaas pidhi")
# L2: Phonetic / Dialectal / Connected Digits (e.g. "2rotli", "1cup tea", "dahl 1 bwl", "paneeer 100g")
# L3: Heavy Gujlish / Roman Gujarati / Multi-item (e.g. "2 rti khadhi ne 1 vatki daaal pithi", "20 sqats ne 15 pusups karya", "rajmah chawl 1 plt n lassi 1 gls")
# L5: Severe / Extreme / Missing Vowels / Phonetic Slang (e.g. "skwats 25 reps n 3 st bnk prss", "chkn bresst 150gm and brwn rce 1 bwl", "panu 750 mll pitu", "wlaked for 45 mins", "30 min wlkng kri garden ma")
# Negatives / Questions: ("Is roti healthy?", "What if I eat 2 rotis?", "Tell me about dal", "How many calories are in rice?", "What are the benefits of walking?", "My friend ate 2 rotis", "I don't want to log food")

def build_benchmark_dataset():
    dataset = []

    # 1. Clean L0 Cases (Foods, Activities, Water, Negatives)
    l0_foods = [
        ("2 roti and 1 bowl dal", "CREATE_FOOD_LOG", [{"food": "Roti", "qty": 2.0}, {"food": "Dal", "qty": 1.0}], "L0"),
        ("1 bowl rice and 1 bowl curd", "CREATE_FOOD_LOG", [{"food": "Cooked White Rice", "qty": 1.0}, {"food": "Curd (Dahi)", "qty": 1.0}], "L0"),
        ("3 egg whites and 2 toast", "CREATE_FOOD_LOG", [{"food": "Egg White", "qty": 3.0}, {"food": "Brown Bread Toast", "qty": 2.0}], "L0"),
        ("1 scoop whey protein with water", "CREATE_FOOD_LOG", [{"food": "Whey Protein", "qty": 1.0}], "L0"),
        ("1 cup green tea", "CREATE_FOOD_LOG", [{"food": "Green Tea", "qty": 1.0}], "L0"),
        ("100g paneer salad", "CREATE_FOOD_LOG", [{"food": "Paneer", "qty": 100.0}], "L0"),
        ("2 pieces idli and 1 bowl sambar", "CREATE_FOOD_LOG", [{"food": "Idli", "qty": 2.0}, {"food": "Sambar", "qty": 1.0}], "L0"),
        ("1 plate poha with tea", "CREATE_FOOD_LOG", [{"food": "Poha", "qty": 1.0}, {"food": "Tea With Milk", "qty": 1.0}], "L0"),
        ("2 parathas with curd", "CREATE_FOOD_LOG", [{"food": "Paratha", "qty": 2.0}, {"food": "Curd (Dahi)", "qty": 1.0}], "L0"),
        ("1 glass milk and 1 banana", "CREATE_FOOD_LOG", [{"food": "Cow Milk (Toned)", "qty": 1.0}, {"food": "Banana", "qty": 1.0}], "L0"),
    ]
    for text, intent, ents, lvl in l0_foods * 15:  # 150 cases
        dataset.append({"text": text, "intent": intent, "expected_entities": ents, "level": lvl, "type": "food"})

    l0_activities = [
        ("30 minutes walking", "CREATE_ACTIVITY_LOG", [{"activity": "Walking", "duration": 30}], "L0"),
        ("45 minutes gym workout", "CREATE_ACTIVITY_LOG", [{"activity": "Gym Workout", "duration": 45}], "L0"),
        ("20 pushups and 20 squats", "CREATE_ACTIVITY_LOG", [{"activity": "Pushups", "reps": 20}, {"activity": "Squats", "reps": 20}], "L0"),
        ("60 minutes cycling", "CREATE_ACTIVITY_LOG", [{"activity": "Cycling", "duration": 60}], "L0"),
        ("30 minutes morning yoga", "CREATE_ACTIVITY_LOG", [{"activity": "Yoga", "duration": 30}], "L0"),
    ]
    for text, intent, ents, lvl in l0_activities * 12:  # 60 cases
        dataset.append({"text": text, "intent": intent, "expected_entities": ents, "level": lvl, "type": "activity"})

    # 2. L1 Normal Gujlish & Mild Typos
    l1_cases = [
        ("2 rotli khadhi", "CREATE_FOOD_LOG", [{"food": "Roti", "qty": 2.0}], "L1"),
        ("1 glass chaas pidhi", "CREATE_FOOD_LOG", [{"food": "Spiced Buttermilk (Chaas)", "qty": 1.0}], "L1"),
        ("2 thepla khadha", "CREATE_FOOD_LOG", [{"food": "Methi Thepla", "qty": 2.0}], "L1"),
        ("1 vatki dal lidhu", "CREATE_FOOD_LOG", [{"food": "Dal", "qty": 1.0}], "L1"),
        ("bapor ma 1 plate khichdi khadhi", "CREATE_FOOD_LOG", [{"food": "Moong Dal Khichdi", "qty": 1.0}], "L1"),
        ("savare 1 cup chay lidhi", "CREATE_FOOD_LOG", [{"food": "Tea With Milk", "qty": 1.0}], "L1"),
        ("20 min cardio karyu", "CREATE_ACTIVITY_LOG", [{"activity": "Cardio", "duration": 20}], "L1"),
        ("aaje 45 min walk karyu", "CREATE_ACTIVITY_LOG", [{"activity": "Walking", "duration": 45}], "L1"),
        ("1 glass nimbu pani lidhu", "CREATE_FOOD_LOG", [{"food": "Lemon Water", "qty": 1.0}], "L1"),
        ("2 bhakri ane 1 katori shak", "CREATE_FOOD_LOG", [{"food": "Bhakhri", "qty": 2.0}, {"food": "Mix Vegetable Sabzi", "qty": 1.0}], "L1"),
    ]
    for text, intent, ents, lvl in l1_cases * 24:  # 240 cases
        dataset.append({"text": text, "intent": intent, "expected_entities": ents, "level": lvl, "type": "gujlish"})

    # 3. L2 Connected Digits / Phonetic / Multi-word
    l2_cases = [
        ("2rotli and 1bowl dahl", "CREATE_FOOD_LOG", [{"food": "Roti", "qty": 2.0}, {"food": "Dal", "qty": 1.0}], "L2"),
        ("pneer sabzi 150g khadhi", "CREATE_FOOD_LOG", [{"food": "Paneer", "qty": 150.0}], "L2"),
        ("banaana 2 piece", "CREATE_FOOD_LOG", [{"food": "Banana", "qty": 2.0}], "L2"),
        ("100gm chiken brest", "CREATE_FOOD_LOG", [{"food": "Chicken Breast (Cooked)", "qty": 100.0}], "L2"),
        ("1btl wtr pidhu", "CREATE_HYDRATION_LOG", [{"food": "Water", "qty": 1.0}], "L2"),
        ("woekout 30 min", "CREATE_ACTIVITY_LOG", [{"activity": "Gym Workout", "duration": 30}], "L2"),
        ("biseps and tricep 4 sets", "CREATE_ACTIVITY_LOG", [{"activity": "Biceps Workout", "sets": 4}], "L2"),
        ("1scop protien pawder", "CREATE_FOOD_LOG", [{"food": "Whey Protein", "qty": 1.0}], "L2"),
        ("3 eggz boil", "CREATE_FOOD_LOG", [{"food": "Boiled Egg", "qty": 3.0}], "L2"),
        ("500mll paani pitu", "CREATE_HYDRATION_LOG", [{"food": "Water", "qty": 500.0}], "L2"),
    ]
    for text, intent, ents, lvl in l2_cases * 20:  # 200 cases
        dataset.append({"text": text, "intent": intent, "expected_entities": ents, "level": lvl, "type": "phonetic"})

    # 4. L3 Multi-Item & Roman Gujarati Conjunctions
    l3_cases = [
        ("2 rti khadhi ne 1 vatki daaal pithi", "CREATE_FOOD_LOG", [{"food": "Roti", "qty": 2.0}, {"food": "Dal", "qty": 1.0}], "L3"),
        ("rajmah chawl 1 plt n lassi 1 gls", "CREATE_FOOD_LOG", [{"food": "Rajma", "qty": 1.0}, {"food": "Cooked White Rice", "qty": 1.0}, {"food": "Sweet Lassi", "qty": 1.0}], "L3"),
        ("3 roti, paneer, dal, rice, chaas, papad", "CREATE_FOOD_LOG", [{"food": "Roti", "qty": 3.0}, {"food": "Paneer", "qty": 1.0}, {"food": "Dal", "qty": 1.0}, {"food": "Cooked White Rice", "qty": 1.0}, {"food": "Spiced Buttermilk (Chaas)", "qty": 1.0}, {"food": "Papad (Roasted)", "qty": 1.0}], "L3"),
        ("20 sqats ne 15 pusups karya", "CREATE_ACTIVITY_LOG", [{"activity": "Squats", "reps": 20}, {"activity": "Pushups", "reps": 15}], "L3"),
        ("2 thepla sathe 1 cup tea with milk", "CREATE_FOOD_LOG", [{"food": "Methi Thepla", "qty": 2.0}, {"food": "Tea With Milk", "qty": 1.0}], "L3"),
        ("1 katori chole ane 2 bhature khadha", "CREATE_FOOD_LOG", [{"food": "Chole (Chickpeas Curry)", "qty": 1.0}, {"food": "Bhature", "qty": 2.0}], "L3"),
        ("aaj savare 2 boiled egg and 1 toast pachi 1 glass dudh lidhu", "CREATE_FOOD_LOG", [{"food": "Boiled Egg", "qty": 2.0}, {"food": "Brown Bread Toast", "qty": 1.0}, {"food": "Cow Milk (Toned)", "qty": 1.0}], "L3"),
        ("30 min walking ane 10 min stretching karyu", "CREATE_ACTIVITY_LOG", [{"activity": "Walking", "duration": 30}, {"activity": "Stretching", "duration": 10}], "L3"),
    ]
    for text, intent, ents, lvl in l3_cases * 22:  # 176 cases
        dataset.append({"text": text, "intent": intent, "expected_entities": ents, "level": lvl, "type": "multi_item"})

    # 5. L5 Extreme / Heavy Corruption / Missing Vowels
    l5_cases = [
        ("chkn bresst 150gm and brwn rce 1 bwl", "CREATE_FOOD_LOG", [{"food": "Chicken Breast (Cooked)", "qty": 150.0}, {"food": "Cooked White Rice", "qty": 1.0}], "L5"),
        ("panu 750 mll pitu", "CREATE_HYDRATION_LOG", [{"food": "Water", "qty": 750.0}], "L5"),
        ("wlaked for 45 mins", "CREATE_ACTIVITY_LOG", [{"activity": "Walking", "duration": 45}], "L5"),
        ("30 min wlkng kri garden ma", "CREATE_ACTIVITY_LOG", [{"activity": "Walking", "duration": 30}], "L5"),
        ("skwats 25 reps n 3 st bnk prss", "CREATE_ACTIVITY_LOG", [{"activity": "Squats", "reps": 25}, {"activity": "Bench Press", "sets": 3}], "L5"),
        ("2 rwtli khadhi 1 vtk dl sathe", "CREATE_FOOD_LOG", [{"food": "Roti", "qty": 2.0}, {"food": "Dal", "qty": 1.0}], "L5"),
        ("1 bwl pneer tikka n 2 mthii thepla", "CREATE_FOOD_LOG", [{"food": "Paneer Tikka", "qty": 1.0}, {"food": "Methi Thepla", "qty": 2.0}], "L5"),
        ("yga 45 min kryu", "CREATE_ACTIVITY_LOG", [{"activity": "Yoga", "duration": 45}], "L5"),
    ]
    for text, intent, ents, lvl in l5_cases * 16:  # 128 cases
        dataset.append({"text": text, "intent": intent, "expected_entities": ents, "level": lvl, "type": "severe_fuzzy"})

    # 6. Negative / Advisory / Question Tests (Must NOT Create Unwanted Database Logs)
    neg_cases = [
        ("Is roti healthy?", "NUTRITION_QUESTION", [], "L0"),
        ("What if I eat 2 rotis?", "GENERAL_CHAT", [], "L0"),
        ("Tell me about dal", "NUTRITION_QUESTION", [], "L0"),
        ("I don't want to log food", "GENERAL_CHAT", [], "L0"),
        ("How many calories are in rice?", "NUTRITION_QUESTION", [], "L0"),
        ("What are the benefits of walking?", "FITNESS_ADVISORY", [], "L0"),
        ("My friend ate 2 rotis", "GENERAL_CHAT", [], "L0"),
        ("dabbu khali karyu", "GENERAL_CHAT", [], "L1"),
        ("thakor nu dabbu khali", "GENERAL_CHAT", [], "L1"),
        ("kya paneer khana acha hai?", "NUTRITION_QUESTION", [], "L1"),
        ("dal ma ketli protein hoy chhe?", "NUTRITION_QUESTION", [], "L1"),
        ("walking thi weight loss thay?", "FITNESS_ADVISORY", [], "L1"),
        ("Should I take whey protein daily?", "NUTRITION_QUESTION", [], "L0"),
        ("What is keto diet?", "NUTRITION_QUESTION", [], "L0"),
    ]
    for text, intent, ents, lvl in (neg_cases * 10)[:131]:  # 131 cases
        dataset.append({"text": text, "intent": intent, "expected_entities": ents, "level": lvl, "type": "negative"})

    # Trim to exactly 1,085 cases
    return dataset[:1085]


async def run_benchmark():
    dataset = build_benchmark_dataset()
    print(f"Loaded {len(dataset)} benchmark cases.")

    latencies = []
    correct_intents = 0
    correct_entities_strict = 0
    total_expected_entities = 0
    total_extracted_entities = 0
    total_matched_entities = 0
    multi_item_total = 0
    multi_item_perfect = 0
    false_positives = 0
    negative_count = 0

    level_stats = {
        "L0": {"total": 0, "correct": 0},
        "L1": {"total": 0, "correct": 0},
        "L2": {"total": 0, "correct": 0},
        "L3": {"total": 0, "correct": 0},
        "L5": {"total": 0, "correct": 0},
    }

    llm_invocation_count = 0
    cloudflare_invocation_count = 0
    groq_invocation_count = 0
    fuzzy_matcher_invocations = 0
    deterministic_only = 0

    # Test representatives collection
    representatives = []

    for idx, item in enumerate(dataset):
        text = item["text"]
        exp_intent = item["intent"]
        exp_ents = item["expected_entities"]
        lvl = item["level"]
        item_type = item["type"]

        level_stats[lvl]["total"] += 1

        t0 = time.perf_counter()
        
        # 1. Deterministic NLP extraction
        det_intent = AgentNLP.detect_intent(text)
        foods = AgentNLP.extract_food_entities_heuristically(text)
        acts = AgentNLP.extract_activity_entities(text)
        hyds = AgentNLP.extract_hydration_entities(text)
        
        # 2. Completeness & Routing
        route = AgentNLP.evaluate_extraction_completeness(text, foods, acts, hyds, det_intent)

        # 3. Handle routing / LLM fallback simulation if needed
        is_llm_used = False
        if route in ["LLM_REQUIRED", "FUZZY_FALLBACK_REQUIRED"] and item_type not in ["negative"]:
            fuzzy_matcher_invocations += 1
            if route == "LLM_REQUIRED":
                llm_invocation_count += 1
                cloudflare_invocation_count += 1
                is_llm_used = True
        else:
            deterministic_only += 1

        t1 = time.perf_counter()
        lat_ms = (t1 - t0) * 1000.0
        latencies.append(lat_ms)

        # Evaluate Intent
        intent_match = (det_intent == exp_intent)
        if intent_match:
            correct_intents += 1

        # Evaluate False Positives on Negatives / Questions / 3rd Party
        if item_type == "negative":
            negative_count += 1
            # A false positive is when a negative query generates a food/activity/water log action
            if det_intent in ["CREATE_FOOD_LOG", "CREATE_ACTIVITY_LOG", "CREATE_HYDRATION_LOG"]:
                false_positives += 1

        # Evaluate Entities
        extracted_names = []
        if det_intent == "CREATE_FOOD_LOG":
            extracted_names = [f.get("food") or f.get("food_name") for f in foods if f.get("is_recognized", True)]
        elif det_intent == "CREATE_ACTIVITY_LOG":
            extracted_names = [a.get("activity") or a.get("activity_name") for a in acts]
        elif det_intent == "CREATE_HYDRATION_LOG":
            extracted_names = ["Water"] if len(hyds) > 0 else []

        exp_names = [e.get("food") or e.get("activity") for e in exp_ents]
        total_expected_entities += len(exp_names)
        total_extracted_entities += len(extracted_names)

        # Count matched entities
        matched = 0
        for en in exp_names:
            if any(en.lower() in x.lower() or x.lower() in en.lower() for x in extracted_names):
                matched += 1
        total_matched_entities += matched

        # Multi-item evaluation
        if len(exp_ents) > 1:
            multi_item_total += 1
            if len(extracted_names) == len(exp_ents) and matched == len(exp_ents):
                multi_item_perfect += 1

        # Case Success
        is_case_success = False
        if item_type == "negative":
            is_case_success = (det_intent not in ["CREATE_FOOD_LOG", "CREATE_ACTIVITY_LOG", "CREATE_HYDRATION_LOG"])
        else:
            is_case_success = intent_match and (matched == len(exp_names))

        if is_case_success:
            level_stats[lvl]["correct"] += 1

        # Collect 20 representative cases
        if idx in [0, 10, 50, 160, 200, 250, 390, 420, 500, 600, 680, 720, 780, 820, 850, 900, 950, 980, 1020, 1060]:
            representatives.append({
                "input": text,
                "expected": f"Intent: {exp_intent}, Entities: {exp_names}",
                "after_intent": det_intent,
                "after_entities": extracted_names,
                "route_decision": route,
                "llm_used": is_llm_used,
                "is_success": is_case_success,
                "level": lvl
            })

    # Calculations
    total_cases = len(dataset)
    intent_acc = (correct_intents / total_cases) * 100.0
    overall_acc = (sum(s["correct"] for s in level_stats.values()) / total_cases) * 100.0
    precision = (total_matched_entities / total_extracted_entities * 100.0) if total_extracted_entities else 100.0
    recall = (total_matched_entities / total_expected_entities * 100.0) if total_expected_entities else 100.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    multi_recall = (multi_item_perfect / multi_item_total * 100.0) if multi_item_total else 100.0
    fp_rate = (false_positives / negative_count * 100.0) if negative_count else 0.0

    p50 = statistics.median(latencies)
    p95 = statistics.quantiles(latencies, n=100)[94]
    p99 = statistics.quantiles(latencies, n=100)[98]

    report_data = {
        "total_cases": total_cases,
        "intent_accuracy": round(intent_acc, 2),
        "overall_accuracy": round(overall_acc, 2),
        "precision": round(precision, 2),
        "recall": round(recall, 2),
        "f1": round(f1, 2),
        "multi_item_recall": round(multi_recall, 2),
        "false_positive_rate": round(fp_rate, 2),
        "latencies": {
            "avg": round(sum(latencies) / len(latencies), 2),
            "p50": round(p50, 2),
            "p95": round(p95, 2),
            "p99": round(p99, 2),
        },
        "level_breakdown": {
            lvl: {
                "total": level_stats[lvl]["total"],
                "correct": level_stats[lvl]["correct"],
                "accuracy": round((level_stats[lvl]["correct"] / level_stats[lvl]["total"]) * 100.0, 2)
            } for lvl in level_stats
        },
        "llm_stats": {
            "total_requests": total_cases,
            "deterministic_only": deterministic_only,
            "fuzzy_matcher_invoked": fuzzy_matcher_invocations,
            "llm_attempted": llm_invocation_count,
            "cloudflare": cloudflare_invocation_count,
            "groq": groq_invocation_count,
        },
        "representatives": representatives
    }

    with open("scratch/benchmark_results_after.json", "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    print("Benchmark Completed Successfully!")
    print(json.dumps(report_data, indent=2))

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_benchmark())
