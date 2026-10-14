"""
STEP 3: clean the crawled full texts (same rules as the 2026-10-13 run).

Removes:
  1. boilerplate pages: the first 200 characters of the body appear on 3+ rows
     (old URLs redirecting to a promo page, e.g. "Pinkvilla Buzz ...", and the
     same story syndicated to several sites)
  2. bodies that never name the group (wrong page extracted, repurposed domains)

Input : data/extra/news_en_fulltext.csv
Output: data/extra/news_en_fulltext_clean.csv
        data/extra/site_list.csv          (articles per site, for the data card)

2026-10-13 result: 1,777 -> 1,502 (263 boilerplate, 12 no group name)
"""
import re

import pandas as pd

IN = "data/extra/news_en_fulltext.csv"
OUT = "data/extra/news_en_fulltext_clean.csv"
SITES = "data/extra/site_list.csv"
NAMES = {"BTS": r"\bbts\b|bangtan", "BLACKPINK": "blackpink",
         "SEVENTEEN": "seventeen", "TWICE": r"\btwice\b"}
BOILER_MIN_REPEAT = 3


def main():
    f = pd.read_csv(IN, encoding="utf-8-sig")
    n0 = len(f)
    head = f["text"].fillna("").str[:200]
    boiler = head.map(head.value_counts()) >= BOILER_MIN_REPEAT
    ment = pd.Series([bool(re.search(NAMES[g], str(t), re.I)) for g, t in zip(f["group"], f["text"])],
                     index=f.index)
    clean = f[~boiler & ment].copy()
    print(f"start {n0} | boilerplate removed {boiler.sum()} | "
          f"no group name removed {(~ment & ~boiler).sum()} | final {len(clean)}")
    print(clean["group"].value_counts().to_string())
    year = clean["published_at"].astype(str).str[:4]
    print(clean.groupby([clean["group"], year]).size().unstack(fill_value=0).to_string())
    site = clean["source_url"].str.extract(r"https?://(?:www\.)?([^/]+)")[0]
    print(f"{site.nunique()} sites"); print(site.value_counts().head(15).to_string())
    site.value_counts().rename_axis("site").rename("articles").to_csv(SITES, encoding="utf-8-sig")
    clean.to_csv(OUT, index=False, encoding="utf-8-sig")
    print(f"saved -> {OUT}, {SITES}")


if __name__ == "__main__":
    main()
