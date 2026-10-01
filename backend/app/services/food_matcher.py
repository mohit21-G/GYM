"""
food_matcher.py
---------------
FitBot input normalization and fuzzy food/exercise matching pipeline.

Pipeline per item:
  raw text
    -> normalize()          strip emojis, lowercase, fix spacing
    -> extract_quantity()   parse "2 rotli", "200g paneer", "ek bowl"
    -> synonym lookup       local names -> canonical DB names (from synonyms.json)
    -> exact match          check CANONICAL_INDIAN_FOOD_PROFILES or exercise list
    -> rapidfuzz WRatio     fuzzy match against in-memory corpus
    -> LLM fallback         only for confirm/not_found (called by caller, not here)

Match statuses returned:
  "matched"   score >= 85  — use directly, no question
  "confirm"   60-85        — return top 3 suggestions for user choice
  "not_found" < 60         — return up to 3 closest if any
"""

from __future__ import annotations

import json
import logging
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rapidfuzz import fuzz, process as fuzz_process

logger = logging.getLogger("food_matcher")

# ---------------------------------------------------------------------------
# Load synonyms from JSON (extend without touching code)
# ---------------------------------------------------------------------------
_SYNONYMS_PATH = Path(__file__).parent.parent / "data" / "synonyms.json"

def _load_synonyms() -> Tuple[Dict[str, str], Dict[str, str]]:
    """Load food and exercise synonym dicts from synonyms.json."""
    try:
        data = json.loads(_SYNONYMS_PATH.read_text(encoding="utf-8"))
        food_syns: Dict[str, str] = {k.lower(): v for k, v in data.get("food", {}).items()}
        ex_syns: Dict[str, str] = {k.lower(): v for k, v in data.get("exercise", {}).items()}
        logger.info("Loaded synonyms: %d food, %d exercise", len(food_syns), len(ex_syns))
        return food_syns, ex_syns
    except Exception as exc:
        logger.error("Could not load synonyms.json: %s", exc)
        return {}, {}

FOOD_SYNONYMS, EXERCISE_SYNONYMS = _load_synonyms()

# ---------------------------------------------------------------------------
# Number words (Hinglish / Gujlish / English)
# ---------------------------------------------------------------------------
_NUMBER_WORDS: Dict[str, float] = {
    "one": 1.0, "two": 2.0, "three": 3.0, "four": 4.0, "five": 5.0,
    "six": 6.0, "seven": 7.0, "eight": 8.0, "nine": 9.0, "ten": 10.0,
    "half": 0.5, "adhu": 0.5, "adho": 0.5, "aadha": 0.5, "adha": 0.5,
    "ek": 1.0, "be": 2.0, "tran": 3.0, "traan": 3.0, "char": 4.0,
    "panch": 5.0, "chha": 6.0, "sat": 7.0, "aath": 8.0, "nav": 9.0,
    "das": 10.0, "dedh": 1.5, "dhai": 2.5, "dhedh": 1.5,
    "do": 2.0, "teen": 3.0, "tin": 3.0, "chaar": 4.0, "paanch": 5.0,
}

# ---------------------------------------------------------------------------
# Unit normalization
# ---------------------------------------------------------------------------
_UNIT_MAP: Dict[str, str] = {
    "katori": "bowl", "katoris": "bowl", "vatki": "bowl", "vaatki": "bowl",
    "bowl": "bowl", "bowls": "bowl", "katora": "bowl",
    "cup": "cup", "cups": "cup", "kapp": "cup", "kap": "cup",
    "glass": "glass", "glasses": "glass", "glaas": "glass", "gls": "glass",
    "plate": "plate", "plates": "plate", "thaali": "plate", "plet": "plate",
    "piece": "piece", "pieces": "piece", "pcs": "piece", "pc": "piece",
    "nag": "piece", "tukda": "piece", "slice": "slice", "slices": "slice",
    "scoop": "scoop", "scoops": "scoop", "skup": "scoop",
    "spoon": "tbsp", "chamach": "tbsp", "chamchi": "tbsp", "chamcho": "tbsp",
    "tablespoon": "tbsp", "tablespoons": "tbsp", "tbsp": "tbsp",
    "teaspoon": "tsp", "teaspoons": "tsp", "tsp": "tsp",
    "ml": "ml", "liter": "l", "litre": "l", "ltr": "l", "l": "l",
    "gram": "g", "grams": "g", "g": "g", "kg": "kg",
    "bottle": "bottle", "bottles": "bottle",
    "serving": "serving", "servings": "serving",
}

# ---------------------------------------------------------------------------
# In-memory corpus caches (rebuilt on demand, thread-safe enough for single-
# process Uvicorn workers; if multi-process, each worker builds its own copy)
# ---------------------------------------------------------------------------
class _CorpusCache:
    food_names: List[str] = []          # canonical names from DB + profiles
    exercise_names: List[str] = []      # canonical exercise names
    food_dirty: bool = True             # rebuild needed
    exercise_dirty: bool = True

_cache = _CorpusCache()


def invalidate_food_cache() -> None:
    """Call this whenever a new food is added to the DB."""
    _cache.food_dirty = True
    logger.debug("Food corpus cache invalidated")


def _get_food_corpus() -> List[str]:
    """Return (and lazily build) the in-memory food name corpus."""
    if not _cache.food_dirty and _cache.food_names:
        return _cache.food_names

    # Import here to avoid circular imports
    from .food_service import CANONICAL_INDIAN_FOOD_PROFILES  # type: ignore

    names = list(CANONICAL_INDIAN_FOOD_PROFILES.keys())
    # Also add all synonym targets so fuzzy matching can reach them
    names += list(set(FOOD_SYNONYMS.values()))
    _cache.food_names = list(dict.fromkeys(names))   # deduplicate, preserve order
    _cache.food_dirty = False
    logger.debug("Food corpus rebuilt: %d entries", len(_cache.food_names))
    return _cache.food_names


def _get_exercise_corpus() -> List[str]:
    """Return the in-memory exercise name corpus."""
    if not _cache.exercise_dirty and _cache.exercise_names:
        return _cache.exercise_names

    base = [
        "push-ups", "pull-ups", "sit-ups", "squats", "lunges", "crunches",
        "plank", "burpees", "jumping jacks", "jump rope", "bench press",
        "deadlifts", "running", "jogging", "walking", "cycling", "swimming",
        "yoga", "gym workout", "strength training", "HIIT", "zumba", "dancing",
        "pilates", "stretching", "badminton", "cricket", "football",
    ]
    names = base + list(set(EXERCISE_SYNONYMS.values()))
    _cache.exercise_names = list(dict.fromkeys(names))
    _cache.exercise_dirty = False
    return _cache.exercise_names


# ---------------------------------------------------------------------------
# Text normalization helpers
# ---------------------------------------------------------------------------
_EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"   # emoticons
    "\U0001F300-\U0001F5FF"   # symbols & pictographs
    "\U0001F680-\U0001F6FF"   # transport
    "\U0001F1E0-\U0001F1FF"   # flags
    "\U00002700-\U000027BF"   # dingbats
    "\U000024C2-\U0001F251"
    "]+",
    flags=re.UNICODE,
)

# Indic digit mapping (Gujarati + Devanagari)
_INDIC_DIGITS: Dict[str, str] = {
    "૦": "0", "૧": "1", "૨": "2", "૩": "3", "૪": "4",
    "૫": "5", "૬": "6", "૭": "7", "૮": "8", "૯": "9",
    "०": "0", "१": "1", "२": "2", "३": "3", "४": "4",
    "५": "5", "६": "6", "७": "7", "८": "8", "९": "9",
}


def normalize(text: str) -> str:
    """
    Normalize raw user input:
      - Convert Indic digits to ASCII
      - Strip emojis and non-printable characters
      - Lowercase, collapse whitespace
      - Separate fused digit+word tokens ("2rotli" -> "2 rotli")
      - Fix common single-word typos via synonym keys (cheap, no regex loop)

    Returns the cleaned string. Does NOT extract quantity.
    """
    if not text:
        return ""

    # Indic digits
    t = "".join(_INDIC_DIGITS.get(ch, ch) for ch in text)

    # NFC normalization (important for Gujarati/Devanagari)
    t = unicodedata.normalize("NFC", t)

    # Strip emojis
    t = _EMOJI_RE.sub(" ", t)

    # Remove non-printable / control characters except newlines
    t = "".join(ch if ch.isprintable() or ch == "\n" else " " for ch in t)

    # Lowercase
    t = t.lower()

    # Separate fused digit+letter tokens ("2rotli" -> "2 rotli", "500ml" -> "500 ml")
    t = re.sub(r"(\d+(?:\.\d+)?)([a-z\u0A80-\u0AFF\u0900-\u097F]+)", r"\1 \2", t)
    t = re.sub(r"([a-z\u0A80-\u0AFF\u0900-\u097F]+)(\d+)", r"\1 \2", t)

    # Collapse multiple spaces / trim
    t = re.sub(r"[ \t]+", " ", t).strip()

    return t


def extract_quantity(text: str) -> Tuple[Optional[float], Optional[str], str]:
    """
    Parse quantity and unit from a normalized item string.

    Examples:
      "2 rotli"            -> (2.0, None,    "rotli")
      "1 bowl rice"        -> (1.0, "bowl",  "rice")
      "200g paneer"        -> (200.0, "g",   "paneer")
      "ek katori dal"      -> (1.0, "bowl",  "dal")
      "half glass chaas"   -> (0.5, "glass", "chaas")
      "pushap 20 min"      -> (20.0, "min",  "pushap")

    Returns (quantity, unit, remaining_text).
    quantity is None if not found (caller should assume 1 serving).
    unit is None if no unit token was found.
    """
    t = text.strip()
    qty: Optional[float] = None
    unit: Optional[str] = None

    # 1. Try number-word at start ("ek", "be", "half", ...)
    for word, val in sorted(_NUMBER_WORDS.items(), key=lambda x: -len(x[0])):
        pattern = rf"^{re.escape(word)}\b"
        if re.match(pattern, t, re.IGNORECASE):
            qty = val
            t = t[len(word):].strip()
            break

    # 2. Try numeric value (int or float) at start
    if qty is None:
        m = re.match(r"^(\d+(?:\.\d+)?)\s*", t)
        if m:
            qty = float(m.group(1))
            t = t[m.end():].strip()

    # 3. Try unit immediately after quantity (or at start if no qty yet)
    tokens = t.split()
    if tokens:
        candidate = tokens[0].lower().rstrip("s")  # naive deplural
        # Check both with-s and without-s
        raw_unit = tokens[0].lower()
        mapped = _UNIT_MAP.get(raw_unit) or _UNIT_MAP.get(candidate)
        # Special case: "min" / "mins" / "minutes" for exercise
        if raw_unit in ("min", "mins", "minute", "minutes"):
            mapped = "min"
        if mapped:
            unit = mapped
            t = " ".join(tokens[1:]).strip()

    # 4. If still no qty but a trailing number exists ("paneer 100g")
    if qty is None:
        m = re.search(r"\b(\d+(?:\.\d+)?)\s*(g|kg|ml|l)\b", t)
        if m:
            qty = float(m.group(1))
            raw_u = m.group(2).lower()
            unit = _UNIT_MAP.get(raw_u, raw_u)
            t = (t[:m.start()] + t[m.end():]).strip()

    return qty, unit, t


# ---------------------------------------------------------------------------
# LLM-corrected name cache (typo -> corrected name)
# ---------------------------------------------------------------------------
_llm_correction_cache: Dict[str, str] = {}


def get_llm_cache(typo: str) -> Optional[str]:
    """Return a previously LLM-corrected name for *typo*, or None."""
    return _llm_correction_cache.get(typo.lower())


def set_llm_cache(typo: str, corrected: str) -> None:
    """Store an LLM correction so the same typo never calls the LLM again."""
    _llm_correction_cache[typo.lower()] = corrected
    logger.debug("LLM cache: '%s' -> '%s'", typo, corrected)


# ---------------------------------------------------------------------------
# Core match result type
# ---------------------------------------------------------------------------
class MatchResult:
    """Result of a single food or exercise match attempt."""

    __slots__ = ("status", "matched_name", "score", "suggestions", "original")

    def __init__(
        self,
        status: str,                       # "matched" | "confirm" | "not_found"
        original: str,
        matched_name: Optional[str] = None,
        score: float = 0.0,
        suggestions: Optional[List[str]] = None,
    ) -> None:
        self.status = status
        self.original = original
        self.matched_name = matched_name
        self.score = score
        self.suggestions = suggestions or []

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"MatchResult(status={self.status!r}, matched={self.matched_name!r}, "
            f"score={self.score:.1f}, original={self.original!r})"
        )


# ---------------------------------------------------------------------------
# Public fuzzy match functions
# ---------------------------------------------------------------------------

def match_food(query: str) -> MatchResult:
    """
    Match a single food name string against the food corpus.

    Pipeline:
      1. normalize()
      2. Synonym lookup (exact key match on lowercased query)
      3. Exact match against corpus
      4. rapidfuzz WRatio scoring
         >= 85 -> matched
         60-85 -> confirm (top 3)
          < 60 -> not_found (top 3 if any >= 30)

    Args:
        query: Raw or pre-normalized food name string.

    Returns:
        MatchResult with status, matched_name, score, suggestions.
    """
    if not query or not query.strip():
        return MatchResult("not_found", query)

    normalized_q = normalize(query)
    corpus = _get_food_corpus()

    # --- Step 1: Synonym lookup ---
    syn = FOOD_SYNONYMS.get(normalized_q)
    if syn:
        logger.debug("Synonym hit: '%s' -> '%s'", normalized_q, syn)
        return MatchResult("matched", query, matched_name=syn, score=100.0)

    # Try multi-word synonym after stripping leading quantity tokens
    _, _, name_only = extract_quantity(normalized_q)
    syn2 = FOOD_SYNONYMS.get(name_only)
    if syn2:
        logger.debug("Synonym hit (name_only): '%s' -> '%s'", name_only, syn2)
        return MatchResult("matched", query, matched_name=syn2, score=100.0)

    # --- Step 2: LLM cache check ---
    cached = get_llm_cache(normalized_q)
    if cached:
        return MatchResult("matched", query, matched_name=cached, score=95.0)

    # --- Step 3: Exact case-insensitive match against corpus ---
    lower_corpus = [c.lower() for c in corpus]
    try:
        idx = lower_corpus.index(normalized_q)
        return MatchResult("matched", query, matched_name=corpus[idx], score=100.0)
    except ValueError:
        pass
    try:
        idx = lower_corpus.index(name_only)
        return MatchResult("matched", query, matched_name=corpus[idx], score=100.0)
    except ValueError:
        pass

    # --- Step 4: rapidfuzz WRatio ---
    # Use WRatio which handles partial matches, transpositions, and token order
    results = fuzz_process.extract(
        normalized_q, corpus, scorer=fuzz.WRatio, limit=5
    )
    # results: list of (match, score, index)
    if not results:
        return MatchResult("not_found", query)

    best_name, best_score, _ = results[0]

    if best_score >= 85:
        logger.debug("Fuzzy matched: '%s' -> '%s' (%.1f)", normalized_q, best_name, best_score)
        return MatchResult("matched", query, matched_name=best_name, score=best_score)

    top3 = [r[0] for r in results[:3]]

    if best_score >= 60:
        logger.debug(
            "Fuzzy confirm: '%s' -> top3=%s (best=%.1f)", normalized_q, top3, best_score
        )
        return MatchResult(
            "confirm", query, matched_name=best_name, score=best_score, suggestions=top3
        )

    # Only surface suggestions if they have at least a weak signal
    weak = [r[0] for r in results[:3] if r[1] >= 30]
    logger.debug("No match: '%s' (best=%.1f)", normalized_q, best_score)
    return MatchResult("not_found", query, score=best_score, suggestions=weak)


def match_exercise(query: str) -> MatchResult:
    """
    Match a single exercise name string against the exercise corpus.

    Same pipeline as match_food but uses EXERCISE_SYNONYMS and exercise corpus.

    Args:
        query: Raw or pre-normalized exercise name string.

    Returns:
        MatchResult with status, matched_name, score, suggestions.
    """
    if not query or not query.strip():
        return MatchResult("not_found", query)

    normalized_q = normalize(query)
    corpus = _get_exercise_corpus()

    # Synonym lookup
    syn = EXERCISE_SYNONYMS.get(normalized_q)
    if syn:
        logger.debug("Exercise synonym: '%s' -> '%s'", normalized_q, syn)
        return MatchResult("matched", query, matched_name=syn, score=100.0)

    _, _, name_only = extract_quantity(normalized_q)
    syn2 = EXERCISE_SYNONYMS.get(name_only)
    if syn2:
        return MatchResult("matched", query, matched_name=syn2, score=100.0)

    # Exact match
    lower_corpus = [c.lower() for c in corpus]
    try:
        idx = lower_corpus.index(normalized_q)
        return MatchResult("matched", query, matched_name=corpus[idx], score=100.0)
    except ValueError:
        pass

    # Fuzzy
    results = fuzz_process.extract(
        normalized_q, corpus, scorer=fuzz.WRatio, limit=5
    )
    if not results:
        return MatchResult("not_found", query)

    best_name, best_score, _ = results[0]

    if best_score >= 85:
        return MatchResult("matched", query, matched_name=best_name, score=best_score)

    top3 = [r[0] for r in results[:3]]

    if best_score >= 60:
        return MatchResult(
            "confirm", query, matched_name=best_name, score=best_score, suggestions=top3
        )

    weak = [r[0] for r in results[:3] if r[1] >= 30]
    return MatchResult("not_found", query, score=best_score, suggestions=weak)


# ---------------------------------------------------------------------------
# Absurd quantity guard
# ---------------------------------------------------------------------------

_ABSURD_LIMITS: Dict[str, float] = {
    # food items where very high counts are implausible
    "roti": 15.0,
    "chapati": 15.0,
    "phulka": 20.0,
    "thepla": 20.0,
    "rotli": 15.0,
    "bhakri": 10.0,
    "paratha": 10.0,
    "egg": 20.0,
    "banana": 10.0,
    "apple": 8.0,
    "idli": 20.0,
    "samosa": 10.0,
    # exercise duration (minutes)
    "running": 300.0,
    "walking": 600.0,
    "gym workout": 300.0,
    "cycling": 480.0,
    "swimming": 300.0,
}
_DEFAULT_FOOD_MAX = 30.0
_DEFAULT_EXERCISE_MAX_MIN = 600.0   # 10 hours


def is_absurd_quantity(name: str, quantity: float, item_type: str = "food") -> bool:
    """
    Return True if the quantity looks implausible for the given item.

    Args:
        name:      Canonical or raw food/exercise name.
        quantity:  Parsed quantity value.
        item_type: "food" or "exercise".

    Returns:
        True if absurd (caller should ask for confirmation instead of logging).
    """
    if quantity <= 0:
        return True
    lower = name.lower()
    for key, limit in _ABSURD_LIMITS.items():
        if key in lower:
            return quantity > limit
    if item_type == "food":
        return quantity > _DEFAULT_FOOD_MAX
    # exercise: treat as minutes unless it's reps
    return quantity > _DEFAULT_EXERCISE_MAX_MIN


# ---------------------------------------------------------------------------
# LLM JSON correction parser (used by ai_service for fallback items)
# ---------------------------------------------------------------------------

_LLM_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)
_LLM_FIRST_BRACE_RE = re.compile(r"\{[\s\S]*\}")
_LLM_THINK_RE = re.compile(r"<think>[\s\S]*?</think>", re.IGNORECASE)


def parse_llm_json(raw: str) -> Optional[Dict[str, Any]]:
    """
    Safely extract the first JSON object from a raw LLM response.

    Handles:
      - <think>...</think> reasoning blocks (GLM 4.7 / DeepSeek style)
      - ```json ... ``` fences
      - Leading/trailing prose around the JSON object
      - Invalid JSON (returns None)

    Args:
        raw: Raw string output from the LLM.

    Returns:
        Parsed dict, or None if extraction/parsing fails.
    """
    if not raw:
        return None

    # Remove reasoning blocks
    cleaned = _LLM_THINK_RE.sub("", raw).strip()

    # Try fenced block first
    fence_match = _LLM_JSON_FENCE_RE.search(cleaned)
    if fence_match:
        candidate = fence_match.group(1).strip()
    else:
        # Find first { ... } block
        brace_match = _LLM_FIRST_BRACE_RE.search(cleaned)
        if not brace_match:
            logger.debug("parse_llm_json: no JSON object found in: %.120s", raw)
            return None
        candidate = brace_match.group(0)

    try:
        parsed = json.loads(candidate)
        if not isinstance(parsed, dict):
            return None
        # Ensure entities key exists (used by ai_service)
        if "entities" not in parsed:
            parsed["entities"] = {}
        return parsed
    except json.JSONDecodeError as exc:
        logger.debug("parse_llm_json decode error: %s | candidate=%.120s", exc, candidate)
        return None
