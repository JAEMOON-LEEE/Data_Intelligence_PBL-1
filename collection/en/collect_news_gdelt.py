"""
Collect English-language news HEADLINES from non-Korean outlets via GDELT.

Why: the Guardian barely covers rookie groups (BABYMONSTER 0, CORTIS 2).
GDELT indexes thousands of news sites worldwide, including international
K-pop/entertainment media, and needs no API key.

What you get (write this in the data card):
- Headline + URL + outlet country + date. GDELT does NOT provide article
  text, so `text` = headline, text_type = "headline".
- Korean outlets are excluded (sourcecountry South Korea, .kr domains, and
  Korean media's English editions) so the corpus is "overseas" coverage.
- GDELT officially supports only the most recent ~3 months. Older windows
  often still return results, but not guaranteed. check_data.py shows the
  real date spread.

Usage:  python collect_news_gdelt.py
"""
import json
import re
import time
from datetime import date, datetime, timedelta
from urllib.parse import urlparse

import requests

import config
from common import mentions_group, now_utc, save

URL = "https://api.gdeltproject.org/api/v2/doc/doc"
WINDOW_DAYS = 91          # one request per quarter
EARLIEST = date(2017, 1, 1)  # GDELT full-text index starts around here
PAUSE = 6                 # seconds between requests (GDELT asks for ~1 per 5s)

# Korean media in English: domestic, not overseas -> exclude.
KOREAN_DOMAINS = (
    "koreaherald.com", "koreatimes.co.kr", "joongang.co.kr", "joins.com",
    "yna.co.kr", "khan.co.kr", "chosun.com", "donga.com", "hani.co.kr",
    "kbs.co.kr", "sbs.co.kr", "mbc.co.kr", "arirang.com", "kpopherald.com",
    "starnewskorea.com", "koreajoongangdaily.joins.com", "fnnews.com",
    "newsis.com", "news1.kr", "mk.co.kr", "hankyung.com", "sedaily.com",
    "osen.co.kr", "osenworld.com", "tenasia.com", "xportsnews.com",
)


def gdelt_query(info: dict) -> str:
    names = [n for n in info["en_names"]]
    terms = " OR ".join(f'"{n}"' if " " in n else n for n in names)
    terms = f"({terms})" if len(names) > 1 else terms
    return f"{terms} sourcelang:english -sourcecountry:KS"


_BAD_ESCAPE = re.compile(r'\\(?![\"\\/bfnrtu])')


def parse_json(text: str):
    """GDELT sometimes returns slightly broken JSON (raw control characters or
    invalid backslash escapes inside headlines). Try strict, then lenient."""
    text = (text or "").strip()
    if not text.startswith("{"):
        return None
    for candidate in (text, _BAD_ESCAPE.sub(r"\\\\", text)):
        try:
            return json.loads(candidate, strict=False)
        except ValueError:
            continue
    return None


class QueryRejected(Exception):
    """GDELT refused the query itself (e.g. a keyword it considers too short)."""


def fetch(query: str, start: date, end: date):
    """Return a list of articles, [] if GDELT truly has none, or None if the
    request FAILED (rate limit / timeout). Callers must not treat None as 0."""
    params = {
        "query": query, "mode": "artlist", "format": "json", "maxrecords": 250,
        "sort": "hybridrel",
        "startdatetime": start.strftime("%Y%m%d000000"),
        "enddatetime": end.strftime("%Y%m%d235959"),
    }
    for wait in (0, 15, 30, 60):
        time.sleep(wait)
        try:
            r = requests.get(URL, params=params, timeout=60)
        except requests.RequestException:
            continue                      # timeout / connection reset -> retry
        if r.status_code == 429:
            continue
        parsed = parse_json(r.text)
        if parsed is not None:
            return parsed.get("articles", [])
        msg = r.text.strip()[:120]
        if not msg:
            return []                     # GDELT sends an empty body when nothing matches
        if "limit" in msg.lower() or "slow down" in msg.lower():
            continue
        if any(w in msg.lower() for w in ("too short", "too common", "invalid query",
                                          "parentheses", "illegal character")):
            raise QueryRejected(msg)
        print(f"    GDELT unreadable reply: {msg[:80]}")
        return None
    return None


def is_korean_outlet(item: dict) -> bool:
    domain = (item.get("domain") or urlparse(item.get("url", "")).netloc).lower()
    return (
        domain.endswith(".kr")
        or any(domain.endswith(d) for d in KOREAN_DOMAINS)
        or (item.get("sourcecountry") or "").lower() in ("south korea", "korea, south")
    )


def parse(item: dict, group: str, query: str) -> dict:
    seen = datetime.strptime(item["seendate"], "%Y%m%dT%H%M%SZ")
    return {
        "group": group,
        "language": "en",
        "source": "gdelt_news",
        "source_url": item.get("url", ""),
        "query": query,
        "title": "",                       # headline lives in text (no body available)
        "text": (item.get("title") or "").strip(),
        "text_type": "headline",
        "published_at": seen.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "collected_at": now_utc(),
    }


def even_sample(rows: list, n: int) -> list:
    rows = sorted(rows, key=lambda r: r["published_at"])
    if len(rows) <= n:
        return rows
    step = len(rows) / n
    return [rows[int(i * step)] for i in range(n)]


def collect_group(group: str, info: dict) -> list:
    query = gdelt_query(info)
    start = max(date.fromisoformat(info["debut"]), EARLIEST)
    end_all = date.fromisoformat(config.END_DATE) if config.END_DATE else date.today()
    rows, seen_urls, seen_titles = [], set(), set()
    dropped_kr = 0
    while start <= end_all:
        end = min(start + timedelta(days=WINDOW_DAYS - 1), end_all)
        arts = fetch(query, start, end)
        if arts is None:
            print(f"    {start} ~ {end}: FAILED (GDELT rate limit), skipped")
            start = end + timedelta(days=1)
            time.sleep(PAUSE)
            continue
        kept = 0
        for a in arts:
            if (a.get("language") or "English") != "English":
                continue
            if is_korean_outlet(a):
                dropped_kr += 1
                continue
            row = parse(a, group, query)
            key_t = row["text"].lower()
            if not row["text"] or row["source_url"] in seen_urls or key_t in seen_titles:
                continue
            if not mentions_group(row["text"], info["en_names"]):
                continue  # headline must actually name the group
            seen_urls.add(row["source_url"])
            seen_titles.add(key_t)
            rows.append(row)
            kept += 1
        print(f"    {start} ~ {end}: {len(arts)} returned, {kept} kept")
        start = end + timedelta(days=1)
        time.sleep(PAUSE)
    sampled = even_sample(rows, config.NEWS_PER_LANG)
    flag = "" if len(sampled) >= config.NEWS_PER_LANG else "  <- SHORT"
    print(f"  {group}: {len(rows)} usable headlines "
          f"(Korean outlets dropped: {dropped_kr}), kept {len(sampled)}{flag}")
    return sampled


def main():
    rows = []
    for group, info in config.GROUPS.items():
        print(f"[GDELT] {group}   query: {gdelt_query(info)}")
        rows += collect_group(group, info)
    save(rows, f"{config.RAW_DIR}/news_en_gdelt_{date.today():%Y%m%d}.csv")


if __name__ == "__main__":
    main()
