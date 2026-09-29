import json
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath("."))

sleep_cases = []
with open('benchmark/benchmark_10k/dataset/benchmark_10k_cases.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        tc = json.loads(line)
        if tc.get('category') == 'Sleep Tracking':
            sleep_cases.append(tc)

print(f"Total sleep cases: {len(sleep_cases)}")
from collections import Counter
print("Languages:", Counter(c['language'] for c in sleep_cases))

# Test extract_sleep_entity and detect_intent on sample sleep cases across all languages
from backend.app.services.agent_nlp import AgentNLP

failed_intents = []
for tc in sleep_cases:
    inp = tc['input_text']
    intent = AgentNLP.detect_intent(inp)
    sleep_ent = AgentNLP.extract_sleep_entity(inp)
    if intent != 'CREATE_SLEEP_LOG':
        failed_intents.append((tc['test_id'], tc['language'], inp, intent))

print(f"Non-CREATE_SLEEP_LOG intents: {len(failed_intents)} / {len(sleep_cases)}")
for tid, lang, inp, intent in failed_intents[:15]:
    print(f"  [{tid}] ({lang}) {inp!r} -> {intent}")
