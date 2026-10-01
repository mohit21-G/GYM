import sys
sys.path.insert(0, 'backend')
from app.services.agent_nlp import AgentNLP

msg = "2 rti khadhi ne 1 vatki daaal pithi"
repaired = AgentNLP.repair_missing_spaces_and_typos(msg)
print("Original:", msg)
print("Repaired:", repaired)
intent = AgentNLP.detect_intent(msg)
print("Intent:", intent)
foods = AgentNLP.extract_food_entities_heuristically(msg)
print("Foods:", foods)
