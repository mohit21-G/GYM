import sys
sys.path.insert(0, 'backend')
from app.services.agent_nlp import AgentNLP

text = """8:30 AM 2 eggs khadha
    1:00 PM dal rice khadhu
    6:00 PM 30 min walking kari"""

foods = AgentNLP.extract_food_entities_heuristically(text)
print("Extracted foods count:", len(foods))
for f in foods:
    print(" - Food:", f.get("food"), "Qty:", f.get("quantity"), "Unit:", f.get("unit"), "Raw:", f.get("raw_text"))
