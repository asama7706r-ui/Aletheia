"""Check that every quotation in cases_coded.json occurs verbatim in the file it names.
Matching ignores differences in whitespace only (runs of spaces, newlines and form feeds count as one space).
Clifford quotations (S06) are checked against the coder's own clifford_transcription.txt.
Usage: python -I check_quotes.py   (run from history_ladder_test/)"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
SRC = "coder_package/sources"
CLIFF = "coder_returned/clifford_transcription.txt"


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


texts = {}
for f in os.listdir(SRC):
    if f.endswith(".txt"):
        texts[f] = norm(open(os.path.join(SRC, f), encoding="utf-8", errors="replace").read())
texts["clifford_transcription.txt"] = norm(open(CLIFF, encoding="utf-8", errors="replace").read())


def resolve(name):
    base = os.path.basename(name or "")
    if base.startswith("S06") or "clifford" in base.lower():
        return "clifford_transcription.txt"
    for k in texts:
        if k == base or k.split("_")[0] == base.split("_")[0].split(".")[0]:
            return k
    return None


cases = json.load(open("coder_returned/cases_coded.json", encoding="utf-8"))
total = ok = 0
fails = []


def walk(o, path, case):
    global total, ok
    if isinstance(o, dict):
        if "file" in o and "text" in o:
            total += 1
            key = resolve(o["file"])
            q = norm(o["text"])
            if key and q and q in texts[key]:
                ok += 1
            else:
                fails.append((case, path, o.get("file"), o.get("locator"), o["text"][:140], key))
            return
        for k, v in o.items():
            walk(v, f"{path}.{k}", case)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            walk(v, f"{path}[{i}]", case)


for c in cases:
    walk(c, c["case_id"], c["case_id"])
print(f"quotations: {total}; found verbatim: {ok}; not found: {len(fails)}")
for f in fails:
    print("NOT FOUND", f)
