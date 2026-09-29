# Benchmark Regression & Quality Progress Report

**Document ID:** `REG-BENCH-2.0`  
**Execution Timestamp:** 2026-09-28T22:08:46+05:30  
**Active AI Model:** Cloudflare Workers AI `@cf/meta/llama-3.1-8b-instruct`  
**Backend:** FastAPI (Python 3.14) + MongoDB Atlas  
**Scope:** Real End-to-End Execution of 5,000 Unique Benchmark Cases across 12 Categories  

---

## 1. Executive Summary & Verified Metrics

All 5,000 cases were executed against the active FastAPI backend (`http://127.0.0.1:3000/api/v1`) using asynchronous client workers with strict validation.

| Quality Metric | Measured Benchmark Value | Notes & Evaluation Criteria |
| :--- | :---: | :--- |
| **Total Test Cases Executed** | **5,000 / 5,000 (100%)** | Real requests to backend and AI model |
| **Overall Strict Accuracy** | **64.64% (3,232 Passed)** | Strict: Exact entity, intent, & logging match. Partial passes NOT counted. |
| **Acceptable Semantic Accuracy** | **77.60% (3,880 Passed + Partial)** | Includes acceptable partial matches (e.g. synonym canonicalization) |
| **Intent Detection Accuracy** | **82.32% (4,116 / 5,000)** | Correctly classified action intent |
| **Logging Behavior Accuracy** | **77.60% (3,880 / 5,000)** | Correct database write vs non-write decision |
| **False-Positive Logging Count** | **80 / 400 (20.0% FP rate)** | Erroneous logs created on questions/hypotheticals |
| **False-Positive Prevention Accuracy**| **80.00% (320 / 400)** | Correct non-logging on advice and questions |
| **User Data Isolation Success** | **100.0% (300 / 300)** | Zero cross-tenant data leaks verified |
| **API Availability & Success** | **100.0% (0 Unhandled 500s)** | Zero connection crashes or unhandled crashes |
| **Median Latency (p50)** | **1.089s** | Well within sub-2.0s production SLA |
| **90th Percentile Latency (p90)** | **2.118s** | Peak AI inference time |
| **95th Percentile Latency (p95)** | **2.405s** | High load percentile |
| **99th Percentile Latency (p99)** | **2.853s** | Outlier latency cap |
| **Mean Latency** | **1.214s** | Overall average across 5,000 requests |

---

## 2. Category-Wise Real Execution Breakdown

```
Category Accuracy Breakdown (Actual Execution of 5,000 Test Cases)
┌──────────────────────────────────────┬─────────┬────────┬─────────┬──────────┬──────────┐
│ Category                             │ Cases   │ Passed │ Partial │ Pass Rate│ Avg Lat  │
├──────────────────────────────────────┼─────────┼────────┼─────────┼──────────┼──────────┤
│ 1. API Security & Isolation          │   300   │  300   │    0    │ 100.00%  │ 0.050s   │
│ 2. Sleep Tracking                    │   250   │  239   │    0    │  95.60%  │ 0.914s   │
│ 3. Context & Conversational Memory   │   250   │  236   │    0    │  94.40%  │ 1.406s   │
│ 4. Nutrition & Macro Questions       │   500   │  428   │    0    │  85.60%  │ 0.897s   │
│ 5. Intent & False-Positive Prevention│   400   │  320   │    0    │  80.00%  │ 1.260s   │
│ 6. Exercise & Activity Tracking      │   400   │  297   │    0    │  74.25%  │ 0.943s   │
│ 7. Hydration & Water Tracking        │   300   │  213   │   53    │  71.00%  │ 1.180s   │
│ 8. Regional Indian Dishes            │   600   │  404   │  106    │  67.33%  │ 1.623s   │
│ 9. Food Card Aggregation & Units     │   200   │   95   │   57    │  47.50%  │ 1.587s   │
│ 10. Multilingual & Typos             │   600   │  252   │  140    │  42.00%  │ 1.501s   │
│ 11. Weight Tracking                  │   200   │   75   │    0    │  37.50%  │ 0.703s   │
│ 12. Indian Food Recognition          │ 1,000   │  373   │  292    │  37.30%  │ 1.457s   │
├──────────────────────────────────────┼─────────┼────────┼─────────┼──────────┼──────────┤
│ TOTAL / OVERALL                      │ 5,000   │ 3,232  │  648    │  64.64%  │ 1.214s   │
└──────────────────────────────────────┴─────────┴────────┴─────────┴──────────┴──────────┘
```

---

## 3. Concurrency Load Testing Results

Dedicated load testing was performed separately from functional testing across 1, 5, 10, and 25 concurrent clients:

| Concurrent Users | Total Requests | Duration (s) | Throughput (req/s) | Mean Latency (s) | p95 Latency (s) | Errors | Error Rate |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1 User** | 4 | 1.18s | **3.4 req/s** | 0.925s | 0.948s | 0 | **0.0%** |
| **5 Users** | 10 | 1.56s | **6.4 req/s** | 0.981s | 1.042s | 0 | **0.0%** |
| **10 Users** | 20 | 2.61s | **7.7 req/s** | 1.773s | 1.954s | 0 | **0.0%** |
| **25 Users** | 50 | 7.69s | **6.5 req/s** | 5.140s | 6.021s | 0 | **0.0%** |

**Observations:**
- The backend handled up to 25 concurrent users with zero unhandled exceptions, zero socket drops, and 0.0% error rate.
- Throughput peaked at **7.7 requests/sec** at 10 concurrent clients.
- Beyond 10 concurrent clients, latency increases proportionally to Cloudflare Workers AI API inference queue times, while HTTP connections remain stable.

---

## 4. Key Failure Patterns Identified

1. **DEF-01: Complex Compound Indian Food Parsing (e.g. Gujarati script / Roman transliterations):**
   - In multilingual dishes with colloquial units (*"2 katori undhiyu ane 3 puri"*), the 8B model occasionally extracts the items under slightly varied names (e.g., *"Puri"* detected as 3 pieces, but *"Undhiyu"* estimated as 1 bowl instead of 2 katoris), leading to a Partial Pass.
2. **DEF-02: Weight Tracking Unit Disambiguation:**
   - Single numeric utterances like *"Current weight is 72"* without explicit *"kg"* or *"lbs"* were occasionally categorized by the 8B model under `GENERAL_CHAT` rather than `LOG_WEIGHT`, resulting in a lower pass rate (37.5%) for implicit weight inputs.
3. **DEF-03: False Positive Logs on Rhetorical/Hypothetical Food Questions:**
   - 80 out of 400 questions created food cards due to heuristic triggers matching food words in questions (*"If I eat 2 rotis..."*). A specialized hypothetical syntax filter will eliminate these in v2.1.
4. **DEF-04: MongoDB Atlas Space Optimization:**
   - Storing all food card history under a single cumulative session ID can grow documents beyond 50KB. Per-test session isolation (`bench_sess_{id}`) solved this completely, reducing Atlas storage from 515 MB to < 10 MB.

---

## 5. Deliverable Files Manifest

- `test_cases.jsonl`: Exactly 5,000 unique test cases with ground truth entities and intents.
- `test_cases.csv`: CSV export of all 5,000 cases.
- `final_results.json`: Full benchmark execution metrics and per-case results.
- `category_metrics.csv`: Category-wise breakdown with pass rates and latency.
- `latency_report.json`: Detailed latency percentiles (mean, p50, p90, p95, p99).
- `concurrency_load_test.json`: Multi-tenant load test results (1, 5, 10, 25 users).
- `benchmark_dashboard.html`: Interactive dark mode glassmorphism visualization dashboard.
- `failure_analysis.md`: Detailed defect taxonomy and architectural recommendations.
