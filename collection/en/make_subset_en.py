"""
STEP 5 (optional): make a smaller, equal-size English dataset, e.g. 200 articles
per group (team decision 2026-10-14, to match the Korean side).

Sampling = stratified by YEAR, same rule as the headline collection:
each year gets an equal share (200 / 10 years = 20); years with fewer articles
(e.g. SEVENTEEN 2018) give their unused share to the other years. Fixed seed,
so the subset is reproducible.

Input : data/processed/en_processed.csv   (full 1,502)
        data/raw/all_raw.csv               (same rows, unprocessed)
Output: data/processed/en_processed_200.csv
        data/raw_subset/all_raw_200.csv    (outside data/raw so merge.py ignores it)

Usage:  python make_subset_en.py            # 200 per group
        python make_subset_en.py --n 300
"""
import argparse
import os
import random
from collections import defaultdict

import pandas as pd

import config

PROCESSED = f"{config.PROCESSED_DIR}/en_processed.csv"
RAW = f"{config.RAW_DIR}/all_raw.csv"


def stratified_ids(sub: pd.DataFrame, target: int, seed: int) -> list:
    rng = random.Random(seed)
    by_year = defaultdict(list)
    for i, y in zip(sub["id"], sub["published_at"].astype(str).str[:4]):
        by_year[y].append(i)
    years = sorted(by_year)
    for y in years:
        by_year[y].sort()
        rng.shuffle(by_year[y])
    take = {y: 0 for y in years}
    left = min(target, len(sub))
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
    return [i for y in years for i in by_year[y][: take[y]]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200, help="articles per group")
    args = ap.parse_args()

    p = pd.read_csv(PROCESSED, encoding="utf-8-sig")
    keep = []
    for g, sub in p.groupby("group"):
        ids = stratified_ids(sub, args.n, config.RANDOM_SEED)
        if len(ids) < args.n:
            print(f"  WARNING {g}: only {len(ids)} articles available (< {args.n})")
        keep += ids
    out = p[p["id"].isin(keep)].copy()

    tag = str(args.n)
    dest_p = f"{config.PROCESSED_DIR}/en_processed_{tag}.csv"
    out.to_csv(dest_p, index=False, encoding="utf-8-sig")
    if os.path.exists(RAW):
        r = pd.read_csv(RAW, encoding="utf-8-sig")
        os.makedirs("data/raw_subset", exist_ok=True)
        r[r["id"].isin(keep)].to_csv(f"data/raw_subset/all_raw_{tag}.csv", index=False, encoding="utf-8-sig")

    year = out["published_at"].astype(str).str[:4]
    print(f"{len(out)} articles ({args.n} per group, spread evenly by year, seed {config.RANDOM_SEED})\n")
    print(out.groupby([out["group"], year]).size().unstack(fill_value=0).to_string())
    print(f"\nmedian length: {int(out['text'].str.split().map(len).median())} words")
    print(f"saved -> {dest_p}" + (f", data/raw_subset/all_raw_{tag}.csv" if os.path.exists(RAW) else ""))


if __name__ == "__main__":
    main()
