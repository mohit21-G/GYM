# Fitness AI Chatbot — 10,000-Test Benchmark Summary Report

**Run ID**: `run_10k_1790619102`  
**Suite Execution Time**: `2026-09-28T18:11:42.898300+00:00` to `2026-09-28T18:35:16.327237+00:00`  
**Model Identifier**: `@cf/meta/llama-3.1-8b-instruct`  
**Environment**: FastAPI + Python 3.14 + MongoDB Atlas  

## Overall Executive Scores

- **Total Dataset Cases**: **10,000**
- **Strict Pass Accuracy (All Cases)**: **70.41%** (7,041 cases)
- **Strict Pass Accuracy (Eligible Cases)**: **70.41%** (7,041 / 10,000 cases)
- **Total Passing Accuracy (Strict + Partial)**: **92.27%** (9,227 cases)
- **Failed**: 773
- **Infrastructure Errors**: 0
- **Skipped Cases**: 0
- **False-Positive Logging Count**: 315
- **User Isolation Failures**: 0 (100% Isolated)
- **p50 Latency**: 1147.3 ms
- **p95 Latency**: 2410.1 ms
- **p99 Latency**: 2907.8 ms

## Status Accounting Reconciliation

| Status | Count | Percentage |
|---|---|---|
| **PASS** | 7,041 | 70.41% |
| **PARTIAL_PASS** | 2,186 | 21.86% |
| **FAIL** | 773 | 7.73% |
| **INFRA_ERROR** | 0 | 0.00% |
| **SKIPPED** | 0 | 0.00% |
| **TOTAL** | **10,000** | **100.00%** |

## Accuracy by Primary Category

| Category | Total Cases | Passed | Partial | Failed | Infra | Skipped | Strict Pass Rate (%) |
|---|---|---|---|---|---|---|---|
| Food Logging | 2,500 | 1,115 | 1,028 | 357 | 0 | 0 | 44.60% |
| Hydration | 1,000 | 723 | 277 | 0 | 0 | 0 | 72.30% |
| Exercise & Activity | 1,000 | 972 | 28 | 0 | 0 | 0 | 97.20% |
| Weight Tracking | 700 | 700 | 0 | 0 | 0 | 0 | 100.00% |
| Sleep Tracking | 700 | 392 | 308 | 0 | 0 | 0 | 56.00% |
| Nutrition & Advice | 900 | 900 | 0 | 0 | 0 | 0 | 100.00% |
| Intent & False-Positive Prevention | 1,000 | 738 | 0 | 262 | 0 | 0 | 73.80% |
| Context & Multi-Turn | 800 | 732 | 68 | 0 | 0 | 0 | 91.50% |
| Aggregation & DB Verification | 700 | 450 | 186 | 64 | 0 | 0 | 64.29% |
| Edge Cases & Robustness | 700 | 319 | 291 | 90 | 0 | 0 | 45.57% |

## Accuracy by Language

| Language | Total Cases | Passed | Partial | Failed | Infra | Skipped | Strict Pass Rate (%) |
|---|---|---|---|---|---|---|---|
| English | 4,589 | 3,746 | 474 | 369 | 0 | 0 | 81.63% |
| Gujlish | 1,459 | 961 | 461 | 37 | 0 | 0 | 65.87% |
| Hindi | 972 | 594 | 299 | 79 | 0 | 0 | 61.11% |
| Hinglish | 1,139 | 790 | 261 | 88 | 0 | 0 | 69.36% |
| Gujarati | 1,141 | 631 | 400 | 110 | 0 | 0 | 55.30% |
| Code-Mixed / Slang | 700 | 319 | 291 | 90 | 0 | 0 | 45.57% |
