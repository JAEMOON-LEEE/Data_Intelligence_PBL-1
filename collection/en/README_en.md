# English news collection and preprocessing

This repository contains the four-group news pipeline (BTS, BLACKPINK,
SEVENTEEN and TWICE). The [Korean README](README.md) documents all commands,
intermediate files and the historical data card. Earlier YouTube pipelines and
scripts such as `analyze_en.py` or `make_final_subset.py` are not included.

Use a Python 3.12 virtual environment and run commands from the repository root:

```bash
python -m pip install -r collection/en/requirements.txt -r preprocessing/en/requirements.txt
python -m spacy download en_core_web_sm
python collection/en/collect_news_en_trial.py
python collection/en/collect_fulltext_en.py
python collection/en/clean_fulltext_en.py
```

The default GDELT pipeline needs no API key. Guardian queries require both
`GUARDIAN_API_KEY` and `guardian` in `config.EN_SOURCES`; the default skips them.
`config.py` automatically loads `.env` if present; [the example](.env.example)
contains only the optional Guardian setting. The trial collector ends at today's
date; `config.END_DATE` only controls the separate `collect_news_gdelt.py` script.

Before merging, move headline CSVs out of `data/raw/` and copy
`data/extra/news_en_fulltext_clean.csv` to `data/raw/news_en_fulltext.csv`.
Use the guarded Python snippet in [README.md](README.md). `merge.py` reads all
CSV files directly in `data/raw/`, excluding its own `all_raw.csv` output.

```bash
python collection/en/merge.py
python preprocessing/en/preprocess_en.py
python preprocessing/en/check_data.py
python collection/en/make_subset_en.py --n 200
```

Intermediate outputs are `data/raw/all_raw.csv`,
`data/processed/en_processed.csv`, `data/raw_subset/all_raw_200.csv` and
`data/processed/en_processed_200.csv`. The committed team-format CSVs are
`data/raw/en/raw_en.csv` and `data/processed/en/processed_en.csv` (800 rows each).
They use different group labels and source values; do not pass them directly to
the default preprocessor. See [preprocessing instructions](../../preprocessing/en/README.md).

`make_repo_export.py` expects the old flat source layout and is not a direct
repository-root command. Its export also writes old README templates. Refer to
the Korean README before using it; do not overwrite the current documentation.

Historical run (2026-10-13): 3,998 headline URLs, 1,777 full texts, 1,502 after
cleaning, then 800 sampled articles. [stats/](stats/README.md) records the full
collection, not just the sample. Crawling again may produce different results.
