"""
STEP 2: crawl the FULL TEXT (and publisher summary) of every English headline
collected in step 1 (data/raw/news_en_headlines.csv, GDELT URLs).

Responsible-collection safeguards (write these in the data card):
  - robots.txt is checked for every site; disallowed or unreadable -> skipped
  - honest User-Agent identifying a student research project
  - >= HOST_DELAY seconds between requests to the same site
  - theguardian.com is skipped (the Guardian registration states that full
    article text is not stored)
  - text is used only for aggregate analysis; do NOT redistribute it

Order: group by group, year by year; already-crawled URLs (cache) first.
Cache : data/cache_fulltext/  -> rerun = resume, nothing is fetched twice.

Usage (Colab):
  !python collect_fulltext_en.py                      # crawl ALL headlines
  !python collect_fulltext_en.py --limit 40           # quick test (40 random URLs)
  !python collect_fulltext_en.py --per-year 60        # stop a group-year at 60 full texts
  !python collect_fulltext_en.py --per-year 60 --match-groups
        # every group gets at most the smallest group's count in each year

Output (data/extra/):
  news_en_fulltext.csv   text = article body (text_type=full), title = headline
  news_en_summary.csv    text = publisher summary (text_type=summary)
  fetch_report.csv       one row per URL with status
  fulltext_by_year.csv   group x year: available / tried / full_text
"""
import argparse
import hashlib
import json
import os
import socket
import time
import urllib.robotparser as robotparser
from urllib.parse import urlparse

import pandas as pd
import requests

import config

UA = "SunmoonUniv-PBL-student-research/1.0 (non-commercial coursework; aggregate text analysis)"
HOST_DELAY = 3.0
TIMEOUT = 20
SKIP_DOMAINS = ("theguardian.com",)
MIN_FULLTEXT_WORDS = 80          # shorter "bodies" are usually cookie walls / teasers
INPUT = f"{config.RAW_DIR}/news_en_headlines.csv"
OUT_DIR = "data/extra"
CACHE_DIR = "data/cache_fulltext"

socket.setdefaulttimeout(TIMEOUT)    # robots.txt reads have no timeout of their own
_robots, _last_hit = {}, {}


def host_of(url):
    u = urlparse(url)
    return f"{u.scheme}://{u.netloc}", u.netloc.lower()


def robots_allows(url):
    base, _ = host_of(url)
    if base not in _robots:
        rp = robotparser.RobotFileParser(base + "/robots.txt")
        try:
            rp.read()          # 404 -> allow all, 401/403 -> disallow all (stdlib behaviour)
        except Exception:
            rp = None          # unreadable -> treat as NOT allowed (conservative)
        _robots[base] = rp
    rp = _robots[base]
    return rp is not None and rp.can_fetch(UA, url)


def polite_wait(netloc):
    wait = HOST_DELAY - (time.time() - _last_hit.get(netloc, 0))
    if wait > 0:
        time.sleep(wait)
    _last_hit[netloc] = time.time()


def meta_summary(html):
    from bs4 import BeautifulSoup
    s = BeautifulSoup(html, "html.parser")
    for attrs in ({"property": "og:description"}, {"name": "description"},
                  {"name": "twitter:description"}):
        m = s.find("meta", attrs=attrs)
        if m and (m.get("content") or "").strip():
            return " ".join(m["content"].split())
    return ""


def main_text(html, url):
    try:
        import trafilatura
        txt = trafilatura.extract(html, url=url, include_comments=False,
                                  include_tables=False, favor_precision=True)
        if txt:
            return " ".join(txt.split())
    except ImportError:
        pass
    from bs4 import BeautifulSoup        # fallback: join <p> paragraphs
    s = BeautifulSoup(html, "html.parser")
    paras = [p.get_text(" ", strip=True) for p in s.find_all("p")]
    return " ".join(p for p in paras if len(p.split()) >= 8)


def fetch(url):
    """Return dict(status, summary, fulltext). Cached on disk."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = f"{CACHE_DIR}/{hashlib.sha1(url.encode()).hexdigest()}.json"
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    base, netloc = host_of(url)
    if any(netloc.endswith(d) for d in SKIP_DOMAINS):
        res = {"status": "skipped_domain", "summary": "", "fulltext": ""}
    elif not robots_allows(url):
        res = {"status": "robots_disallowed", "summary": "", "fulltext": ""}
    else:
        polite_wait(netloc)
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT)
            if r.status_code != 200 or "html" not in r.headers.get("Content-Type", "html"):
                res = {"status": f"http_{r.status_code}", "summary": "", "fulltext": ""}
            else:
                summ = meta_summary(r.text)
                body = main_text(r.text, url)
                if len(body.split()) < MIN_FULLTEXT_WORDS:
                    body = ""
                status = "ok" if body else ("summary_only" if summ else "no_text")
                res = {"status": status, "summary": summ, "fulltext": body}
        except requests.RequestException as e:
            res = {"status": "error_" + type(e).__name__, "summary": "", "fulltext": ""}
    # transient network errors are not cached, so a rerun retries them
    if not res["status"].startswith("error_"):
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(res, fh, ensure_ascii=False)
    return res


def is_cached(url):
    return os.path.exists(f"{CACHE_DIR}/{hashlib.sha1(url.encode()).hexdigest()}.json")


def crawl(df, per_year=None, match_groups=False):
    """Group by group, year by year. Cached URLs first, then random order
    (fixed seed). per_year=None -> crawl everything."""
    df = df.copy()
    df["year"] = df["published_at"].astype(str).str[:4]
    order = df.groupby("group").size().sort_values().index.tolist()   # smallest first
    total = len(df) if per_year is None else None
    report, table, cap = [], [], {}
    for group in order:
        gp = df[df["group"] == group]
        print(f"\n[{group}] {len(gp)} URLs")
        for year in sorted(gp["year"].unique()):
            target = per_year
            if match_groups and year in cap:
                target = cap[year] if target is None else min(target, cap[year])
            cand = gp[gp["year"] == year].sample(frac=1, random_state=config.RANDOM_SEED)
            cand = cand.assign(_c=cand["source_url"].map(is_cached)).sort_values(
                "_c", ascending=False, kind="stable").drop(columns="_c")
            ok = tried = 0
            for _, row in cand.iterrows():
                if target is not None and ok >= target:
                    break
                res = fetch(row["source_url"])
                tried += 1
                ok += res["status"] == "ok"
                report.append({**row.to_dict(), **res})
                if len(report) % 50 == 0:
                    msg = f"{len(report)}/{total}" if total else f"{len(report)} fetched"
                    print(f"    ... {msg}, full texts so far: {sum(r['status'] == 'ok' for r in report)}")
            table.append({"group": group, "year": year, "available": len(cand),
                          "tried": tried, "full_text": ok,
                          "target": "all" if target is None else target})
            print(f"  {year}: {ok:4d} full texts  (tried {tried} of {len(cand)}"
                  + ("" if target is None else f", target {target}") + ")")
            if match_groups:
                cap[year] = min(cap.get(year, ok), ok)
    return pd.DataFrame(report), pd.DataFrame(table)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=INPUT)
    ap.add_argument("--limit", type=int, default=None, help="quick test: only N random URLs")
    ap.add_argument("--per-year", type=int, default=None,
                    help="stop each group-year at N full texts (default: crawl all)")
    ap.add_argument("--match-groups", action="store_true",
                    help="cap each year at the smallest group's count (equal groups)")
    args = ap.parse_args()

    df = pd.read_csv(args.input, encoding="utf-8-sig")
    df = df[df["source"] == "gdelt_news"].drop_duplicates("source_url").reset_index(drop=True)
    if args.limit:
        df = df.sample(min(args.limit, len(df)), random_state=config.RANDOM_SEED).reset_index(drop=True)
    print(f"[fulltext] {len(df)} URLs from {args.input}")
    print(f"  groups: {df['group'].value_counts().to_dict()}")
    print(f"  >= {HOST_DELAY}s between requests per site; cached in {CACHE_DIR} (rerun = resume)")

    rep, table = crawl(df, args.per_year, args.match_groups)
    if "id" not in rep.columns:
        rep["id"] = ""                      # ids are assigned by merge.py
    os.makedirs(OUT_DIR, exist_ok=True)
    rep[["group", "published_at", "source_url", "status"]].to_csv(
        f"{OUT_DIR}/fetch_report.csv", index=False, encoding="utf-8-sig")
    table.to_csv(f"{OUT_DIR}/fulltext_by_year.csv", index=False, encoding="utf-8-sig")

    def version(col, text_type):
        v = rep[rep[col].fillna("").str.len() > 0].copy()
        v["title"] = v["text"]          # keep the headline as title
        v["text"] = v[col]
        v["text_type"] = text_type
        return v[["id", "group", "language", "source", "source_url", "query", "title",
                  "text", "text_type", "published_at", "collected_at"]]

    summ, full = version("summary", "summary"), version("fulltext", "full")
    if match_groups := args.match_groups:
        # a group crawled early can end up above a group that ran out later ->
        # trim every group to the smallest count in each year
        yr = full["published_at"].astype(str).str[:4]
        mins = table.groupby("year")["full_text"].min()
        full = full[full.groupby([full["group"], yr]).cumcount() < yr.map(mins).fillna(0).values]
        table["full_text"] = table["year"].map(mins).where(
            table["year"].map(mins) < table["full_text"], table["full_text"])
    summ.to_csv(f"{OUT_DIR}/news_en_summary.csv", index=False, encoding="utf-8-sig")
    full.to_csv(f"{OUT_DIR}/news_en_fulltext.csv", index=False, encoding="utf-8-sig")

    print("\n" + "=" * 60 + "\nRESULT\n")
    print(rep.groupby(["group", "status"]).size().unstack(fill_value=0).to_string())
    print("\nfull texts per group and year:")
    print(table.pivot(index="group", columns="year", values="full_text").fillna(0).astype(int).to_string())
    print("\ntotal full texts:", full["group"].value_counts().to_dict(), f"= {len(full)}")
    if len(full):
        print(f"full text length: median {int(full['text'].str.split().map(len).median())} words")
    print(f"\nsaved -> {OUT_DIR}/news_en_fulltext.csv, news_en_summary.csv, fetch_report.csv, fulltext_by_year.csv")


if __name__ == "__main__":
    main()
