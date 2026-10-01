# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, 'backend')
from app.services.agent_nlp import AgentNLP

print("AgentNLP loaded successfully!")

test_inputs = [
    "2 rti khadhi ne 1 vatki daaal pithi",
    "chkn bresst 150gm and brwn rce 1 bwl",
    "panu 750 mll pitu",
    "wlaked for 45 mins",
    "20 squats, 15 pushups, 30 min walking",
    "20 sqats ne 15 pusups karya",
    "skwats 25 reps n 3 st bnk prss",
    "Is roti healthy?",
    "What if I eat 2 rotis?",
    "Tell me about dal",
    "I don't want to log food",
    "How many calories are in rice?",
    "What are the benefits of walking?",
    "My friend ate 2 rotis"
]

for inp in test_inputs:
    intent = AgentNLP.detect_intent(inp)
    foods = AgentNLP.extract_food_entities_heuristically(inp)
    acts = AgentNLP.extract_activity_entities(inp)
    comp = AgentNLP.evaluate_extraction_completeness(inp, intent, foods, acts)
    print(f"INP: {inp}\n  -> INTENT: {intent}\n  -> FOODS: {foods}\n  -> ACTS: {acts}\n  -> COMP: {comp}\n")
