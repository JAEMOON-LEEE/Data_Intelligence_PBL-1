"""
Build the GitHub upload for the team repo (JAEMOON-LEEE/Data_Intelligence_PBL-1),
in the repo's folder layout and the SAME format as data/raw/ko/raw_ko.csv.

Format changes (English data -> team format, matching the Korean file):
  group        BTS/BLACKPINK/SEVENTEEN/TWICE -> bts/블랙핑크/세븐틴/트와이스
  source       gdelt_news -> the outlet's domain (e.g. billboard.com)
  text_type    full -> news
  published_at UTC "2017-01-23T05:03:27Z" -> KST "2017-01-23 14:03:27"
  collected_at UTC -> KST ISO "2026-10-13T22:14:05+09:00"

Output (folder repo_export/, copy its contents into the repo root):
  collection/en/        collection code + README (Korean data card) + stats/
  preprocessing/en/     preprocess_en.py, check_data.py (+ README)
  data/raw/en/raw_en.csv               200 per group, team schema
  data/processed/en/processed_en.csv   same rows + clean_text, tokens, n_tokens

Usage (run inside the kpop_en folder, after make_subset_en.py):
  python make_repo_export.py               # with article text
  python make_repo_export.py --no-text     # public-repo safe: no article text,
                                           # headline + URL + tokens only
"""
import argparse
import os
import shutil

import pandas as pd

OUT = "repo_export"
RAW_IN = "data/raw_subset/all_raw_200.csv"
PROC_IN = "data/processed/en_processed_200.csv"
GROUP_MAP = {"BTS": "bts", "BLACKPINK": "블랙핑크", "SEVENTEEN": "세븐틴", "TWICE": "트와이스"}
TEAM_COLS = ["id", "group", "language", "source", "source_url", "query", "title", "text",
             "text_type", "published_at", "collected_at"]
COLLECTION_CODE = ["config.py", "common.py", "collect_news_gdelt.py", "collect_news_en_trial.py",
                   "collect_fulltext_en.py", "clean_fulltext_en.py", "make_subset_en.py", "merge.py",
                   "make_repo_export.py", "requirements.txt"]
PREPROCESS_CODE = ["preprocess_en.py", "check_data.py"]
STATS = ["data/extra/site_list.csv", "data/extra/fulltext_by_year.csv", "data/extra/fetch_report.csv"]

# lets preprocessing/en/*.py find config.py / common.py in collection/en/
PATH_FIX = '''
# --- repo layout: config.py and common.py live in collection/en/ ---
import os as _os, sys as _sys
_here = _os.path.dirname(_os.path.abspath(__file__))
for _p in (_here, _os.path.join(_here, "..", "..", "collection", "en")):
    if _os.path.exists(_os.path.join(_p, "config.py")) and _p not in _sys.path:
        _sys.path.insert(0, _p)
# -------------------------------------------------------------------
'''

PREPROCESS_README = """# 영어 전처리 코드

- `preprocess_en.py`: 정제(HTML, URL, 숫자, 기호 제거) → 소문자 → spaCy 표제어 추출 →
  명사/고유명사/형용사/동사만 사용 → 불용어 제거(spaCy + 도메인 불용어, 그룹명).
  멤버 이름은 정제 전에 통일: S.Coups → Scoups, J-Hope → Jhope, V → Taehyung(BTS),
  The8 → Minghao, Rose/Rosé → Roseanne.
- `check_data.py`: 그룹/연도별 개수, 본문 길이, 그룹별 상위 단어 확인.

설정 파일(`config.py`, `common.py`)은 `collection/en/`에 있습니다 (자동으로 찾음).
전체 실행 순서와 데이터 카드는 `collection/en/README.md` 참고.
"""

REPO_NOTE = """> **GitHub 저장소 구조 안내**: 이 폴더(`collection/en/`)의 코드는 원래 한 폴더에서
> 실행하도록 만들어졌습니다. 다시 실행하려면 `collection/en/`과 `preprocessing/en/`의
> `.py` 파일을 한 폴더에 모아서 아래 순서대로 실행하세요.
> 최종 데이터: `data/raw/en/raw_en.csv`, `data/processed/en/processed_en.csv`
> (그룹당 200건, 한국어 데이터와 같은 컬럼 형식).

"""


def to_kst(series, fmt):
    ts = pd.to_datetime(series, utc=True, errors="coerce").dt.tz_convert("Asia/Seoul")
    return ts.dt.strftime(fmt).fillna("")


def team_format(df):
    df = df.copy()
    unknown = set(df["group"]) - set(GROUP_MAP)
    if unknown:
        raise SystemExit(f"unexpected groups: {unknown}")
    df["group"] = df["group"].map(GROUP_MAP)
    df["source"] = df["source_url"].str.extract(r"https?://(?:www\.)?([^/]+)")[0].fillna("")
    df["text_type"] = "news"
    df["published_at"] = to_kst(df["published_at"], "%Y-%m-%d %H:%M:%S")
    df["collected_at"] = to_kst(df["collected_at"], "%Y-%m-%dT%H:%M:%S+09:00")
    return df


def copy_with_path_fix(src, dst):
    code = open(src, encoding="utf-8").read()
    if code.startswith('"""'):
        end = code.index('"""', 3) + 3
        code = code[:end] + "\n" + PATH_FIX + code[end:]
    else:
        code = PATH_FIX + code
    open(dst, "w", encoding="utf-8").write(code)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-text", action="store_true",
                    help="leave article text out (for a PUBLIC repo)")
    args = ap.parse_args()
    for f in (RAW_IN, PROC_IN):
        if not os.path.exists(f):
            raise SystemExit(f"missing {f}: run make_subset_en.py first")

    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    d = {k: os.path.join(OUT, k) for k in
         ("collection/en", "collection/en/stats", "preprocessing/en", "data/raw/en", "data/processed/en")}
    for p in d.values():
        os.makedirs(p, exist_ok=True)

    raw = team_format(pd.read_csv(RAW_IN, encoding="utf-8-sig"))[TEAM_COLS]
    proc = team_format(pd.read_csv(PROC_IN, encoding="utf-8-sig"))
    proc = proc[TEAM_COLS + ["clean_text", "tokens", "n_tokens"]]
    if args.no_text:
        raw["text"] = ""
        proc["text"] = ""
        proc["clean_text"] = ""
    raw.to_csv(f"{d['data/raw/en']}/raw_en.csv", index=False, encoding="utf-8-sig")
    proc.to_csv(f"{d['data/processed/en']}/processed_en.csv", index=False, encoding="utf-8-sig")

    for f in COLLECTION_CODE:
        if os.path.exists(f):
            shutil.copy(f, d["collection/en"])
        else:
            print(f"  (skipped, not found: {f})")
    for f in PREPROCESS_CODE:
        copy_with_path_fix(f, os.path.join(d["preprocessing/en"], f))
    for f in STATS:
        if os.path.exists(f):
            shutil.copy(f, d["collection/en/stats"])
    if os.path.exists("README_ko.md"):
        body = open("README_ko.md", encoding="utf-8").read()
        title, rest = body.split("\n", 1)
        open(f"{d['collection/en']}/README.md", "w", encoding="utf-8").write(title + "\n\n" + REPO_NOTE + rest)
    if os.path.exists("README.md"):
        shutil.copy("README.md", f"{d['collection/en']}/README_en.md")
    open(f"{d['preprocessing/en']}/README.md", "w", encoding="utf-8").write(PREPROCESS_README)

    # ---- report
    print(f"rows: raw {len(raw)}, processed {len(proc)}" + ("   (NO article text)" if args.no_text else ""))
    print("groups:", raw["group"].value_counts().to_dict())
    print("text_type:", raw["text_type"].unique().tolist(), "| language:", raw["language"].unique().tolist())
    yr = raw["published_at"].str[:4]
    print(raw.groupby([raw["group"], yr]).size().unstack(fill_value=0).to_string())
    print("example dates:", raw["published_at"].iloc[0], "|", raw["collected_at"].iloc[0])
    print("top sources:", raw["source"].value_counts().head(5).to_dict())
    print(f"\nfiles in {OUT}/:")
    for root, _, files in sorted(os.walk(OUT)):
        for f in sorted(files):
            p = os.path.join(root, f)
            print(f"  {p[len(OUT) + 1:]:55s} {os.path.getsize(p) / 1024:8.0f} KB")


if __name__ == "__main__":
    main()
