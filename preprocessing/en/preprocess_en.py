"""
English preprocessing: tokenization, lemmatization, stopword removal.

Steps (write these in the report):
 1. Clean: HTML entities/tags, URLs, @mentions, '#' symbol, emojis, numbers
 2. Lowercase
 3. spaCy (en_core_web_sm): tokenize + lemmatize ("performances" -> "performance")
 4. Keep content words only: NOUN, PROPN, ADJ, VERB
 5. Remove stopwords: spaCy list + domain list below (+ group names, optional)
 6. Drop tokens shorter than 2 letters; drop docs with < MIN_TOKENS tokens
 7. Drop duplicate documents (same cleaned text within a group)
 8. Comments: sample down to COMMENTS_PER_LANG per group (fixed seed)

Output columns = original schema + clean_text, tokens, n_tokens
`tokens` is space-joined -> feed straight into CountVectorizer / TfidfVectorizer.

Usage:  python preprocess_en.py [input_csv]   (default: data/raw/all_raw.csv)
"""

# --- repo layout: config.py and common.py live in collection/en/ ---
import os as _os, sys as _sys
_here = _os.path.dirname(_os.path.abspath(__file__))
for _p in (_here, _os.path.join(_here, "..", "..", "collection", "en")):
    if _os.path.exists(_os.path.join(_p, "config.py")) and _p not in _sys.path:
        _sys.path.insert(0, _p)
# -------------------------------------------------------------------

import os
import re
import sys

import pandas as pd

import config

MIN_TOKENS = 3
KEEP_POS = {"NOUN", "PROPN", "ADJ", "VERB"}

# Words that appear everywhere in K-pop text and carry no comparison value.
# Adjust after looking at the first frequency chart — and document changes.
DOMAIN_STOPWORDS = {
    "kpop", "k", "pop", "song", "songs", "video", "mv", "music", "group",
    "member", "members", "like", "get", "go", "make", "say", "know",
    "think", "lol", "omg", "guy", "thing", "really", "just", "also",
    "year", "time", "new", "one", "first",
    # added after pilot run (2026-10-08): generic verbs / meta-talk that
    # appeared in every group's top words without saying anything about it
    "let", "come", "look", "watch", "want", "feel", "comment",
    # added after the news-headline check (2026-10-13): publisher word and
    # group-type labels ("girl group", "boy band") that only describe the type
    "news", "girl", "boy", "band",
}
# Map variants to one form after lemmatization (pilot: "armys" vs "army").
# Member names are deliberately KEPT: they are a finding, not noise.
NORMALIZE = {"armys": "army", "blinks": "blink", "streaming": "stream", "scoup": "scoups"}

# Member-name fixes applied to the RAW text before cleaning (accents would be
# stripped, and "Rose" can be read as the verb "rise").
#   (pattern, replacement, groups or None for all)
NAME_FIX = [
    (r"\bros[eé]\b", "Roseanne", {"BLACKPINK"}),   # BLACKPINK rows: Rose/Rosé = the member
    (r"\brosé\b", "Roseanne", None),                # accented form is always the member
    # added 2026-10-13 (full-text check): names that cleaning would break
    #   S.Coups -> "s coups" -> lemma "coup";  J-Hope -> dropped (not alphabetic)
    #   V -> dropped (1 letter);  The8 -> "the" (stopword)
    (r"\bs\s*\.?\s*coups\b", "Scoups", {"SEVENTEEN"}),
    (r"\bj\s*-?\s*hope\b", "Jhope", None),
    (r"(?<!Vol\. )(?<!Vol )(?<!Part )(?-i:\bV\b)(?!\s*\.)", "Taehyung", {"BTS"}),   # capital V only, not "V." abbreviations
    (r"(?-i:\bThe\s?8\b|\bTHE\s?8\b)", "Minghao", {"SEVENTEEN"}),
]

# Headlines often end with the publisher ("... – Manila Bulletin",
# "... : Bollywood News"). An ending that repeats >= OUTLET_MIN_REPEAT times
# in the corpus is treated as a publisher name and removed (data-driven).
OUTLET_SEP = re.compile(r"\s+(?:–|—|\||:)\s+(?=[^–—|:]+$)")
OUTLET_MIN_REPEAT = 3
# Group names dominate every count chart; removing them shows what people
# say ABOUT the group. Set False if the team wants to keep them.
REMOVE_GROUP_NAMES = True

URL_RE = re.compile(r"https?://\S+|www\.\S+")
MENTION_RE = re.compile(r"@\w+")
NON_ALPHA_RE = re.compile(r"[^a-zA-Z\s'-]")
SPACE_RE = re.compile(r"\s+")


def load_nlp():
    import spacy
    try:
        return spacy.load("en_core_web_sm", disable=["ner", "parser"])
    except OSError:
        raise SystemExit("Run first:  python -m spacy download en_core_web_sm")


def build_stopwords(nlp) -> set:
    stops = set(nlp.Defaults.stop_words) | DOMAIN_STOPWORDS
    if REMOVE_GROUP_NAMES:
        for info in config.GROUPS.values():
            for name in info["en_names"]:
                stops |= set(name.lower().split())
    return stops


def clean_text(text: str) -> str:
    import html
    text = html.unescape(str(text))
    text = re.sub(r"<[^>]+>", " ", text)
    text = URL_RE.sub(" ", text)
    text = MENTION_RE.sub(" ", text)
    text = text.replace("#", " ")
    text = NON_ALPHA_RE.sub(" ", text)  # emojis, numbers, symbols
    return SPACE_RE.sub(" ", text).strip().lower()


def tokenize(docs, nlp, stops) -> list:
    out = []
    for doc in nlp.pipe(docs, batch_size=256):
        toks = []
        for t in doc:
            lemma = t.lemma_.lower().strip("'-")
            lemma = NORMALIZE.get(lemma, lemma)
            if (
                t.pos_ in KEEP_POS
                and len(lemma) >= 2
                and lemma.isalpha()
                and lemma not in stops
                and t.text.lower() not in stops
            ):
                toks.append(lemma)
        out.append(toks)
    return out


def fix_names(text: str, group: str) -> str:
    for pat, rep, groups in NAME_FIX:
        if groups is None or group in groups:
            text = re.sub(pat, rep, text, flags=re.I)
    return text


def strip_outlets(texts: pd.Series) -> tuple:
    """Remove publisher endings that repeat across the corpus."""
    def tail(t):
        parts = OUTLET_SEP.split(t)
        return parts[-1].strip().lower() if len(parts) > 1 else None
    tails = texts.map(tail)
    counts = tails.value_counts()
    outlets = set(counts[counts >= OUTLET_MIN_REPEAT].index)
    def strip(t):
        parts = OUTLET_SEP.split(t)
        if len(parts) > 1 and parts[-1].strip().lower() in outlets:
            return " ".join(parts[:-1]).strip()
        return t
    return texts.map(strip), sorted(outlets)


def preprocess(df: pd.DataFrame, nlp) -> pd.DataFrame:
    df = df[df["language"] == "en"].copy()
    keep = getattr(config, "EN_SOURCES", None)
    if keep:
        dropped = (~df["source"].isin(keep)).sum()
        df = df[df["source"].isin(keep)].copy()
        if dropped:
            print(f"sources kept: {keep} ({dropped} rows from other sources removed)")
    stops = build_stopwords(nlp)
    n0 = len(df)

    df["text"] = [fix_names(str(t), g) for t, g in zip(df["text"].fillna(""), df["group"])]
    df["title"] = [fix_names(str(t), g) for t, g in zip(df["title"].fillna(""), df["group"])]
    # Headlines live in `text` (headline version) or in `title` (summary/full
    # versions). Publisher endings are detected across ALL headlines together
    # and stripped from whichever column holds them.
    is_head = df["text_type"] == "headline"
    has_title = df["title"].fillna("").str.len() > 0
    heads = pd.concat([df.loc[is_head, "text"], df.loc[has_title, "title"]])
    if len(heads):
        _, outlets = strip_outlets(heads)
        outlet_set = set(outlets)

        def strip_known(t):
            parts = OUTLET_SEP.split(t)
            if len(parts) > 1 and parts[-1].strip().lower() in outlet_set:
                return " ".join(parts[:-1]).strip()
            return t

        df.loc[is_head, "text"] = df.loc[is_head, "text"].map(strip_known)
        df.loc[has_title, "title"] = df.loc[has_title, "title"].map(strip_known)
        if outlets:
            print(f"publisher endings removed ({len(outlets)}): {', '.join(outlets[:15])}"
                  + (" ..." if len(outlets) > 15 else ""))

    # news: title + summary/body together; comments: text only
    combined = (df["title"].fillna("") + ". " + df["text"].fillna("")).where(
        df["title"].fillna("") != "", df["text"].fillna("")
    )
    df["clean_text"] = combined.map(clean_text)
    df["tokens_list"] = tokenize(df["clean_text"].tolist(), nlp, stops)
    df["n_tokens"] = df["tokens_list"].map(len)
    df["tokens"] = df["tokens_list"].map(" ".join)
    df = df.drop(columns="tokens_list")

    short = df["n_tokens"] < MIN_TOKENS
    df = df[~short]
    dup = df.duplicated(subset=["group", "clean_text"])
    df = df[~dup]

    # comments: sample to the agreed size per group
    is_c = df["text_type"] == "comment"
    comments = (
        df[is_c].sample(frac=1, random_state=config.RANDOM_SEED)  # shuffle
        .groupby("group").head(config.COMMENTS_PER_LANG)          # keep N per group
    )
    df = pd.concat([df[~is_c], comments]).sort_values(["source", "group", "published_at"])

    print(f"English rows: {n0} -> {len(df)}  (too short: {short.sum()}, duplicates: {dup.sum()})")
    print(df.groupby(["group", "source"]).size().unstack(fill_value=0).to_string())
    has_comments = (df["text_type"] == "comment").any()
    for g, sub in df.groupby("group"):
        n = (sub["text_type"] == "comment").sum()
        if has_comments and n < config.COMMENTS_PER_LANG:
            print(f"  WARNING {g}: only {n} comments after cleaning (target {config.COMMENTS_PER_LANG})")
    return df.reset_index(drop=True)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else f"{config.RAW_DIR}/all_raw.csv"
    df = pd.read_csv(path, encoding="utf-8-sig")
    out = preprocess(df, load_nlp())
    os.makedirs(config.PROCESSED_DIR, exist_ok=True)
    dest = f"{config.PROCESSED_DIR}/en_processed.csv"
    out.to_csv(dest, index=False, encoding="utf-8-sig")
    print(f"saved -> {dest}")


if __name__ == "__main__":
    main()
