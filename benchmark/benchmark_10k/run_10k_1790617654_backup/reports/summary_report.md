# Fitness AI Chatbot — 10,000-Test Benchmark Summary Report

**Run ID**: `run_10k_1790617654`  
**Timestamp**: `2026-09-28T17:47:34.320656+00:00` to `2026-09-28T17:47:39.221493+00:00`  
**Model**: `@cf/meta/llama-3.1-8b-instruct`  
**Backend**: FastAPI + Python 3.14 + MongoDB Atlas  

## Overall Executive Scores

- **Total Cases**: 10,000
- **Strict Pass Accuracy**: **15.11%** (1,511 cases)
- **Total Passing Accuracy (Strict + Partial)**: **22.25%** (2,225 cases)
- **Failed**: 343
- **Infrastructure Errors**: 7432
- **False-Positive Logging Count**: 0
- **User Isolation Failures**: 0 (100% Isolated)
- **p50 Latency**: 237.9 ms
- **p95 Latency**: 2111.3 ms
- **p99 Latency**: 2724.6 ms

## Accuracy by Primary Category

| Category | Total Cases | Passed | Partial | Failed | Strict Pass Rate (%) |
|---|---|---|---|---|---|
| Food Logging | 2,500 | 1,327 | 714 | 343 | 53.08% |
| Hydration | 1,000 | 0 | 0 | 0 | 0.00% |
| Exercise & Activity | 1,000 | 0 | 0 | 0 | 0.00% |
| Weight Tracking | 700 | 0 | 0 | 0 | 0.00% |
| Sleep Tracking | 700 | 0 | 0 | 0 | 0.00% |
| Nutrition & Advice | 900 | 0 | 0 | 0 | 0.00% |
| Intent & False-Positive Prevention | 1,000 | 0 | 0 | 0 | 0.00% |
| Context & Multi-Turn | 800 | 0 | 0 | 0 | 0.00% |
| Aggregation & DB Verification | 700 | 184 | 0 | 0 | 26.29% |
| Edge Cases & Robustness | 700 | 0 | 0 | 0 | 0.00% |

## Accuracy by Language

| Language | Total Cases | Passed | Partial | Failed | Pass Rate (%) |
|---|---|---|---|---|---|
| English | 4,589 | 467 | 166 | 139 | 13.79% |
| Gujlish | 1,459 | 389 | 212 | 3 | 41.19% |
| Hindi | 972 | 85 | 29 | 42 | 11.73% |
| Hinglish | 1,139 | 344 | 208 | 86 | 48.46% |
| Gujarati | 1,141 | 226 | 99 | 73 | 28.48% |
| Code-Mixed / Slang | 700 | 0 | 0 | 0 | 0.00% |
