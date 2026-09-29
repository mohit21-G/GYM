# Fitness AI Chatbot — 5,000 Test Cases & Benchmark System (v2.0)

**Author:** Antigravity Senior QA Automation & AI Evaluation Team  
**Date:** 2026-09-28  
**Target Environment:** Local Full-Stack (`FastAPI` + `MongoDB Atlas` + `Vite / React` + `Cloudflare Workers AI Llama-3.1-8B-Instruct`)  
**Benchmark Suite Version:** `2.0.0`  

---

## 1. Overview & Objectives

The **Fitness AI Chatbot 5,000 Benchmark System** is a production-grade automated evaluation and stress-testing framework designed to assess the conversational understanding, domain entity extraction, nutritional precision, multi-dialect Indic parsing, multi-tenant isolation, and high-concurrency throughput of the Fitness AI Agent.

### Core Evaluation Dimensions:
1. **Intent Classification Accuracy:** Disambiguating meal logging (`CREATE_FOOD_LOG`), workout logging (`CREATE_ACTIVITY_LOG`), hydration (`CREATE_HYDRATION_LOG`), sleep (`CREATE_SLEEP_LOG`), weight (`CREATE_WEIGHT_LOG`), summary queries (`QUERY_FOOD_LOG`), updates (`UPDATE_FOOD_LOG`), deletions (`DELETE_FOOD_LOG`), and purely conversational questions (`GENERAL_CHAT`).
2. **Indian Regional Food Recognition:** Evaluating 60+ staple dishes across Gujarati, North Indian, South Indian, Maharashtrian, Rajasthani, Bihari, and Bengali regional cuisines.
3. **Multilingual & Phonetic Typo Robustness:** Parsing Gujlish, Hinglish, Romanized Hindi/Gujarati, Native Gujarati script, and Devanagari script, alongside realistic real-world phonetic typos, missing spaces, and colloquial abbreviations.
4. **False-Positive Prevention:** Guaranteeing that nutritional questions (*"How many calories are in 1 roti?"*), hypothetical future actions (*"I might eat pizza tonight"*), negations (*"I did not eat anything yet"*), and advice queries generate **0 food records**.
5. **Fitbit-Style Card Aggregation & Calorie Totals:** Verifying that repeated entries within the same day aggregate into unified food cards with accurate macro summations.
6. **Multi-Tenant User Isolation & Security:** Proving 100% boundary isolation where User B cannot access User A's logs, accompanied by token authentication enforcement and payload validation.
7. **Concurrency & Latency Profiling:** Benchmarking throughput and p50, p90, p95, p99 latencies across 1, 5, 10, and 25 concurrent clients.

---

## 2. Test Suite Distribution (Exactly 5,000 Unique Cases)

The dataset was generated deterministically without trivial duplicates, spanning 12 distinct functional categories:

| Category | Cases | Category ID Prefix | Primary Verification Goal |
| :--- | :---: | :---: | :--- |
| **Indian Food Recognition & Meal Logging** | 1,000 | `IND-` | Broad Indian food database recognition, portion parsing, meal timing |
| **Regional Gujarati, Hindi & Indian Dishes** | 600 | `REG-` | Regional specialties (Kathiyawadi, Surti, Maharashtrian, Bihari, Kashmiri, Andhra) |
| **Multilingual, Transliteration, Typos & Slang** | 600 | `TYP-` | Phonetic typos, dropped vowels, no-space strings, slang numerals (`ek`, `be`, `tran`) |
| **Calories, Protein, Macros & Nutrition Questions** | 500 | `NUT-` | Macro and calorie inquiries without accidental food logging |
| **Exercise & Activity Tracking** | 400 | `ACT-` | Cardio, strength reps, sports, yoga, and MET-based calorie burn estimates |
| **Hydration & Water Tracking** | 300 | `HYD-` | Milliliters, liters, glasses, bottles, and daily progress accumulation |
| **Sleep Tracking** | 250 | `SLP-` | Sleep duration, bedtime/wake times, and recovery advice |
| **Weight & Body Measurement Tracking** | 200 | `WGT-` | Metric (kg) and Imperial (lbs) body weight tracking |
| **Intent Detection & False-Positive Prevention** | 400 | `FPS-` | Zero logging on questions, hypotheticals, negations, and greetings |
| **Context, Follow-ups, Corrections & Memory** | 250 | `CTX-` | Multi-turn updates, deletions, and conversational food summary queries |
| **Food Card Aggregation & Unit Handling** | 200 | `AGG-` | Aggregation of repeat items and diverse culinary units (katoris, bowls, scoops) |
| **API Errors, Security, Persistence & Isolation** | 300 | `SEC-` | 401 unauthorized, 422 validation, injection defense, multi-tenant isolation |
| **TOTAL** | **5,000** | — | **100% Reproducible Dataset** |

---

## 3. Directory Layout & Artifacts

```
benchmark/fitness_ai_v2/
├── test_cases.jsonl             # 5,000 unique test cases in JSON Lines format
├── test_cases.csv               # 5,000 unique test cases in CSV format
├── generate_5000_dataset.py     # Deterministic dataset generation script
├── benchmark_config.json        # Test harness and threshold configuration
├── run_benchmark.py             # Asynchronous high-throughput test runner
├── baseline_results.json        # Pre-fix baseline execution results and metrics
├── final_results.json           # Post-fix final execution results and metrics
├── category_metrics.csv         # Category-level pass rates and latencies
├── latency_report.json          # Latency percentile breakdown (p50, p90, p95, p99)
├── concurrency_load_test.json   # 1, 5, 10, 25 concurrent user benchmark results
├── failure_analysis.md          # Comprehensive root-cause defect analysis
├── regression_report.md         # Pre- vs Post-fix comparative audit
├── benchmark_dashboard.html     # Interactive rich UI visual dashboard
└── README.md                    # Technical documentation and execution guide
```

---

## 4. How to Reproduce & Execute

### Prerequisites:
- Python 3.10+
- Dependencies: `aiohttp`, `numpy`
- Running FastAPI backend on `http://127.0.0.1:3000`

### Commands:
```bash
# 1. Regenerate 5,000 Dataset
python benchmark/fitness_ai_v2/generate_5000_dataset.py

# 2. Run Complete 5,000 Benchmark Suite (Concurrency 10)
python -u benchmark/fitness_ai_v2/run_benchmark.py --mode baseline --concurrency 10

# 3. Run Stratified Sample (e.g., 200 cases)
python -u benchmark/fitness_ai_v2/run_benchmark.py --sample 200 --concurrency 5

# 4. View Interactive Visual Dashboard
# Open benchmark/fitness_ai_v2/benchmark_dashboard.html in any modern browser
```
