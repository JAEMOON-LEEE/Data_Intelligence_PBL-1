"""
Trial: collect up to 500 English news items per group (config.GROUPS), spread
as evenly as possible from debut year to now, from two sources:

  - Guardian Open Platform  (headline + standfirst; covers 1999-now)
  - GDELT                   (headline only; worldwide outlets; ~2017-now,
                             officially guaranteed only for the last ~3 months)

Korean outlets are excluded (overseas coverage only). Ambiguous names
(e.g. "Seventeen" = magazine / number) must appear with a K-pop context word.

"Evenly" = stratified by YEAR: each year gets an equal share of the target;
years with fewer articles give their unused share to years with more.
The script prints a year-by-year table so the team can compare the groups.

Usage (Colab):  !python collect_news_en_trial.py
Output: data/raw/news_en_trial_<date>.csv  +  data/news_en_trial_coverage.csv (outside raw/ so merge.py skips it)
"""
import json
import os
import random
import time
from collections import defaultdict
from datetime import date, datetime, timedelta

import re

import pandas as pd
import requests

import config
from collect_news_gdelt import QueryRejected, fetch as gdelt_fetch, is_korean_outlet
from common import mentions_group, now_utc, save, strip_html, to_utc_iso

GUARDIAN_URL = "https://content.guardianapis.com/search"
GDELT_START = date(2017, 1, 1)
GDELT_WINDOW = 91
GDELT_PAUSE = 8           # Colab IPs are shared; GDELT wants >= 5 s between calls
CACHE_DIR = "data/cache_gdelt"  # successful windows are saved here; reruns skip them


# ------------------------------------------------------------------ helpers
# Not news: app-spam pages, bot posts with links / stream counters, petitions,
# MP3 download pages ("... Mp3 [2.16 MB]"), lyrics/chord pages, personality quizzes.
SPAM = re.compile(r"\bapk\b|mod money|https?\s*:|\bt\s*\.\s*co\s*/|streams today|"
                  r"change\s*\.\s*org|\bpetition\b|"
                  r"\bmp3\b|\[\s*\d+(\s*\.\s*\d+)?\s*mb\s*\]|"
                  # lyrics / chord pages, personality quizzes (added 2026-10-13 spot check)
                  r"\blyrics?\b|\blirik\b|\bchords?\b|kunci gitar|\bquiz\b|"
                  r"\bwe'?ll (determine|reveal|tell)\b|\byou'?re most like\b|"
                  r"\bwallpapers?\b|\bhd download\b", re.I)
# matched against the URL's HOST only (2026-10-13 fix: a plain substring test
# for "t.co" also hit nypost.com, washingtonpost.com, cnet.com, ...)
SPAM_HOSTS = ("change.org", "t.co")


def spam_url(url: str) -> bool:
    from urllib.parse import urlparse
    host = urlparse(url or "").netloc.lower().split(":")[0]
    host = host[4:] if host.startswith("www.") else host
    return "apk" in host or any(host == h or host.endswith("." + h) for h in SPAM_HOSTS)


def match_form(title: str) -> str:
    """GDELT spaces out hyphens ("K - pop", "J - Hope"); join them for matching."""
    return re.sub(r"\s*-\s*", "-", title or "")


def other_groups(group: str) -> list:
    names = [n for g, i in config.GROUPS.items() if g != group for n in i["en_names"]]
    return names + list(getattr(config, "MULTI_GROUP_EXTRA", []))


def excluded(text: str, info: dict, group: str = None, url: str = "") -> bool:
    bad = info.get("en_exclude") or []
    if bad and mentions_group(text, bad):
        return True
    if info.get("en_exclude_regex") and re.search(info["en_exclude_regex"], text or "", re.I):
        return True
    if SPAM.search(text or "") or spam_url(url):
        return True
    if group and getattr(config, "DROP_MULTI_GROUP", False) and mentions_group(text, other_groups(group)):
        return True
    return False


def relevant(text: str, info: dict) -> bool:
    if not mentions_group(text, info["en_names"]) or excluded(text, info):
        return False
    ctx = info.get("en_context") or []
    return not ctx or mentions_group(text, ctx)


def row(group, source, url, query, title, text, text_type, published):
    return {"group": group, "language": "en", "source": source, "source_url": url,
            "query": query, "title": title, "text": text, "text_type": text_type,
            "published_at": published, "collected_at": now_utc()}


# ------------------------------------------------------------------ Guardian
def guardian(group, info):
    if not config.GUARDIAN_API_KEY:
        print("  Guardian: no key, skipped")
        return []
    out, page, pages = [], 1, 1
    while page <= pages and page <= 25:          # 25 x 200 = 5,000 scanned max
        r = requests.get(GUARDIAN_URL, timeout=30, params={
            "q": info["en_query"], "from-date": info["debut"], "order-by": "oldest",
            "page-size": 200, "page": page, "show-fields": "headline,trailText,bodyText",
            "api-key": config.GUARDIAN_API_KEY})
        r.raise_for_status()
        resp = r.json()["response"]
        pages = resp.get("pages", 0)
        for it in resp.get("results", []):
            f = it.get("fields", {})
            title = strip_html(f.get("headline") or it.get("webTitle", ""))
            summary = strip_html(f.get("trailText", ""))
            body = strip_html(f.get("bodyText", ""))          # relevance check only, not saved
            if excluded(title, info, group, it.get("webUrl", "")):
                continue
            if relevant(" ".join([title, summary, body]), info) and mentions_group(title + " " + summary + " " + body[:1500], info["en_names"]):
                out.append(row(group, "guardian", it.get("webUrl", ""), info["en_query"],
                               title, summary or title, "summary",
                               to_utc_iso(it.get("webPublicationDate", ""))))
        page += 1
        time.sleep(0.2)
    print(f"  Guardian: {len(out)} relevant articles")
    return out


# ------------------------------------------------------------------ GDELT
REJECT_DIR = "data/check"


def gdelt(group, info):
    gq = info.get("gdelt_query", info["en_names"][0])
    state = {"q": f"{gq} sourcelang:english -sourcecountry:KS", "suffix": ""}
    # a cache made with the fallback query is marked _fb, so the two never mix
    os.makedirs(CACHE_DIR, exist_ok=True)
    if info.get("gdelt_query_fallback") and any(
            f.startswith(group.replace(" ", "_") + "_fb_") for f in os.listdir(CACHE_DIR)):
        state.update(q=f"{info['gdelt_query_fallback']} sourcelang:english -sourcecountry:KS", suffix="_fb")
    start = max(date.fromisoformat(info["debut"]), GDELT_START)
    windows = []
    while start <= date.today():
        end = min(start + timedelta(days=GDELT_WINDOW - 1), date.today())
        windows.append((start, end))
        start = end + timedelta(days=1)

    out, seen, rejected = [], set(), []
    require = info.get("en_headline_require")

    os.makedirs(CACHE_DIR, exist_ok=True)

    def run(win):
        path = f"{CACHE_DIR}/{group.replace(' ', '_')}{state['suffix']}_{win[0]}_{win[1]}.json"
        cached = os.path.exists(path)
        if cached:
            with open(path, encoding="utf-8") as fh:
                arts = json.load(fh)
        else:
            try:
                arts = gdelt_fetch(state["q"], *win)
            except QueryRejected as e:
                if state["suffix"] or not info.get("gdelt_query_fallback"):
                    raise SystemExit(f"GDELT rejected the {group} query: {e}\n"
                                     f"-> edit gdelt_query for {group} in config.py")
                print(f"    GDELT rejected the query ({str(e)[:60]}); "
                      f"switching {group} to the fallback query")
                state.update(q=f"{info['gdelt_query_fallback']} sourcelang:english -sourcecountry:KS",
                             suffix="_fb")
                return run(win)
            if arts is None:
                return False
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(arts, fh, ensure_ascii=False)
        kept = 0
        for a in arts:
            if is_korean_outlet(a) or (a.get("language") or "English") != "English":
                continue
            title = (a.get("title") or "").strip()
            key = title.lower()
            mt = match_form(title)
            if not title or key in seen or not mentions_group(mt, info["en_names"]):
                continue
            if (require and not re.search(require, mt)) or excluded(mt, info, group, a.get("url", "")):
                seen.add(key)
                rejected.append({"group": group, "title": title, "url": a.get("url", "")})
                continue
            seen.add(key)
            ts = datetime.strptime(a["seendate"], "%Y%m%dT%H%M%SZ").strftime("%Y-%m-%dT%H:%M:%SZ")
            out.append(row(group, "gdelt_news", a.get("url", ""), state["q"], "", title, "headline", ts))
            kept += 1
        print(f"    GDELT {win[0]} ~ {win[1]}: {len(arts)} returned, {kept} kept"
              + ("  (cached)" if cached else ""))
        return True, cached

    failed = []
    for win in windows:
        res = run(win)
        if not res:
            print(f"    GDELT {win[0]} ~ {win[1]}: FAILED (rate limit), will retry")
            failed.append(win)
        if not res or not res[1]:                 # no pause needed for cached windows
            time.sleep(GDELT_PAUSE)

    for round_no in (1, 2, 3):                    # retry failed windows, slower each round
        if not failed:
            break
        print(f"  retrying {len(failed)} failed windows (round {round_no}) ...")
        time.sleep(30 * round_no)
        still = []
        for win in failed:
            if not run(win):
                still.append(win)
            time.sleep(GDELT_PAUSE * 2)
        failed = still

    if failed:
        print(f"  WARNING: {len(failed)} windows still FAILED -> years "
              f"{sorted({w[0].year for w in failed})} are under-counted.\n"
              f"  -> Just run the script again later: finished windows are cached, only these are re-requested.")
    print(f"  GDELT: {len(out)} relevant headlines  ({len(rejected)} rejected by filters)")
    # for checking the filters: what was thrown away (names that are also
    # ordinary words / abbreviations -> look at these for BTS and TWICE)
    os.makedirs(REJECT_DIR, exist_ok=True)
    pd.DataFrame(rejected, columns=["group", "title", "url"]).to_csv(
        f"{REJECT_DIR}/rejected_{group.replace(' ', '_')}.csv", index=False, encoding="utf-8-sig")
    return out


# ------------------------------------------------------------------ sampling
def stratified_by_year(rows, target, first_year, seed):
    """Equal share per year; unused share flows to years that have more."""
    rng = random.Random(seed)
    by_year = defaultdict(list)
    for r in rows:
        by_year[int(r["published_at"][:4])].append(r)
    years = list(range(first_year, date.today().year + 1))
    for y in years:
        rng.shuffle(by_year[y])
    take = {y: 0 for y in years}
    left = target
    while left > 0:
        open_years = [y for y in years if take[y] < len(by_year[y])]
        if not open_years:
            break
        share = max(1, left // len(open_years))
        for y in open_years:
            add = min(share, len(by_year[y]) - take[y], left)
            take[y] += add
            left -= add
            if left == 0:
                break
    picked = [r for y in years for r in by_year[y][: take[y]]]
    table = {y: (len(by_year[y]), take[y]) for y in years}
    return picked, table


POOL_OUT = "data/pool/news_en_pool.csv"
HEADLINES_OUT = f"{config.RAW_DIR}/news_en_headlines.csv"


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool-only", action="store_true",
                    help="save the FULL filtered pool (no sampling) to data/pool/ and stop; "
                         "reads GDELT from the cache, does not touch data/raw")
    args = ap.parse_args()
    use_guardian = not getattr(config, "EN_SOURCES", None) or "guardian" in config.EN_SOURCES

    all_rows, coverage, pool = [], [], []
    for group, info in config.GROUPS.items():
        print(f"\n[{group}] debut {info['debut']}")
        rows = (guardian(group, info) if use_guardian else []) + gdelt(group, info)
        # same story from both sources -> keep one
        seen, uniq = set(), []
        for r in rows:
            k = (r["title"] or r["text"]).lower()[:80]
            if k not in seen:
                seen.add(k)
                uniq.append(r)
        if args.pool_only:
            pool += uniq
            print(f"  {group}: {len(uniq)} in pool")
            continue
        picked, table = stratified_by_year(uniq, config.NEWS_PER_LANG,
                                           int(info["debut"][:4]), config.RANDOM_SEED)
        all_rows += picked
        print(f"  {group}: {len(uniq)} unique available -> kept {len(picked)} / target {config.NEWS_PER_LANG}")
        print("  year : available -> kept")
        for y, (avail, kept) in table.items():
            print(f"  {y} : {avail:5d} -> {kept:4d}")
            coverage.append({"group": group, "year": y, "available": avail, "kept": kept})
        src = pd.Series([r["source"] for r in picked]).value_counts().to_dict() if picked else {}
        print(f"  kept by source: {src}")

    if args.pool_only:
        os.makedirs(os.path.dirname(POOL_OUT), exist_ok=True)
        save(pool, POOL_OUT)
        p = pd.DataFrame(pool)
        if len(p):
            p["year"] = p["published_at"].str[:4]
            print("\npool size by group and year:")
            print(p.groupby(["group", "year"]).size().unstack(fill_value=0).to_string())
        return

    save(all_rows, HEADLINES_OUT)
    cov = pd.DataFrame(coverage)
    cov.to_csv("data/news_en_headlines_coverage.csv", index=False)
    # spot-check file: 30 random kept headlines per group -> read them!
    os.makedirs(REJECT_DIR, exist_ok=True)
    kept = pd.DataFrame(all_rows)
    if len(kept):
        (kept.sample(frac=1, random_state=config.RANDOM_SEED).groupby("group").head(30)
             .sort_values("group")[["group", "published_at", "text", "source_url"]]
             .to_csv(f"{REJECT_DIR}/spotcheck_kept.csv", index=False, encoding="utf-8-sig"))

    print("\n" + "=" * 60 + "\nSUMMARY: English headlines per group\n")
    if len(cov):
        summ = cov.groupby("group").agg(available=("available", "sum"), kept=("kept", "sum"),
                                        years_with_data=("available", lambda s: int((s > 0).sum())),
                                        years_total=("year", "count"))
        print(summ.to_string())
    print(f"\nsaved -> {HEADLINES_OUT}")
    print(f"check the filters -> {REJECT_DIR}/spotcheck_kept.csv (kept) and {REJECT_DIR}/rejected_<group>.csv (dropped)")


if __name__ == "__main__":
    main()
