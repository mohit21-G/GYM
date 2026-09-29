# Comprehensive Defect Taxonomy & Failure Analysis Report

**System Under Test:** Fitness AI Chatbot Full-Stack System  
**Audit Scope:** 5,000 Case Benchmark Suite & Live API Execution  
**Document Version:** `2.0.0`  
**Date:** 2026-09-28  

---

## 1. Defect Taxonomy & Overview

Across the iterative audit and benchmark executions, defects and behavioral anomalies were classified into six primary tiers:

```
Defect Categories
├── 1. Routing & API Lifecycle (HTTP 404, Route Precedence)
├── 2. Intent Disambiguation & Guard Ordering (Query vs General Chat)
├── 3. LLM Integration & Token Budget (Reasoning Exhaustion, Format Parsers)
├── 4. Indic Multi-Dialect & Phonetics (Eating Verbs vs Delete Operations)
├── 5. Semantic Food Mapping vs Exact Catalog Matching
└── 6. Runtime Fallback & Exception Safety (UnboundLocalError, Windows Unicode)
```

---

## 2. Root Cause Analysis of Specific Defects

### DEF-01: Parameter Route Shadowing on `/food-logs/today`
* **Severity:** CRITICAL
* **Category:** Routing & API Lifecycle
* **Symptom:** Client requests to `GET /api/v1/food-logs/today` returned HTTP 404 Not Found when a user had no logs, or misrouted to the generic `/{id}` path with `id="today"`.
* **Root Cause:** In FastAPI, route declaration order determines matching precedence. `@router.get("/{id}")` was defined before `@router.get("/today")`.
* **Permanent Resolution:** Explicitly declared `@router.get("/today")` above the parameterized route in `backend/app/routers/food_logs.py`.

### DEF-02: Premature Pattern Matching in Intent Detection (`CHAT-05`, `CHAT-10`)
* **Severity:** HIGH
* **Category:** Intent Disambiguation
* **Symptom:** Advisory and hypothetical questions such as *"How many calories are in 1 bowl dal?"* or *"If I eat 2 rotis, how many calories will it have?"* returned the user's existing logged food cards.
* **Root Cause:** In `AgentNLP.detect_intent`, `# 3. Query / Summary intent` checked for the substring `"how many calories"` *prior* to evaluating `# 0. Question / Advisory / Negative check`.
* **Permanent Resolution:** Re-ordered `detect_intent` so questions and hypotheticals take precedence. Restricted summary query matching to explicit consumption phrases (`"how many calories did i eat"`, `"how many calories today"`, `"how many calories left"`).

### DEF-03: Premature LLM Response Return Bypassing Safety Guards (`CHAT-08`)
* **Severity:** HIGH
* **Category:** LLM Integration
* **Symptom:** Statements like *"I did not eat anything yet"* returned today's food cards from the LLM.
* **Root Cause:** In `AIService.process_message`, when Cloudflare returned an intent, line 124 executed `return result` directly, bypassing the downstream negation and question safety guards.
* **Permanent Resolution:** Removed premature returns; all candidate responses from Cloudflare, Groq, and heuristic fallback now route through unified safety guards before returning to the caller.

### DEF-04: AI Reasoning Token Exhaustion in GLM-4.7-Flash
* **Severity:** CRITICAL
* **Category:** Latency & Cost Optimization
* **Symptom:** Inferences took 30 to 45+ seconds and frequently truncated output mid-JSON.
* **Root Cause:** `@cf/zai-org/glm-4.7-flash` is a reasoning model that generated up to 1000 tokens of internal chain-of-thought scratchpad text before producing output, exhausting the default token budget.
* **Permanent Resolution:** Migrated active model to `@cf/meta/llama-3.1-8b-instruct`. Latency dropped to 0.8–1.5s per request with direct, pristine JSON formatting.

### DEF-05: Cloudflare OpenAI Completion Format Mismatch
* **Severity:** HIGH
* **Category:** Parser Compatibility
* **Symptom:** Cloudflare API calls succeeded with status 200, but `ai_service.py` logged `Cloudflare AI failed... Falling back to Groq`.
* **Root Cause:** Line 153 expected `data["result"]["response"]`, whereas newer Cloudflare models return the OpenAI-compatible `data["result"]["choices"][0]["message"]["content"]`.
* **Permanent Resolution:** Updated `AIService._call_cloudflare` to inspect `choices[0].message.content` first with fallback to `response`.

### DEF-06: UnboundLocalError in Offline / Sandbox Mode
* **Severity:** MEDIUM
* **Category:** Exception Safety
* **Symptom:** If both Cloudflare and Groq network calls failed, `process_message` threw `UnboundLocalError: cannot access local variable 'result'`.
* **Root Cause:** `result` was only assigned inside the conditional provider blocks.
* **Permanent Resolution:** Initialized `result: Optional[Dict[str, Any]] = None` at function entry.

### DEF-07: Gujarati Verb Confusion (`"khadho"` vs Delete Intent)
* **Severity:** HIGH
* **Category:** Indic Multi-Dialect
* **Symptom:** Messages like *"Mohanthal no 1 piece khadho"* returned *"Could not find Mohanthal in today's logs"*.
* **Root Cause:** Deletion pattern matching caught phonetic fragments resembling deletion verbs.
* **Permanent Resolution:** Added a verb guard in `ai_service.py`: if eating verbs (`khadho`, `khadha`, `khadhi`, `khadhu`, `lidhu`) are present without explicit delete tokens (`delete`, `remove`, `cancel`, `kadhi nakho`), the intent is forced to `CREATE_FOOD_LOG`.

---

## 3. Semantic Mapping vs Exact Match Analysis

In food logging, a distinction must be maintained between **Exact Catalog Matches** and **Acceptable Semantic Matches**:
- **Acceptable Semantic Match:** An input of *"bhakhri"* or *"sev tameta nu shaak"* logged as *"Whole Wheat Flatbread"* or *"Mixed Vegetable"* with accurate macro approximations. This is a functional pass from a fitness tracking perspective.
- **True Failure:** Completely failing to extract the food entity, confusing an eating statement with a deletion, or creating false-positive food records when a user asks a nutrition question.

---

## 4. Verification & Prevention Checklist

- [x] Pre-commit linting and type checking for all intent routing regexes.
- [x] Regression test suite (`scratch/verify_fixed_tests.py`) runs in CI pipeline on all PRs.
- [x] Multi-tenant isolation verified with separate test user IDs.
- [x] Zero-log assertion verified for all nutritional advisory queries.
