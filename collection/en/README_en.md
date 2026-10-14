# K-POP Domestic vs. Overseas — Data Collection & English Preprocessing

Data Intelligence PBL Module #1 (English side). Collects overseas English news
articles about BTS, SEVENTEEN, BLACKPINK and TWICE (GDELT + full-text crawl),
cleans them and preprocesses them for Count/TF-IDF and LDA.
Start with **CURRENT PIPELINE** below; later sections are earlier plans kept for reference.

## Setup

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
cp .env.example .env      # then fill in the keys
```

API keys (all free):
- **YouTube Data API v3** — Google Cloud Console → enable "YouTube Data API v3" → API key
- **Guardian Open Platform** — open-platform.theguardian.com/access (developer key)

Load keys: `export $(cat .env | xargs)` (macOS/Linux), or set them in your IDE.

## CURRENT PIPELINE: 4 groups, English full text (final, 2026-10-13)

Groups: **BTS, SEVENTEEN, BLACKPINK, TWICE** (2 boy + 2 girl groups; HYBE / YG / JYP).
Run in Colab from a Google Drive folder, so caches survive disconnects.

```bash
# STEP 1  headlines (GDELT): up to 1,000 per group, spread evenly by year (2017-now)
python collect_news_en_trial.py
#   -> data/raw/news_en_headlines.csv
#   -> data/check/spotcheck_kept.csv, rejected_<group>.csv   (READ them: filter check)

# STEP 2  full text: crawl every headline URL (resumable, cached)
python collect_fulltext_en.py --limit 40      # quick test
python collect_fulltext_en.py                 # all (~1-1.5 h)
#   -> data/extra/news_en_fulltext.csv, fetch_report.csv, fulltext_by_year.csv

# STEP 3  clean: drop promo/redirect/duplicate pages and bodies without the group name
python clean_fulltext_en.py
#   -> data/extra/news_en_fulltext_clean.csv, site_list.csv

# STEP 4  swap into data/raw (merge.py merges EVERY csv in data/raw), then preprocess
mkdir -p data/headline_version && mv data/raw/news_en_headlines.csv data/headline_version/
cp data/extra/news_en_fulltext_clean.csv data/raw/news_en_fulltext.csv
python merge.py && python preprocess_en.py && python check_data.py
#   -> data/raw/all_raw.csv, data/processed/en_processed.csv  (MAIN FILE for analysis)
```

### STEP 5 (team decision 2026-10-14): 200 articles per group, spread evenly by year
```bash
python make_subset_en.py            # --n 300 for another size
#   -> data/processed/en_processed_200.csv   (800 rows: 200 x 4, ~20 per year)
#   -> data/raw_subset/all_raw_200.csv
```
Years with fewer articles keep all they have (SEVENTEEN 2017: 13, 2018: 7, 2026: 9;
TWICE 2018: 15); their unused share goes to other years. Fixed seed (42).

### Final English dataset (2026-10-13 run)

| Stage | Rows |
|---|---|
| GDELT headlines (filtered, 1,000 per group, even by year) | 3,998 unique URLs |
| Full text crawled (`ok`) | 1,777 (44%) |
| After cleaning (step 3) | **1,502** |
| After preprocessing | 1,502 (none too short / duplicate) |

Per group: SEVENTEEN 412, BLACKPINK 377, BTS 364, TWICE 349. Median length 358 words.

Articles per year:

| | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|
| BLACKPINK | 15 | 33 | 32 | 34 | 33 | 39 | 42 | 54 | 57 | 38 |
| BTS | 33 | 31 | 28 | 17 | 32 | 34 | 36 | 50 | 54 | 49 |
| SEVENTEEN | 13 | 7 | 22 | 21 | 53 | 70 | 53 | 90 | 74 | 9 |
| TWICE | 19 | 15 | 30 | 38 | 38 | 34 | 55 | 54 | 48 | 18 |

### Data card notes (English side)

**Source and method**
- Articles found via GDELT DOC 2.0 (worldwide English-language news), Korean
  outlets and their English editions excluded -> overseas coverage only. 2017-now
  (GDELT's index starts 2017). Timestamps in UTC.
- Full text fetched from the publisher pages with trafilatura.

**Responsible collection**
- robots.txt checked for every site; disallowed or unreadable -> skipped.
- Honest User-Agent naming the course project; >= 3 s between requests per site.
- theguardian.com skipped (Guardian developer registration: full text not stored).
- Text used for aggregate analysis only; NOT redistributed (keep `all_raw.csv` and
  `en_processed.csv` out of public repositories).

**Filters**
- Headline must name the group. Ambiguous names: "TWICE"/"BTS" must be written in
  capitals or appear with a K-pop word / member name; ordinary uses removed
  ("twice as", "won twice", BTS Skytrain, "behind the scenes"); "Seventeen" magazine,
  ages and the Indonesian band removed.
- Headlines naming 2+ candidate groups dropped (one article = one group).
- Spam removed: APK/MP3/wallpaper downloads, lyrics/chord pages, quizzes, petitions.
- Step 3: 263 boilerplate pages (promo redirects, syndicated duplicates) and 12
  bodies that never name the group removed.

**Preprocessing** (`preprocess_en.py`)
- spaCy lemmatization, nouns/proper nouns/adjectives/verbs only, stopwords
  (spaCy + domain list), group names removed as stopwords, publisher endings
  stripped from headlines.
- Member names normalized before cleaning so they survive: S.Coups -> Scoups,
  J-Hope -> Jhope, V -> Taehyung (BTS rows), The8 -> Minghao, Rose/Rosé -> Roseanne.

**Limitations (state these)**
- 56% of crawls failed: robots.txt disallowed (~40% of URLs, mostly K-pop
  specialist sites), 403 blocked, 404/410 deleted, or no article body.
- Source skew: 290 sites; top = Billboard, Pinkvilla, Times of India. About 20% of
  articles come from Indian outlets, because K-pop specialist sites block crawling.
- BTS had the lowest crawl success (39%).
- Thin years: 2017-2018 for all groups; SEVENTEEN before 2021 and in 2026 (partial
  year). Compare groups over the whole period; treat per-year results for thin
  years as low-confidence.
- GDELT sometimes writes "BTS" as "BT" in headlines, so a few two-group headlines
  slipped past the multi-group filter.
- TWICE headlines in title case without any K-pop word ("Twice tops chart") are
  dropped by design (precision over recall); see data/check/rejected_TWICE.csv.

### Older versions (kept for the record)
- 2-group final (BLACKPINK + SEVENTEEN, 500 headlines each): `make_final_subset.py`
  -> `data/raw/news_en_final_bp_svt.csv`. Group choice evidence: `data/trial_4groups/`.

## Run order: English news trial (originally 4 groups)

```bash
python collect_news_en_trial.py  # Guardian + GDELT, 500/group, spread by year (~20 min)
python merge.py
python preprocess_en.py
python check_data.py
python analyze_en.py             # optional for the trial
```

## Run order: full pipeline (news + YouTube comments)

```bash
python collect_youtube.py    # ko + en comments  -> data/raw/youtube_comments_*.csv
python collect_news_gdelt.py # English news headlines, non-Korean outlets (no key) -> data/raw/news_en_gdelt_*.csv
# python collect_news_en.py  # Guardian (optional; covers only BTS/BLACKPINK well)
python merge.py              # one file + ids    -> data/raw/all_raw.csv
python preprocess_en.py      # English           -> data/processed/en_processed.csv
python check_data.py         # pilot report
python analyze_en.py         # frequency, word clouds, Count vs TF-IDF, LDA -> results/en/ (start with summary.md)
```

Edit groups, debut dates, targets and video IDs in `config.py` only.

## Schema

`id, group, language, source, source_url, query, title, text, text_type, published_at, collected_at`

| column | meaning |
|---|---|
| id | `<lang>_<source>_<n>`, assigned in merge.py |
| source | `youtube`, `gdelt_news`, `guardian` |
| query | search keyword, or `video:<id>` for comments |
| text_type | `headline` (GDELT), `summary` (Guardian standfirst), `full`, `comment` |
| published_at | UTC, ISO-8601 |

Processed file adds: `clean_text`, `tokens` (space-joined lemmas), `n_tokens`.

## Ethics notes for the comment pipeline (earlier plan, not used for the final English data)

- No author names or comment IDs are collected (de-identification by design).
  YouTube rows link to the video, not the individual comment.
- Naver returns summaries only; the Guardian is set to summaries too
  (`GUARDIAN_TEXT` in config) so both languages use comparable text length.
- Guardian developer keys are non-commercial; confirm their terms cover
  text/data mining for coursework before submitting.
- YouTube comments sorted by `relevance` skew toward top-liked (fan) comments.
- Comment language: Korean = Hangul ≥ 30% of letters; English = detected by
  `lingua` (limited to common K-pop fan languages). Mixed-language comments
  that fit neither are dropped.
- Naver API has no date filter; check the date distribution in `check_data.py`.

## Pilot pass/fail checks (agree with the team)

1. Date distribution actually spans debut → now (not just recent months)
2. ≥ 400 English comments per group survive cleaning
3. Enough Korean comments per group (MV comments are mostly non-Korean)
4. LDA test run gives labelable topics

## English news: why GDELT (background)

The Guardian returned 380 BTS / 137 BLACKPINK / 2 CORTIS / 0 BABYMONSTER articles:
Western mainstream press barely covers rookie groups. GDELT indexes worldwide
English-language news (incl. international entertainment / K-pop media), so all
four groups come from the SAME source. Limits for the data card:
- headlines only (GDELT provides no article text)
- Korean outlets and their English editions are excluded (overseas coverage only)
- GDELT officially guarantees only the last ~3 months; older windows usually work
  but check the real date spread in check_data.py
