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

with open('benchmark/benchmark_10k/results/execution_results_10k.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        r = json.loads(line)
        if 'False positive' in r.get('reason', ''):
            tc = dataset.get(r['test_id'])
            if tc and tc.get('category') == 'Edge Cases & Robustness':
                print(f"[{tc['test_id']}] {tc['input_text']!r} -> Exp: {tc['expected_intent']} / {tc['expected_action']}")
