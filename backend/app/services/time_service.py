import re
import zoneinfo
from datetime import datetime, date, timedelta, timezone
from typing import Optional, Tuple, Dict, Any

APP_TIMEZONE = "Asia/Kolkata"
DEFAULT_TIMEZONE = APP_TIMEZONE

INDIC_DIGIT_MAP = {
    '૦': '0', '૧': '1', '૨': '2', '૩': '3', '૪': '4',
    '૫': '5', '૬': '6', '૭': '7', '૮': '8', '૯': '9',
    '०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
    '५': '5', '६': '6', '७': '7', '८': '8', '९': '9',
}

class TimeService:
    _mock_now: Optional[datetime] = None

    @classmethod
    def set_mock_now(cls, mock_dt: Optional[datetime]) -> None:
        """Injects a fake/frozen datetime for deterministic testing without wall-clock dependency."""
        cls._mock_now = mock_dt

    @classmethod
    def reset_mock_now(cls) -> None:
        """Resets the injected mock datetime back to real wall-clock time."""
        cls._mock_now = None

    @staticmethod
    def get_timezone(tz_name: Optional[str] = None) -> zoneinfo.ZoneInfo:
        try:
            return zoneinfo.ZoneInfo(tz_name or DEFAULT_TIMEZONE)
        except Exception:
            return zoneinfo.ZoneInfo(DEFAULT_TIMEZONE)

    @classmethod
    def get_current_local_datetime(cls, tz_name: Optional[str] = None) -> datetime:
        """
        Centralized Single Source of Truth for local datetime.
        Always returns a timezone-aware datetime in Asia/Kolkata (or user tz).
        Supports injected mock clock for deterministic testing.
        """
        tz = cls.get_timezone(tz_name)
        if cls._mock_now is not None:
            dt = cls._mock_now
            if dt.tzinfo is None:
                return dt.replace(tzinfo=tz)
            return dt.astimezone(tz)
        return datetime.now(tz)

    @classmethod
    def get_current_local_time(cls, tz_name: Optional[str] = None) -> datetime:
        """Alias to get_current_local_datetime."""
        return cls.get_current_local_datetime(tz_name)

    @classmethod
    def get_current_local_date_str(cls, tz_name: Optional[str] = None) -> str:
        """Returns the current local calendar date string YYYY-MM-DD in Asia/Kolkata."""
        return cls.get_current_local_datetime(tz_name).strftime("%Y-%m-%d")

    @classmethod
    def get_message_date_context(
        cls,
        text: str,
        tz_name: Optional[str] = None,
    ) -> Tuple[str, bool, bool]:
        """Analyse *text* for relative/absolute date words and return a 3-tuple:

        ``(log_date_str, is_past, is_future)``

        * ``log_date_str``  – YYYY-MM-DD string in Asia/Kolkata for the resolved date.
        * ``is_past``       – True when the resolved date is strictly before today.
        * ``is_future``     – True when the resolved date is strictly after today.

        Uses ``parse_date_from_text`` internally so all language variants (English,
        Hindi, Gujarati, Gujlish including "kale", "kal", future conjugations) are
        handled in one place.

        Examples::

            "kal maine 2 roti khadhi"  →  (yesterday_str, True, False)
            "kale karish"              →  (tomorrow_str, False, True)
            "tomorrow I will eat"      →  (tomorrow_str, False, True)
            "aaj poha khadha"          →  (today_str, False, False)
            "2 roti khadhi"            →  (today_str, False, False)
        """
        today = cls.get_current_local_datetime(tz_name).date()
        resolved, _ = cls.parse_date_from_text(text, reference_date=today)
        log_date_str = resolved.strftime("%Y-%m-%d")
        is_past = resolved < today
        is_future = resolved > today
        return log_date_str, is_past, is_future

    @staticmethod
    def normalize_indic_digits(text: str) -> str:
        """Translates Gujarati and Devanagari numerals to standard ASCII digits."""
        res = []
        for ch in text:
            res.append(INDIC_DIGIT_MAP.get(ch, ch))
        return "".join(res)

    @staticmethod
    def parse_date_from_text(text: str, reference_date: Optional[date] = None) -> Tuple[date, bool]:
        """
        Parses explicit calendar date references from text across languages.
        Supports:
        - Relative dates: today, yesterday, tomorrow (in English, Gujarati, Hindi, Hinglish, Gujlish)
        - Indian numeric format: DD/MM/YYYY or DD-MM-YYYY (e.g. 30/09/2026, 03/04/2026 -> 3rd April)
        - Standard ISO format: YYYY-MM-DD (e.g. 2026-09-30)
        Returns (resolved_date, has_explicit_date).
        """
        ref_d = reference_date or TimeService.get_current_local_datetime().date()
        norm = TimeService.normalize_indic_digits(text)
        lower = norm.lower()

        # 1. ISO format: YYYY-MM-DD
        m_iso = re.search(r"\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b", lower)
        if m_iso:
            try:
                y = int(m_iso.group(1))
                m = int(m_iso.group(2))
                d = int(m_iso.group(3))
                return date(y, m, d), True
            except Exception:
                pass

        # 2. Indian numeric format: DD/MM/YYYY or DD-MM-YYYY
        m_in = re.search(r"\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})\b", lower)
        if m_in:
            try:
                d = int(m_in.group(1))
                m = int(m_in.group(2))
                y = int(m_in.group(3))
                return date(y, m, d), True
            except Exception:
                pass

        # 3. Yesterday / Gaya kale / Gai kale / Kal (past context)
        if any(w in lower for w in [
            "yesterday", "gaya kale", "gaye kale", "gai kale", "gayakale", "gaikale",
            "ગઈકાલે", "ગઈ કાલે", "ગયા કાલે", "ગયાકાલે", "બીતે કલ"
        ]):
            return ref_d - timedelta(days=1), True

        # ---------- "kale" disambiguation (Latin-script Gujarati) ----------
        # "kale" is used both for past ("kal maine khaya") and future ("kale karish").
        # Detect future conjugation markers BEFORE deciding direction.
        #
        # Future markers in Gujlish / Gujarati: khaysh, khais, khaish, karish, karis,
        #   jais, jaish, jayish, piysh, piish, piyish, karish, karunga, karega, jaunga,
        #   aavti, aavtikale — and Gujarati future suffix -ish / -sh on a verb.
        _FUTURE_MARKERS = (
            "khaysh", "khais", "khaish", "khayish",        # khava future
            "karish", "karis", "karaish", "karayish",       # karva future
            "jais", "jaish", "jayish", "jaayish",           # java future
            "piysh", "piish", "piyish", "piyaish",          # pivanu future
            "karunga", "karunga", "karega", "karengi",       # Hindi future
            "jaunga", "jaungi", "jayega", "jayegi",          # Hindi future
            "khaunga", "khaungi", "khayega", "khayegi",      # Hindi future
            "aavti", "aavtikale", "aane wala", "aane wali",  # tomorrow markers
            "aavtikale", "aavti kale",
            "આવતી", "આવતીકાલે", "कल करूंगा", "कल जाऊंगा",
        )

        if re.search(r"\b(?:kale|kal)\b", lower):
            if any(fm in lower for fm in _FUTURE_MARKERS):
                return ref_d + timedelta(days=1), True
            else:
                return ref_d - timedelta(days=1), True

        # ---------- bare "kal" in Devanagari / Gujarati script ----------
        if re.search(r"\b(?:કાલ|कल)\b", lower):
            if any(fm in lower for fm in _FUTURE_MARKERS):
                return ref_d + timedelta(days=1), True
            else:
                return ref_d - timedelta(days=1), True

        # 4. Unambiguous tomorrow
        if any(w in lower for w in [
            "tomorrow", "aavti kale", "aavtikale", "આવતીકાલે", "આવતી કાલે", "कल सुबह"
        ]):
            return ref_d + timedelta(days=1), True

        # 5. Today / Aaje / Aaj
        if any(w in lower for w in ["today", "aaj", "aaje", "આજે", "આજ", "आज"]):
            return ref_d, True

        return ref_d, False

    @staticmethod
    def parse_explicit_or_relative_time(
        text: str,
        reference_time: Optional[datetime] = None,
        tz_name: Optional[str] = None
    ) -> datetime:
        """Parses explicit user time, relative offset, or falls back to current local clock time."""
        dt, _ = TimeService.extract_time_from_text(text, reference_time, tz_name)
        return dt

    @staticmethod
    def extract_time_from_text(
        text: str,
        reference_time: Optional[datetime] = None,
        tz_name: Optional[str] = None
    ) -> Tuple[datetime, bool]:
        """
        Extracts explicit user time or relative offset from text across English, Hindi, Gujarati, Hinglish, Gujlish.
        Returns (resolved_datetime, has_explicit_time).
        If no explicit time or offset is found, returns (current_local_time, False).
        """
        tz = TimeService.get_timezone(tz_name)
        ref = reference_time or TimeService.get_current_local_datetime(tz_name)
        if ref.tzinfo is None:
            ref = ref.replace(tzinfo=tz)
        else:
            ref = ref.astimezone(tz)

        norm = TimeService.normalize_indic_digits(text)
        lower = norm.lower()

        # Step 1: Check for relative time expressions (e.g. "2 hours ago", "30 minutes ago", "1 day ago")
        # Supports English, Gujarati (pahela / પહેલા), Hindi (pehle / पहले)
        m_rel_hr = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:hours?|hrs?|hr|કલાક|घंटे|घंटा)\s*(?:ago|pahela|pehle|પહેલા|પહેલાં|पहले)\b", lower)
        if m_rel_hr:
            hrs = float(m_rel_hr.group(1))
            resolved = ref - timedelta(hours=hrs)
            return resolved, True

        m_rel_min = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:minutes?|mins?|min|મિનિટ|मिनट)\s*(?:ago|pahela|pehle|પહેલા|પહેલાં|पहले)\b", lower)
        if m_rel_min:
            mins = float(m_rel_min.group(1))
            resolved = ref - timedelta(minutes=mins)
            return resolved, True

        m_rel_day = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:days?|divas?|din|દિવાસ|દિવસ|दिन)\s*(?:ago|pahela|pehle|પહેલા|પહેલાં|पहले)\b", lower)
        if m_rel_day:
            days_count = float(m_rel_day.group(1))
            resolved = ref - timedelta(days=days_count)
            return resolved, True

        # Step 2: Date reference (calendar date)
        target_date, has_explicit_date = TimeService.parse_date_from_text(text, reference_date=ref.date())

        # Step 3: Period-of-day indicators in context
        is_morning = any(w in lower for w in [
            "morning", "savar", "savare", "saware", "sawar", "savaar", "subah", "subha", "સવાર", "સવારે", "સવારનો", "सुबह"
        ])
        is_afternoon = any(w in lower for w in [
            "afternoon", "bapor", "bapore", "dopahar", "બપોર", "બપોરે", "બપોરનું", "दोपहर"
        ])
        is_evening = any(w in lower for w in [
            "evening", "sanj", "sanje", "saanj", "saanje", "sanju", "shaam", "sham", "સાંજ", "સાંજે", "સાંજનો", "શામ", "शाम"
        ])
        is_night = any(w in lower for w in [
            "night", "raat", "raate", "raatri", "valoo", "valo", "vaalu", "રાત", "રાત્રે", "વાળુ", "વાળું", "रात"
        ])

        # Priority 1: hh:mm with optional AM/PM (e.g. 4:27 PM, 04:27, 16:27, 4.27 pm, 4:27, 12:05 AM)
        m_time = re.search(
            r"(?:at\s+|@\s*)?(\b\d{1,2})[:.](\d{2})\s*(am|pm|a\.m\.|p\.m\.)?\b",
            lower
        )

        hour: Optional[int] = None
        minute: Optional[int] = None
        has_explicit_time = False

        if m_time:
            h = int(m_time.group(1))
            m = int(m_time.group(2))
            meridiem = m_time.group(3)

            if 0 <= h <= 24 and 0 <= m < 60:
                has_explicit_time = True
                if meridiem:
                    meridiem_clean = meridiem.replace(".", "").lower()
                    if meridiem_clean == "pm":
                        if h < 12:
                            h += 12
                    elif meridiem_clean == "am":
                        if h == 12:
                            h = 0
                else:
                    # No explicit AM/PM: resolve based on context
                    if h >= 13:
                        pass  # Already 24h
                    elif is_morning:
                        h = 0 if h == 12 else h
                    elif is_afternoon:
                        h = h if h == 12 else (h + 12 if h < 12 else h)
                    elif is_evening or is_night:
                        h = h if h == 12 else (h + 12 if h < 12 else h)
                    else:
                        # Contextual inference for ambiguous 1-6 vs 7-11:
                        # 1 to 6 without AM/PM in food/workout logging typically implies afternoon/evening (PM).
                        # 7 to 11 typically implies AM unless meal context is dinner.
                        if 1 <= h <= 6:
                            h += 12
                        elif 7 <= h <= 11 and any(w in lower for w in ["dinner", "valo", "raat", "night"]):
                            h += 12
                hour = h
                minute = m

        # Priority 2: Period word followed by single hour (e.g. "savare 8", "bapore 1", "sanje 4", "ratre 9")
        if not has_explicit_time:
            m_hour = re.search(
                r"\b(?:savare|saware|subah|bapore|dopahar|sanje|shaam|ratre|raat|at|સવારે|બપોરે|સાંજે|રાત્રે|सुबह|दोपहर|शाम|रात)\s+(\d{1,2})(?:\s*(vage|vagye|baje|o'?clock|વાગ્યે|વાગે|બજે))?(?:\s+([a-zA-Z\u0A80-\u0AFF\u0900-\u097F]+))?\b",
                lower
            )
            if m_hour:
                clock_marker = m_hour.group(2)
                next_word = (m_hour.group(3) or "").lower()
                food_or_unit_words = {
                    "roti", "rotli", "rotlo", "rotla", "thepla", "theple", "bhakri", "bhakhri", "bread", "paratha", "naan", "puri", "poori",
                    "egg", "eggs", "anda", "ande", "cup", "cups", "glass", "glasses", "bowl", "bowls", "plate", "plates",
                    "piece", "pieces", "dish", "katori", "vatki", "scoop", "scoops", "spoon", "spoons",
                    "poha", "upma", "khichdi", "dal", "daal", "rice", "chawal", "sabzi", "shaak",
                    "રોટલી", "થેપલા", "ભાખરી", "રોટલો", "કપ", "ગ્લાસ", "વાટકી", "પ્લેટ", "નંગ", "ઈંડા", "ઈંડું",
                    "रोटी", "पराठा", "कप", "ग्लास", "कटोरी", "प्लेट", "अंडे", "अंडा"
                }
                if clock_marker or next_word not in food_or_unit_words:
                    h = int(m_hour.group(1))
                    if 1 <= h <= 12:
                        has_explicit_time = True
                        if is_afternoon or is_evening or is_night:
                            h = h if h == 12 else h + 12
                        elif is_morning:
                            h = 0 if h == 12 else h
                        hour = h
                        minute = 0

        # Priority 3: Single hour with am/pm (e.g. "8 am", "4 pm", "at 4pm")
        if not has_explicit_time:
            m_meridiem_hour = re.search(r"\b(\d{1,2})\s*(am|pm|a\.m\.|p\.m\.)\b", lower)
            if m_meridiem_hour:
                h = int(m_meridiem_hour.group(1))
                mer = m_meridiem_hour.group(2).replace(".", "").lower()
                if 1 <= h <= 12:
                    has_explicit_time = True
                    if mer == "pm" and h < 12:
                        h += 12
                    elif mer == "am" and h == 12:
                        h = 0
                    hour = h
                    minute = 0

        # If explicit time or explicit date was supplied, construct resolved_dt
        if has_explicit_time and hour is not None and minute is not None:
            resolved_dt = datetime(
                year=target_date.year,
                month=target_date.month,
                day=target_date.day,
                hour=hour,
                minute=minute,
                second=0,
                tzinfo=tz
            )
            return resolved_dt, True

        if has_explicit_date:
            # User gave a specific date (e.g. yesterday, 30/09/2026) but omitted time -> preserve ref clock on that date
            resolved_dt = datetime(
                year=target_date.year,
                month=target_date.month,
                day=target_date.day,
                hour=ref.hour,
                minute=ref.minute,
                second=ref.second,
                tzinfo=tz
            )
            return resolved_dt, False

        # Default Case A: User does NOT mention time -> use real current local clock time
        return ref, False

    @staticmethod
    def extract_time_range_from_text(
        text: str,
        reference_time: Optional[datetime] = None,
        tz_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Extracts a time range like '7:30 to 9:00', '7:30 - 9:00', '7:30–9:00', '7:30 thi 9:00'.
        Returns a dict with:
        - start_dt: datetime
        - end_dt: datetime
        - duration_minutes: float
        - range_str: str (e.g. '7:30–9:00')
        - raw_match: str (e.g. '7:30 to 9:00')
        Or None if no time range found.
        """
        tz = TimeService.get_timezone(tz_name)
        ref = reference_time or TimeService.get_current_local_datetime(tz_name)
        if ref.tzinfo is None:
            ref = ref.replace(tzinfo=tz)
        else:
            ref = ref.astimezone(tz)

        norm = TimeService.normalize_indic_digits(text)
        lower = norm.lower()

        # Regex for time range
        # e.g., 7:30 to 9:00, 7:30 - 9:00, 7:30–9:00, 7:30 thi 9:00, 7 to 9
        m_range = re.search(
            r"(?:from\s+)?(\b\d{1,2}(?:[:.]\d{2})?\s*(?:am|pm|a\.m\.|p\.m\.)?)\s*(?:to|-|–|—|thi|se|સુધી|થી)\s*(\b\d{1,2}(?:[:.]\d{2})?\s*(?:am|pm|a\.m\.|p\.m\.)?)\b",
            lower
        )
        if not m_range:
            return None

        start_str = m_range.group(1).strip()
        end_str = m_range.group(2).strip()

        # Inherit period of day if present in outer text (e.g. morning, evening)
        period_prefix = ""
        for p_word in ["morning", "savar", "savare", "saware", "subah", "afternoon", "bapor", "bapore", "evening", "sanj", "sanje", "shaam", "night", "raat", "સવાર", "સવારે", "બપોરે", "સાંજે", "રાત્રે", "सुबह", "दोपहर", "शाम", "रात"]:
            if p_word in lower:
                period_prefix = p_word + " "
                break

        start_dt, has_start = TimeService.extract_time_from_text(f"{period_prefix}{start_str}".strip(), reference_time=ref, tz_name=tz_name)
        end_dt, has_end = TimeService.extract_time_from_text(f"{period_prefix}{end_str}".strip(), reference_time=ref, tz_name=tz_name)

        if not (has_start and has_end):
            return None

        # If end is earlier than or equal to start, check PM or overflow
        if end_dt <= start_dt:
            if end_dt.hour < 12 and start_dt.hour <= 12:
                end_dt_pm = end_dt.replace(hour=end_dt.hour + 12)
                if end_dt_pm > start_dt:
                    end_dt = end_dt_pm

        duration_minutes = (end_dt - start_dt).total_seconds() / 60.0
        if duration_minutes <= 0 or duration_minutes > 720:
            return None

        return {
            "start_dt": start_dt,
            "end_dt": end_dt,
            "duration_minutes": duration_minutes,
            "range_str": f"{TimeService.format_time(start_dt)} – {TimeService.format_time(end_dt)}",
            "raw_match": m_range.group(0),
        }

    @staticmethod
    def infer_meal_type(text: str, dt: Optional[datetime] = None, tz_name: Optional[str] = None) -> str:
        """
        Infers meal type according to the required priority:
        1. Explicit user meal wording (Breakfast / Lunch / Snack / Dinner)
        2. Contextual time-of-day wording (Morning / Afternoon / Evening / Night)
        3. Explicit clock-time based inference (only when explicit time is present or dt provided).
        4. If user does NOT provide meal type or contextual time: DO NOT infer from current clock! Returns '—'.
        """
        lower = text.lower()

        # Priority 1: Explicit meal type keywords
        if any(w in lower for w in [
            "breakfast", "nasto", "nashta", "savarno nasto", "savar no nasto",
            "નાસ્તો", "સવારનો નાસ્તો", "नाश्ता", "सुबह का नाश्ता"
        ]):
            return "BREAKFAST"

        if any(w in lower for w in [
            "lunch", "bapor nu", "bapor no", "bapornu", "jamvanu",
            "લંચ", "બપોરનું ભોજન", "બપોરનું જમવાનું", "દોપહર કા ખાના", "लंच", "दोपहर का खाना"
        ]):
            return "LUNCH"

        if any(w in lower for w in [
            "snack", "snacks", "evening snack", "sanj no nasto",
            "સાંજનો નાસ્તો", "स्नैक", "शाम का नाश्ता"
        ]):
            return "SNACK"

        if any(w in lower for w in [
            "dinner", "valoo", "valo", "vaalu", "raat nu", "rat nu",
            "ડિનર", "વાળુ", "વાળું", "રાતનું ભોજન", "રાતનું જમવાનું", "डिनर", "रात का खाना"
        ]):
            return "DINNER"

        # Priority 2: Contextual time-of-day words
        has_dinner_staples = any(w in lower for w in [
            "bhadthu", "bharta", "rotlo", "rotla", "khichdi", "dinner", "valo", "vaalu",
            "વાળુ", "વાળું", "ડિનર", "ડિન્નર", "डिनर"
        ])
        has_snack_staples = any(w in lower for w in [
            "shake", "protein shake", "tea", "chai", "chhas", "chaas", "coffee", "biscuit",
            "snack", "snacks", "nasto", "nashta", "fruit", "apple", "banana"
        ])

        if any(w in lower for w in ["savar", "savare", "saware", "sawar", "savaar", "subah", "subha", "morning", "સવાર", "સવારે", "સવારનો", "सुबह"]):
            return "BREAKFAST"
        if any(w in lower for w in ["bapor", "bapore", "dopahar", "afternoon", "બપોર", "બપોરે", "બપોરનું", "दोपहर"]):
            return "LUNCH"
        if any(w in lower for w in ["sanj", "sanje", "saanj", "saanje", "sanju", "shaam", "sham", "evening", "સાંજ", "સાંજે", "સાંજનો", "શામ", "शाम"]):
            if has_dinner_staples and not has_snack_staples:
                return "DINNER"
            if dt is not None and dt.hour >= 19:
                return "DINNER"
            return "SNACK"
        if any(w in lower for w in ["raat", "raate", "raatri", "night", "રાત", "રાત્રે", "रात"]):
            return "DINNER"

        # Priority 3: Explicit clock-time based inference
        target_dt = dt
        if target_dt is None:
            # Check if text contains explicit clock time
            ext_dt, has_ext = TimeService.extract_time_from_text(text)
            if has_ext:
                target_dt = ext_dt

        if target_dt is not None:
            tz = TimeService.get_timezone(tz_name)
            if target_dt.tzinfo is not None:
                target_dt = target_dt.astimezone(tz)
            hour = target_dt.hour

            if 5 <= hour < 11:
                return "BREAKFAST"
            elif 11 <= hour < 16:
                return "LUNCH"
            elif 16 <= hour < 19:
                return "SNACK"
            else:
                return "DINNER"

        # Rule C: If user does NOT provide meal type or contextual time: DO NOT infer from current clock!
        return "—"

    @staticmethod
    def format_time(dt: Any, tz_name: Optional[str] = None) -> str:
        """
        Formats datetime into clean 12-hour local time representation (e.g. '4:27 PM').
        Correctly converts UTC timestamps to Asia/Kolkata before formatting.
        """
        if dt is None:
            return "12:00 PM"

        tz = TimeService.get_timezone(tz_name)

        if isinstance(dt, str):
            try:
                parsed = datetime.fromisoformat(dt.replace("Z", "+00:00"))
                dt = parsed
            except Exception:
                return "12:00 PM"

        if isinstance(dt, datetime):
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc).astimezone(tz)
            else:
                dt = dt.astimezone(tz)
            return dt.strftime("%I:%M %p").lstrip("0")

        return "12:00 PM"
