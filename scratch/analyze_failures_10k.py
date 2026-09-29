import json
import sys
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding='utf-8')

# Load dataset
dataset = {}
with open('benchmark/benchmark_10k/dataset/benchmark_10k_cases.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            d = json.loads(line)
            dataset[d['test_id']] = d

# Load results
results = []
with open('benchmark/benchmark_10k/results/execution_results_10k.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            results.append(json.loads(line))

print(f"Total dataset: {len(dataset)}, Total results: {len(results)}")

# Group by status
status_counts = Counter(r['status'] for r in results)
print(f"Status Counts: {dict(status_counts)}")

# 1. FALSE POSITIVES (315)
fps = [r for r in results if 'False positive' in r.get('reason', '')]
print(f"\n==================================================")
print(f"1. FALSE POSITIVES ANALYSIS (Total: {len(fps)})")
print(f"==================================================")
fp_categories = Counter(r['category'] for r in fps)
print(f"By category: {dict(fp_categories)}")
print("\nSample False Positives (Inputs vs Outputs):")
for r in fps[:12]:
    tid = r['test_id']
    tc = dataset.get(tid, {})
    print(f"[{tid}] Cat: {tc.get('category')} | Subcat: {tc.get('subcategory')} | Lang: {tc.get('language')}")
    print(f"  Input:    {tc.get('input_text')}")
    print(f"  Expected: {tc.get('expected_intent')} -> {tc.get('expected_action')}")
    print(f"  Output:   {r.get('actual_output')}")
    print(f"  Reason:   {r.get('reason')}")
    print()

# 2. FOOD LOGGING FAILURES & PARTIALS
food_cases = [r for r in results if r['category'] == 'Food Logging']
food_status = Counter(r['status'] for r in food_cases)
print(f"\n==================================================")
print(f"2. FOOD LOGGING ANALYSIS (Total: {len(food_cases)})")
print(f"Status: {dict(food_status)}")
print(f"==================================================")

food_fails = [r for r in food_cases if r['status'] == 'FAIL']
print(f"\nFood Failures ({len(food_fails)}):")
fail_outputs = Counter(r.get('actual_output', '')[:50] for r in food_fails)
print("Top failure outputs:")
for out, cnt in fail_outputs.most_common(5):
    print(f"  [{cnt:3d}] {out!r}")

print("\nSample Food Failures:")
for r in food_fails[:8]:
    tid = r['test_id']
    tc = dataset.get(tid, {})
    print(f"[{tid}] Lang: {tc.get('language')} | Diff: {tc.get('difficulty')}")
    print(f"  Input:    {tc.get('input_text')}")
    print(f"  Expected: {tc.get('expected_intent')} -> Food: {tc.get('expected_canonical_food')}")
    print(f"  Output:   {r.get('actual_output')}")
    print(f"  Reason:   {r.get('reason')}")
    print()

food_partials = [r for r in food_cases if r['status'] == 'PARTIAL_PASS']
print(f"\nFood Partials ({len(food_partials)}):")
print("Sample Food Partials (Semantic mismatches or quantity/unit issues):")
for r in food_partials[:8]:
    tid = r['test_id']
    tc = dataset.get(tid, {})
    print(f"[{tid}] Lang: {tc.get('language')}")
    print(f"  Input:    {tc.get('input_text')}")
    print(f"  Expected: Food={tc.get('expected_canonical_food')}, Qty={tc.get('expected_quantity')}, Unit={tc.get('expected_unit')}")
    print(f"  Actual:   Food={r.get('actual_food')}, Qty={r.get('actual_quantity')}")
    print(f"  Reason:   {r.get('reason')}")
    print()

# 3. SLEEP LOGGING ANALYSIS
sleep_cases = [r for r in results if r['category'] == 'Sleep Tracking']
sleep_status = Counter(r['status'] for r in sleep_cases)
print(f"\n==================================================")
print(f"3. SLEEP LOGGING ANALYSIS (Total: {len(sleep_cases)})")
print(f"Status: {dict(sleep_status)}")
print(f"==================================================")
sleep_partials = [r for r in sleep_cases if r['status'] == 'PARTIAL_PASS']
print(f"Sleep Partials ({len(sleep_partials)}):")
for r in sleep_partials[:6]:
    tid = r['test_id']
    tc = dataset.get(tid, {})
    print(f"[{tid}] Lang: {tc.get('language')}")
    print(f"  Input:    {tc.get('input_text')}")
    print(f"  Expected: Action={tc.get('expected_action')}")
    print(f"  Output:   {r.get('actual_output')}")
    print(f"  Reason:   {r.get('reason')}")
    print()

# 4. EDGE CASES & ROBUSTNESS ANALYSIS
edge_cases = [r for r in results if r['category'] == 'Edge Cases & Robustness']
edge_status = Counter(r['status'] for r in edge_cases)
print(f"\n==================================================")
print(f"4. EDGE CASES ANALYSIS (Total: {len(edge_cases)})")
print(f"Status: {dict(edge_status)}")
print(f"==================================================")
for r in [r for r in edge_cases if r['status'] != 'PASS'][:8]:
    tid = r['test_id']
    tc = dataset.get(tid, {})
    print(f"[{tid}] Status: {r.get('status')} | Lang: {tc.get('language')}")
    print(f"  Input:    {tc.get('input_text')}")
    print(f"  Expected: Intent={tc.get('expected_intent')} -> Action={tc.get('expected_action')}")
    print(f"  Output:   {r.get('actual_output')}")
    print(f"  Reason:   {r.get('reason')}")
    print()
