"""
Shared settings for the PBL Module #1 K-POP data pipeline.
Edit this file, not the scripts.
"""
import os

try:  # load keys from .env automatically if python-dotenv is installed
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ---------------------------------------------------------------------------
# API keys (put them in a .env file or your shell environment, never in git)
# ---------------------------------------------------------------------------
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "")
GUARDIAN_API_KEY = os.getenv("GUARDIAN_API_KEY", "")

# ---------------------------------------------------------------------------
# Groups
#   debut:      collection start date (YYYY-MM-DD). VERIFY these before running.
#   ko_query:   Naver News search keyword
#   en_query:   Guardian search query (boolean operators allowed)
#   en_names:   a document must contain one of these (case-insensitive)
#               to count as relevant -> filters out false matches
#   ko_names:   same for Korean documents
#   official_channels: YouTube channel names that count as "official".
#               Auto-search keeps only videos uploaded by these channels.
#               VERIFY the exact names on YouTube before running.
#   video_ids:  official MV IDs to pull comments from. Filling these in is
#               the most reliable option; if empty, auto-search is used.
# ---------------------------------------------------------------------------
GROUPS = {
    # Final lineup (2026-10-13, afternoon): BTS, SEVENTEEN, BLACKPINK, TWICE
    #   = 2 boy groups + 2 girl groups, HYBE / YG / JYP.
    # MONSTA X and GOT7 were trial candidates (kept below, commented out).
    # en_headline_require -> regex the HEADLINE must match (case-SENSITIVE unless
    #                  the pattern says (?i:...)). Used for names that are also
    #                  ordinary English words ("twice") or abbreviations ("BTS").
    # en_exclude_regex -> headline regex (case-insensitive) that drops the row.
    # gdelt_query_fallback -> used automatically if GDELT rejects gdelt_query.
    "BTS": {
        "debut": "2013-06-13",
        "ko_query": "방탄소년단",
        "en_query": 'BTS AND (k-pop OR kpop OR "Big Hit" OR HYBE OR "boy band")',
        "gdelt_query": 'bts ("k-pop" OR kpop OR hybe OR "big hit" OR "boy band")',
        "gdelt_query_fallback": "(bangtan OR jungkook OR jimin OR taehyung OR namjoon OR seokjin "
                                "OR hoseok OR yoongi)",
        "en_names": ["bts", "bangtan"],
        "en_context": ["k-pop", "kpop", "hybe", "big hit", "boy band", "army"],
        # headline must write BTS in capitals (or Bangtan): lowercase "bts" is
        # usually "behind the scenes"
        "en_headline_require": r"\bBTS\b|(?i:bangtan)",
        # other BTS's: Bangkok Skytrain, telecom base stations, US transport bureau
        "en_exclude": ["skytrain", "bangkok", "mass transit", "behind the scenes",
                       "behind-the-scenes", "bts station", "bts tower", "base station",
                       "base transceiver", "telecom", "transportation statistics",
                       "bts group holdings"],
        "ko_names": ["방탄소년단", "bts"],
        "official_channels": ["hybe labels", "bangtantv"],
        "video_ids": [],
    },
    "TWICE": {
        "debut": "2015-10-20",
        "ko_query": "트와이스",
        "en_query": 'TWICE AND (k-pop OR kpop OR JYP OR "girl group")',
        "gdelt_query": 'twice ("k-pop" OR kpop OR jyp OR "girl group")',
        "en_names": ["twice"],
        "en_context": ["k-pop", "kpop", "jyp", "girl group"],
        # "twice" is an ordinary word -> headline must write TWICE in capitals,
        # or contain a K-pop word / member name
        # accepted: TWICE in capitals; "Twice" as the first word ("Twice performs
        # new song"); "Twice's"; "group/band/stars Twice"; or a K-pop word /
        # member name anywhere. Common-word uses are removed by en_exclude_regex.
        "en_headline_require": r"\bTWICE\b|^Twice\b|\bTwice's|"
                               r"(?i:\b(group|band|idols?|stars?|superstars?|members?)\s+twice\b)|"
                               r"(?i:\b(k-?pop|jyp|girl group|nayeon|jeongyeon|momo|"
                               r"sana|jihyo|mina|dahyun|chaeyoung|tzuyu)\b)",
        "en_exclude": [],
        # ordinary uses of the word: "twice as", "twice a week", "won twice", ...
        "en_exclude_regex": r"\btwice\s+(as|a\s+(day|week|month|year)|the|over|daily|weekly|"
                            r"monthly|yearly|annually|than|more|before|upon|bitten|shy|removed)\b|\btwice-(?!pop)\w|"
                            r"\b(won|lost|scored|happened|struck|strikes?|think|thought|been|"
                            r"nearly|almost|than|least|married|elected|charged|arrested|"
                            r"vaccinated|once or)\s+twice\b",
        "ko_names": ["트와이스", "twice"],
        "official_channels": ["jyp entertainment", "twice"],
        "video_ids": [],
    },
    # en_query      -> Guardian search (boolean). Must force a K-pop context:
    #                  "Seventeen" alone also matches Seventeen magazine / the number.
    # gdelt_query   -> GDELT full-text search (article text must match).
    # en_names      -> the headline/summary must contain one of these.
    # en_context    -> for ambiguous names: article text must also contain one
    #                  of these, or the row is dropped.
    "SEVENTEEN": {
        "debut": "2015-05-26",
        "ko_query": "세븐틴",
        "en_query": 'Seventeen AND (k-pop OR kpop OR Pledis OR "boy band" OR HYBE)',
        "gdelt_query": 'seventeen ("k-pop" OR kpop OR pledis OR "boy band")',
        "en_names": ["seventeen"],
        "en_context": ["k-pop", "kpop", "pledis", "boy band", "hybe", "carat"],
        # drop headlines about OTHER "Seventeen"s: the Indonesian rock band,
        # Seventeen magazine, ages. Found in the 2026-10-13 spot check.
        "en_exclude": ["indonesian band", "rock band", "pop band seventeen", "tsunami", "ifan", "magazine",
                       "seventeen-year", "seventeen year", "aged seventeen"],
        "ko_names": ["세븐틴", "seventeen"],
        "official_channels": ["hybe labels", "seventeen"],
        "video_ids": [],
    },
    # "MONSTA X": {
    #     "debut": "2015-05-14",
    #     "ko_query": "몬스타엑스",
    #     "en_query": '"Monsta X"',
    #     "gdelt_query": '"monsta x"',
    #     "en_names": ["monsta x"],
    #     "en_context": [],
    #     "ko_names": ["몬스타엑스", "monsta x"],
    #     "official_channels": ["monsta x", "starshipTV"],
    #     "video_ids": [],
    # },
    "BLACKPINK": {
        "debut": "2016-08-08",
        "ko_query": "블랙핑크",
        "en_query": '"BLACKPINK"',
        "gdelt_query": "blackpink",
        "en_names": ["blackpink"],
        "en_context": [],
        "ko_names": ["블랙핑크", "blackpink"],
        "official_channels": ["blackpink"],
        "video_ids": [],
    },
    # "GOT7": {
    #     "debut": "2014-01-16",
    #     "ko_query": "갓세븐",
    #     "en_query": "GOT7",
    #     "gdelt_query": "got7",
    #     "en_names": ["got7"],
    #     "en_context": [],
    #     "ko_names": ["갓세븐", "got7"],
    #     "official_channels": ["got7", "jypentertainment"],
    #     "video_ids": [],
    # },
}

# ---------------------------------------------------------------------------
# Targets (per group, per language) — the team's pilot plan
# ---------------------------------------------------------------------------
# Drop headlines that also name ANOTHER group in GROUPS (e.g. "GOT7, Monsta X &
# BTOB debut on Billboard"), so one headline can't count for two groups.
DROP_MULTI_GROUP = True
# Names that ALSO count as "another group" for that filter, although they are
# no longer in GROUPS (trial candidates). Keeps the data identical to the
# reviewed trial: "Seventeen, Monsta X & ..." lineup headlines stay dropped.
MULTI_GROUP_EXTRA = ["monsta x", "got7"]
# Max headlines kept per group, spread evenly by year (2026-10-13: raised from
# 500 to 1000 to get as many full texts as possible). Groups with fewer
# headlines keep all of them.
NEWS_PER_LANG = 1000
# Final English corpus = headlines only (8 Guardian headline+summary rows are
# dropped so every document is the same text type). None = keep all sources.
EN_SOURCES = ["gdelt_news"]   # trial: 500 English articles per group, spread evenly by year
COMMENTS_PER_LANG = 400
# Collect extra comments so ~400 survive cleaning (spam, duplicates, emoji-only).
COMMENT_OVERFETCH = 2.0

# YouTube: how many videos per group when auto-searching, and comment sort order.
# "relevance" = top comments (skews toward fan praise; note it in the data card)
# "time"      = newest first
YT_VIDEOS_PER_GROUP = 8
YT_SEARCH_POOL = 50  # search results scanned before filtering by channel
YT_COMMENT_ORDER = "relevance"
YT_MAX_PAGES_PER_VIDEO = 30  # 100 comments per page

# Guardian: "summary" uses the trailText (standfirst) -> comparable to Naver's
# description. "full" uses the full article body. Keep it consistent with the
# Korean side (Naver only gives summaries) unless the team decides otherwise.
GUARDIAN_TEXT = "summary"

END_DATE = None  # None = today
RANDOM_SEED = 42

RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"
