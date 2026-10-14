"""뉴스엔 직접 검색: 그룹별 200건, 확인된 후보에서 연도별 균등 배분."""
import argparse
import csv
import json
import re
import time
from collections import Counter, defaultdict, deque
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit

import requests
from bs4 import BeautifulSoup
from protego import Protego

BASE, AGENT, KST = "https://www.newsen.com", "NewsenResearchCrawler", timezone(timedelta(hours=9))
GROUPS = {"bts": ("방탄소년단", "BTS"), "블랙핑크": ("블랙핑크", "BLACKPINK"),
          "세븐틴": ("세븐틴", "SEVENTEEN"), "트와이스": ("트와이스", "TWICE"),
          "베이비몬스터": ("베이비몬스터", "BABYMONSTER"), "코르티스": ("코르티스", "CORTIS")}
FIELDS = "id group language source source_url query title text text_type published_at collected_at".split()
DATE = re.compile(r"\b\d{4}-\d{2}-\d{2} \d{2}:\d{2}(?::\d{2})?\b")
BLOCK = re.compile(r"\b(?:noai|notrain|noarchive|nosnippet)\b|"
                   r"(?:크롤링|자동\s*수집|텍스트\s*마이닝|데이터\s*마이닝|AI\s*학습|인공지능\s*학습|수집)"
                   r"\s*(?:을|를|은|는)?\s*(?:금지|불가|제한)|do not (?:crawl|scrape|train)|"
                   r"(?:text|data)\s*mining\s*(?:prohibited|not permitted)", re.I)
NOTICE = re.compile(r"copyright|무단\s*(?:전재|복제)|재배포\s*금지|(?:이용|사용)\s*제한|" + BLOCK.pattern, re.I)
PRIVATE = re.compile(r"[\w.+%-]+@[\w.-]*|(?<!\w)@[\w.]+|"
                     r"(?<!\d)(?:0|\+82[- .]?0?)(?:1[016789]|2|[3-6]\d|70)[- .]?\d{3,4}[- .]?\d{4}(?!\d)|"
                     r"(?<!\d)\d{6}-[1-4]\d{6}(?!\d)|(?:작성자|아이디|닉네임|user[_-]?id)\s*[:=]\s*[\w.@-]+", re.I)

def redact(text):
    return PRIVATE.sub("[비식별]", text)

def related(text, group):
    return any(re.search(r"(?<![A-Za-z])" + re.escape(q) + r"(?![A-Za-z])", text, re.I) for q in GROUPS[group])

class Client:
    def __init__(self, delay):
        self.delay, self.rules = max(2, delay), None
        self.session = requests.Session()
        self.session.headers["User-Agent"] = AGENT + "/1.0"
        response = self.get(BASE + "/robots.txt")
        self.rules = Protego.parse(response.content.decode("utf-8-sig") if response is not None else "")
        rate = self.rules.request_rate(AGENT)
        self.delay = max(self.delay, self.rules.crawl_delay(AGENT) or 0, rate.seconds / rate.requests if rate else 0)

    def get(self, url):
        if not url.startswith(BASE + "/") or (self.rules and not self.rules.can_fetch(url, AGENT)):
            raise RuntimeError(f"호스트/robots.txt 제한: {url}")
        time.sleep(self.delay)
        response = self.session.get(url, timeout=(15, 60), allow_redirects=False)
        if response.status_code in (404, 410):
            return None
        if response.status_code != 200:
            raise RuntimeError(f"HTTP {response.status_code}: 중단 ({url})")
        return response

    def page(self, url):
        response = self.get(url)
        if response is None:
            return None, None
        try:
            html = response.content.decode("utf-8-sig")
        except UnicodeDecodeError:
            html = response.content.decode("cp949")
        soup = BeautifulSoup(html, "html.parser")
        if re.search(r"access denied|too many requests|captcha|접근이?\s*차단|접근\s*제한", soup.get_text(" ", strip=True), re.I):
            raise RuntimeError(f"차단/인증 화면: {url}")
        return response, soup

def restrictions(response, soup):
    directives = response.headers.get("X-Robots-Tag", "")
    for meta in soup.select("meta[name]"):
        name = meta["name"].lower()
        if name in ("robots", AGENT.lower(), "noai", "notrain"):
            directives += " " + (name if name in ("noai", "notrain") else meta.get("content", ""))
    text = soup.get_text("\n", strip=True)
    notes = [redact(line) for line in text.splitlines() if NOTICE.search(line)]
    return notes + ([directives.strip()] if directives.strip() else []), bool(BLOCK.search(directives + " " + text) or re.search(r"\bnone\b", directives, re.I))

def read_article(client, uid, group, query, cutoff, audit):
    url = BASE + "/news_view.php?uid=" + uid
    response, soup = client.page(url)
    row, notes, decision = None, [], "missing"
    if soup is not None:
        notes, blocked = restrictions(response, soup)
        decision = "restricted" if blocked else "invalid"
        if not blocked:
            try:
                title, body = soup.select_one("meta[property='og:title']"), soup.select_one("#CLtag, [itemprop='articleBody']")
                published, headline = soup.select_one("meta[property='article:published_time']"), soup.select_one(".art_title")
                header = headline.find_parent("table") if headline else None
                fallback = DATE.search(header.get_text(" ", strip=True)) if header else None
                if not title or not title.get("content", "").strip() or not body or not (published or fallback):
                    raise ValueError("제목/본문/작성일 누락")
                stamp = datetime.fromisoformat(published["content"] if published else fallback[0])
                stamp = stamp.replace(tzinfo=KST) if stamp.tzinfo is None else stamp.astimezone(KST)
                for node in body.select("script, style, noscript, iframe, img, video, audio, .center_img"):
                    node.decompose()
                raw = re.sub(r"\[[^\]\n]*뉴스엔[^\]\n]*기자\]\s*", "", body.get_text("\n", strip=True))
                text = "\n".join(line for line in raw.splitlines() if not re.match(
                    r"뉴스엔\s+[가-힣]{2,4}\s+\S+@\S*\s*$|기사제보 및 보도자료|copyright|▲", line, re.I))
                if not text.strip():
                    raise ValueError("본문 누락")
                decision = "outside_period" if stamp.year < 2017 or stamp > cutoff else "unrelated"
                if decision != "outside_period" and related(title["content"] + "\n" + text, group):
                    row = dict(zip(FIELDS, ("newsen_" + uid, group, "ko" if re.search(r"[가-힣]", text) else "en", "뉴스엔",
                        url, query, redact(title["content"]), redact(text), "news", stamp.isoformat(), datetime.now(KST).isoformat(timespec="seconds"))))
                    decision = "eligible"
            except (ValueError, KeyError, TypeError) as error:
                decision = str(error)
    audit.write(json.dumps(dict(source_url=url, group=group, query=query, decision=decision, notices=notes,
        http_status=response.status_code if response is not None else None, checked_at=datetime.now(KST).isoformat()), ensure_ascii=False) + "\n")
    audit.flush()
    return row

def candidates(client, group, max_pages, limits):
    for query in GROUPS[group]:
        page, fingerprints = 1, set()
        while not max_pages or page <= max_pages:
            url = BASE + "/news_list.php?" + urlencode(dict(vm="list", searchperiod="all", search="title", searchstring=query, page=page), encoding="euc-kr")
            response, soup = client.page(url)
            if soup is None:
                break
            if restrictions(response, soup)[1]:
                raise RuntimeError(f"검색 페이지 이용 제한: {url}")
            rows = {}
            for link in soup.select("a.line[href*='news_view.php'][href*='searchstring=']"):
                if not link.get_text(strip=True):
                    continue
                uid = parse_qs(urlsplit(link["href"]).query).get("uid", [""])[0]
                table = link.find_parent("table")
                cell = table.select_one("td[align='right'][nowrap]") if table else None
                stamp = DATE.search(cell.get_text(" ", strip=True)) if cell else None
                if not re.fullmatch(r"\d{18}", uid) or not stamp:
                    raise RuntimeError("검색 목록의 ID/작성일 구조가 변경되었습니다.")
                rows[uid] = datetime.fromisoformat(stamp[0]).year
            fingerprint = tuple(rows)
            if not rows or fingerprint in fingerprints:
                limits.append(f"{query}: 빈 목록/페이지 반복, 과거 범위 미확보")
                break
            fingerprints.add(fingerprint)
            if page == 1 or page % 5 == 0:
                print(f"[{group}] 검색 {query} {page}페이지 | 목록 연도 {min(rows.values())}~{max(rows.values())}", flush=True)
            yield from ((uid, query, year) for uid, year in rows.items())
            if not any(parse_qs(urlsplit(a["href"]).query).get("page") == [str(page + 1)] for a in soup.select("a[href*='news_list.php']")):
                break
            page += 1
        else:
            limits.append(f"{query}: 검색 상한 {max_pages}페이지")


def crawl(args):
    cutoff, started = datetime.now(KST), time.monotonic()
    years = list(range(2017, cutoff.year + 1))
    output = Path(args.output)
    audit_path, coverage_path = output.with_suffix(".audit.jsonl"), output.with_suffix(".coverage.csv")
    if any(p.exists() for p in (output, audit_path, coverage_path)):
        raise RuntimeError("결과 파일이 이미 있습니다. 다른 --output을 지정하세요.")
    counts, used, limits = Counter(), set(), defaultdict(list)
    client = Client(args.delay)
    try:
        with output.open("x", encoding="utf-8-sig", newline="") as data, audit_path.open("x", encoding="utf-8") as audit:
            writer = csv.DictWriter(data, fieldnames=FIELDS)
            writer.writeheader()
            data.flush()
            for group in GROUPS:
                pools, seen, total = defaultdict(deque), set(), 0
                print(f"[{group}] 뉴스엔 후보 검색 시작", flush=True)
                for uid, query, year in candidates(client, group, args.max_pages, limits[group]):
                    if uid not in seen and year in years:
                        seen.add(uid)
                        pools[year].append((uid, query, None))
                while total < args.per_group and any(pools.values()):
                    year = min((y for y in years if pools[y]), key=lambda y: (counts[group, y], y))
                    uid, query, row = pools[year].popleft()
                    if uid in used:
                        continue
                    row = row or read_article(client, uid, group, query, cutoff, audit)
                    if row is None:
                        continue
                    actual = datetime.fromisoformat(row["published_at"]).year
                    if actual != year:
                        pools[actual].append((uid, query, row))
                        continue
                    writer.writerow(row)
                    data.flush()
                    used.add(uid)
                    counts[group, actual] += 1
                    total += 1
                    elapsed = time.monotonic() - started
                    eta = timedelta(seconds=int(elapsed * (args.per_group * len(GROUPS) - len(used)) / len(used)))
                    print(f"[{group} {total}/{args.per_group}] 수집 연도 {actual} | 전체 {len(used)}/{args.per_group * len(GROUPS)} | 경과 {timedelta(seconds=int(elapsed))} | 예상 남음 약 {eta}", flush=True)
                print(f"[{group}] 종료 {total}/{args.per_group} | {dict((y, counts[group, y]) for y in years)}", flush=True)
    finally:
        client.session.close()
        with coverage_path.open("x", encoding="utf-8-sig", newline="") as file:
            writer = csv.writer(file)
            writer.writerow("group year baseline_target collected group_total group_shortfall search_limits".split())
            for group in GROUPS:
                total = sum(counts[group, y] for y in years)
                for i, year in enumerate(years):
                    target = args.per_group // len(years) + (i < args.per_group % len(years))
                    writer.writerow([group, year, target, counts[group, year], total, args.per_group - total, " | ".join(limits[group])])
    return len(used) == args.per_group * len(GROUPS)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-group", type=int, default=200)
    parser.add_argument("--delay", type=float, default=3, help="요청 간격: 최소 2초")
    parser.add_argument("--max-pages", type=int, default=0, help="검색어별 페이지 상한: 기본 0이면 목록 끝/반복까지")
    parser.add_argument("--output", default="데이터크롤링.csv")
    args = parser.parse_args()
    if args.per_group < 1 or args.delay < 0 or args.max_pages < 0:
        parser.error("per-group은 1 이상, delay/max-pages는 0 이상이어야 합니다.")
    try:
        if not crawl(args):
            parser.exit(2, "목표 미달: CSV·coverage를 확인하세요. 0건은 검색 범위 내 미확보를 뜻합니다.\n")
    except (requests.RequestException, RuntimeError, OSError, UnicodeError, KeyboardInterrupt) as error:
        parser.exit(1, f"수집 중단: {error}\n")
