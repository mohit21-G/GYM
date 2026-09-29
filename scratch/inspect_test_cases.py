import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('benchmark/benchmark_10k/results/execution_results_10k.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        d = json.loads(line)
        if 'SLP-' in d['test_id']:
            print(json.dumps(d, ensure_ascii=False, indent=2))
            break
