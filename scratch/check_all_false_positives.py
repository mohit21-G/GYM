import json
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath("."))

from backend.app.services.agent_nlp import AgentNLP

dataset = {}
with open('benchmark/benchmark_10k/dataset/benchmark_10k_cases.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        tc = json.loads(line)
        dataset[tc['test_id']] = tc

fps = []
with open('benchmark/benchmark_10k/results/execution_results_10k.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        r = json.loads(line)
        if 'False positive' in r.get('reason', ''):
            fps.append((r['test_id'], dataset.get(r['test_id'])))

print(f"Total false positive cases in results: {len(fps)}")

still_failing = []
for tid, tc in fps:
    if not tc:
        continue
    inp = tc['input_text']
    intent = AgentNLP.detect_intent(inp)
    exp_intent = tc.get('expected_intent')
    exp_act = tc.get('expected_action')
    # If expected_action is NO_LOG, intent must be GENERAL_CHAT or not create food
    if exp_act == "NO_LOG" and intent != "GENERAL_CHAT":
        still_failing.append((tid, tc.get('category'), tc.get('language'), inp, intent, exp_intent))

print(f"Still failing intent detection for NO_LOG: {len(still_failing)} / {len(fps)}")

from collections import Counter
print("Fail categories:", Counter(x[1] for x in still_failing))
print("Fail languages:", Counter(x[2] for x in still_failing))
print("\nSample still failing inputs:")
for tid, cat, lang, inp, intent, exp_intent in still_failing[:20]:
    print(f"  [{tid}] ({cat} | {lang}) {inp!r} -> DETECTED: {intent} (EXP: {exp_intent})")
