"""
Merge all raw CSVs into one file and assign the unique `id`.

- Drops duplicates (same source_url + text).
- id format: <lang>_<source>_<number>, e.g. en_youtube_000123

Usage:  python merge.py
"""
import glob

import pandas as pd

import config
from common import COLUMNS


def main():
    files = sorted(glob.glob(f"{config.RAW_DIR}/*.csv"))
    files = [f for f in files if not f.endswith("all_raw.csv")]
    if not files:
        raise SystemExit(f"No CSVs in {config.RAW_DIR}. Run the collectors first.")
    df = pd.concat([pd.read_csv(f, encoding="utf-8-sig") for f in files], ignore_index=True)
    before = len(df)
    df = df.drop_duplicates(subset=["source_url", "text"]).reset_index(drop=True)
    df = df.sort_values(["language", "source", "group", "published_at"]).reset_index(drop=True)
    df["id"] = (
        df["language"] + "_" + df["source"] + "_"
        + df.groupby(["language", "source"]).cumcount().add(1).astype(str).str.zfill(6)
    )
    df = df[COLUMNS]
    out = f"{config.RAW_DIR}/all_raw.csv"
    df.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"merged {len(files)} files: {before} rows -> {len(df)} after dedupe -> {out}")


if __name__ == "__main__":
    main()
