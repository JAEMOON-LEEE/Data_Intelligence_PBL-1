"""
Pilot check: are we actually getting usable data?

Prints the numbers the team agreed to look at before deciding whether
"debut to now, 100 news + 400 comments" works:
  1. rows per group x language x source
  2. date distribution per group (did "debut to now" really happen?)
  3. text length by text_type (summary vs full vs comment)
  4. after preprocessing: rows left + top words per group

Usage:  python check_data.py [raw_csv] [processed_en_csv]
"""

# --- repo layout: config.py and common.py live in collection/en/ ---
import os as _os, sys as _sys
_here = _os.path.dirname(_os.path.abspath(__file__))
for _p in (_here, _os.path.join(_here, "..", "..", "collection", "en")):
    if _os.path.exists(_os.path.join(_p, "config.py")) and _p not in _sys.path:
        _sys.path.insert(0, _p)
# -------------------------------------------------------------------

import sys
from collections import Counter

import pandas as pd

import config


def report_raw(df: pd.DataFrame):
    print("=" * 60, "\n1) ROWS per group / language / source\n")
    print(df.groupby(["group", "language", "source"]).size().unstack(fill_value=0).to_string())

    print("\n2) DATE DISTRIBUTION (rows per year)\n")
    d = df.copy()
    d["year"] = pd.to_datetime(d["published_at"], utc=True, errors="coerce").dt.year
    for (g, src), sub in d.groupby(["group", "source"]):
        years = sub["year"].value_counts().sort_index()
        share_recent = (sub["year"] >= years.index.max()).mean() if len(years) else 0
        flag = "  <- mostly recent only" if share_recent > 0.7 and len(years) > 0 else ""
        counts = {int(y): int(n) for y, n in years.items()}
        print(f"{g:12s} {src:11s} {counts}{flag}")

    print("\n3) TEXT LENGTH (words) by text_type\n")
    d["words"] = d["text"].fillna("").str.split().map(len)
    print(d.groupby(["language", "text_type"])["words"].describe()[["count", "mean", "50%", "max"]].round(1).to_string())


def report_processed(df: pd.DataFrame):
    print("\n" + "=" * 60, "\n4) AFTER ENGLISH PREPROCESSING\n")
    print(df.groupby(["group", "source"]).size().unstack(fill_value=0).to_string())
    print()
    for g, sub in df.groupby("group"):
        c = Counter(" ".join(sub["tokens"].fillna("")).split())
        print(f"{g:12s} top words: {', '.join(w for w, _ in c.most_common(12))}")


def main():
    raw = sys.argv[1] if len(sys.argv) > 1 else f"{config.RAW_DIR}/all_raw.csv"
    proc = sys.argv[2] if len(sys.argv) > 2 else f"{config.PROCESSED_DIR}/en_processed.csv"
    report_raw(pd.read_csv(raw, encoding="utf-8-sig"))
    try:
        report_processed(pd.read_csv(proc, encoding="utf-8-sig"))
    except FileNotFoundError:
        print("\n(no processed file yet — run preprocess_en.py)")


if __name__ == "__main__":
    main()
