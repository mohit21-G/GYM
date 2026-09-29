import json
import sys
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')

dataset = {}
with open('benchmark/benchmark_10k/dataset/benchmark_10k_cases.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            d = json.loads(line)
            dataset[d['test_id']] = d

results = []
with open('benchmark/benchmark_10k/results/execution_results_10k.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            results.append(json.loads(line))

fps = [r for r in results if 'False positive' in r.get('reason', '')]
print(f"Total False Positives: {len(fps)}")

subcats = Counter(dataset.get(r['test_id'], {}).get('subcategory') for r in fps)
print("By subcategory:", dict(subcats))

print("\n--- SAMPLE FALSE POSITIVES ---")
for r in fps[:20]:
    tid = r['test_id']
    tc = dataset.get(tid, {})
    print(f"[{tid}] {tc.get('subcategory')} | {tc.get('language')}")
    print(f"  Input:    {tc.get('input_text')}")
    print(f"  Expected: {tc.get('expected_intent')} -> {tc.get('expected_action')}")
    print(f"  Output:   {r.get('actual_output')}")
    print(f"  Reason:   {r.get('reason')}")
    print()
