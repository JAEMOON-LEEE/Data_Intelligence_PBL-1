"""Helpers shared by the collectors."""
import html
import os
import re
from datetime import datetime, timezone

import pandas as pd

COLUMNS = [
    "id", "group", "language", "source", "source_url", "query",
    "title", "text", "text_type", "published_at", "collected_at",
]

HANGUL = re.compile(r"[\uac00-\ud7a3\u3131-\u318e]")
LATIN = re.compile(r"[A-Za-z]")
TAG = re.compile(r"<[^>]+>")


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def to_utc_iso(value) -> str:
    """Normalise any timestamp to UTC ISO-8601 (one timezone for everything)."""
    ts = pd.to_datetime(value, utc=True, errors="coerce")
    return "" if pd.isna(ts) else ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def strip_html(text: str) -> str:
    if not isinstance(text, str):
        return ""
    return re.sub(r"\s+", " ", html.unescape(TAG.sub(" ", text))).strip()


_DETECTOR = None


def _detector():
    """Lingua detector limited to languages common in K-pop YouTube comments.
    Limiting the set makes short-text detection faster and more accurate;
    anything outside it that looks Latin-script falls into the closest match
    and is dropped unless it is English."""
    global _DETECTOR
    if _DETECTOR is None:
        from lingua import Language, LanguageDetectorBuilder
        langs = [
            Language.ENGLISH, Language.SPANISH, Language.PORTUGUESE,
            Language.INDONESIAN, Language.TAGALOG, Language.FRENCH,
            Language.GERMAN, Language.ITALIAN, Language.VIETNAMESE,
            Language.TURKISH, Language.MALAY,
        ]
        _DETECTOR = LanguageDetectorBuilder.from_languages(*langs).build()
    return _DETECTOR


def detect_lang(text: str) -> str:
    """Return 'ko', 'en' or 'other'.

    Korean: Hangul is at least 30% of letters.
    English: no Hangul, mostly Latin letters, and lingua says English.
    """
    hangul = len(HANGUL.findall(text))
    latin = len(LATIN.findall(text))
    letters = hangul + latin
    if letters == 0:
        return "other"  # emoji-only, numbers, etc.
    if hangul / letters >= 0.3:
        return "ko"
    if hangul == 0 and latin >= 3:
        from lingua import Language
        return "en" if _detector().detect_language_of(text) == Language.ENGLISH else "other"
    return "other"


def mentions_group(text: str, names) -> bool:
    """Whole-word match, case-insensitive ("bts" must not match "debts")."""
    low = (text or "").lower()
    return any(re.search(r"(?<![a-z0-9])" + re.escape(n.lower()) + r"(?![a-z0-9])", low)
               for n in names)


def save(rows, path: str) -> pd.DataFrame:
    """Write rows with the agreed schema; ids are assigned at merge time."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df = pd.DataFrame(rows)
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ""
    df = df[COLUMNS]
    df.to_csv(path, index=False, encoding="utf-8-sig")  # utf-8-sig: Excel opens Korean correctly
    print(f"  saved {len(df)} rows -> {path}")
    return df
