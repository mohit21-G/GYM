import sys
import os
import json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath("."))

from backend.app.services.agent_nlp import AgentNLP

test_cases = [
    "ગઈકાલે રાત્રે 7 કલાક ઊંઘ લીધી",
    "रात को 8 घंटे की अच्छी नींद ली",
    "I ate 0 Basundi",
    "I ate 0 Cooked White Rice",
    "1 બાસુંદી",
    "1.5 ખીચડી",
    "1 بھنڈી",
    "sev tameta",
    "Maine 1 alu dosa khaya tha",
    "2 uttapam dinner ma lidhu",
    "ate 2 poh pleez trac",
    "ate 2 pneeeer pleez trac",
    "Ate 2 Sev Tameta Nu Shaak'; DROP TABLE daily_food_logs; --",
    "haven't eaten anything today",
    "aaj kuch nahi khaya",
    "khane ka plan hai",
    "what if I eat 2 rotis",
    "suppose I have a banana",
    "is roti healthy?",
]

for s in test_cases:
    intent = AgentNLP.detect_intent(s)
    foods = AgentNLP.extract_food_entities_heuristically(s)
    print(f"INPUT:  {s}")
    print(f"INTENT: {intent}")
    print(f"FOODS:  {foods}")
    print("-" * 50)
