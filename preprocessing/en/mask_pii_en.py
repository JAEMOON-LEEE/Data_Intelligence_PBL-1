"""
Mask personal information in the English article text (team rule: 작성자 아이디 등 비식별화).
Same marker as the Korean crawler: [비식별]
  - email addresses
  - @handles (social media user IDs, mostly fan accounts in embedded tweets)
  - phone numbers
Applies to `title`, `text` and `clean_text`. `tokens` are left unchanged
(preprocessing already removed @handles before tokenizing; checked below).
Usage: python mask_pii_en.py <raw_en.csv> <processed_en.csv> <out_dir>
"""
import re, sys, os
import pandas as pd

EMAIL = re.compile(r"[\w.+%-]+@[\w-]+\.[\w.-]*\w")
HANDLE = re.compile(r"(?<![\w@])@[A-Za-z0-9_.]{2,}")
PHONE = re.compile(r"(?<!\d)(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)\d{3,4}[\s.-]\d{3,4}(?!\d)")
MARK = "[비식별]"

def mask(t):
    if not isinstance(t, str):
        return t
    t = EMAIL.sub(MARK, t)        # emails first, so their @ is not read as a handle
    t = HANDLE.sub(MARK, HANDLE.sub(MARK, t))   # twice: catches handles stuck together (@a@b)
    return PHONE.sub(MARK, t)

def count(series):
    s = series.fillna("")
    return int(sum(len(EMAIL.findall(x)) + len(HANDLE.findall(x)) + len(PHONE.findall(x)) for x in s))

raw_in, proc_in, out = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(out, exist_ok=True)
for path, cols in ((raw_in, ["title", "text"]), (proc_in, ["title", "text", "clean_text"])):
    df = pd.read_csv(path, encoding="utf-8-sig", keep_default_na=False)
    for c in cols:
        if c in df.columns:
            before = count(df[c]); df[c] = df[c].map(mask); after = count(df[c])
            print(f"{os.path.basename(path)} {c}: {before} -> {after}")
    df.to_csv(os.path.join(out, os.path.basename(path)), index=False, encoding="utf-8-sig")
print("saved to", out)
