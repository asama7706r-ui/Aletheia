"""Extract a model's answers from the raw replies pasted into runs/<model>/<batch>.txt.

Pre-registered rules (protocol_llm1.md, section 5):
 R1 Use the LAST fenced block marked json; else the last fenced block of any kind; else the last
    substring starting with '[' that parses as a JSON list. Nothing found -> the batch is MISSING.
 R2 The only repair allowed: delete trailing commas before ']' or '}'.
 R3 A dict holding one list is unwrapped; a single answer dict is wrapped in a list.
 R4 Only ids of that batch count. If an id repeats, the LAST occurrence counts.
 R5 Labels: upper-cased, spaces and hyphens -> underscores. Levels: case-insensitive, plus the
    words "commutative" and "associative". Branches may be strings or {"level": ...}.
 R6 "decisive" given as a flat list of strings for a fork with exactly one non-last branch is
    wrapped into one list. "values" is ignored (not scored).
 R7 Part B: "bound" and "interval" must be exact rationals (fractions, integers or finite
    decimals written as text or numbers). Anything else, or a malformed interval -> label INVALID.
 Worlds of the batch with no parsable answer -> label MISSING. MISSING and INVALID count as wrong.
Usage:  python tools/parse_answers.py <model_dir>      (writes <model_dir>/parsed.json)
"""
import json
import os
import re
import sys
from fractions import Fraction

LEVELS = {"subsumed": "SUBSUMED", "comm": "comm", "commutative": "comm", "graded": "graded",
          "assoc": "assoc", "associative": "assoc"}
FENCE = re.compile(r"```([^\n`]*)\n(.*?)```", re.S)


def _loads(s):
    s = re.sub(r",\s*([\]}])", r"\1", s.strip())
    return json.loads(s)


def extract(text):
    blocks = FENCE.findall(text)
    tagged = [b for tag, b in blocks if tag.strip().lower() == "json"]
    for cand in ([tagged[-1]] if tagged else []) + ([blocks[-1][1]] if blocks else []):
        try:
            return _norm_container(_loads(cand))
        except (ValueError, TypeError):
            pass
    for m in reversed([m.start() for m in re.finditer(r"\[", text)]):
        depth = 0
        for j in range(m, len(text)):
            depth += text[j] == "["
            depth -= text[j] == "]"
            if depth == 0:
                try:
                    got = _norm_container(_loads(text[m:j + 1]))
                    if got and all(isinstance(x, dict) and "id" in x for x in got):
                        return got
                except (ValueError, TypeError):
                    pass
                break
    return None


def _norm_container(obj):
    if isinstance(obj, dict):
        lists = [v for v in obj.values() if isinstance(v, list)]
        if "id" in obj:
            return [obj]
        if len(lists) == 1:
            return lists[0]
        raise TypeError("no answer list")
    if isinstance(obj, list):
        return obj
    raise TypeError("not a list")


def _level(x):
    if isinstance(x, dict):
        x = x.get("level")
    return LEVELS.get(str(x).strip().lower(), str(x).strip())


def _rat(x):
    if isinstance(x, bool) or x is None:
        raise ValueError
    s = str(x).strip()
    if not re.fullmatch(r"[+-]?(\d+(\.\d+)?|\.\d+)(/\d+)?", s):
        raise ValueError(s)
    f = Fraction(s)
    return str(f.numerator) if f.denominator == 1 else "%d/%d" % (f.numerator, f.denominator)


def normalize(a, part):
    out = {"label": re.sub(r"[\s\-]+", "_", str(a.get("label", "")).strip()).upper()}
    if part == "A":
        if "level" in a and a["level"] is not None:
            out["level"] = _level(a["level"])
        if isinstance(a.get("branches"), list):
            out["branches"] = [{"level": _level(b)} for b in a["branches"]]
        dec = a.get("decisive")
        if isinstance(dec, list):
            if dec and all(isinstance(q, str) for q in dec) and len(out.get("branches", [])) == 2:
                dec = [dec]
            out["decisive"] = [[str(q) for q in Q] if isinstance(Q, list) else [str(Q)] for Q in dec]
        return out
    try:
        if out["label"] == "BOUNDED":
            out["bound"] = _rat(a.get("bound"))
        if out["label"] == "ACTIVE" and a.get("interval") is not None:
            iv = a["interval"]
            if not (isinstance(iv, list) and len(iv) == 2):
                raise ValueError
            out["interval"] = [_rat(v) for v in iv]
    except (ValueError, ZeroDivisionError):
        return {"label": "INVALID"}
    return out


def parse_model(model_dir, plan):
    parsed, log = {}, {}
    for batch, ids in plan.items():
        path = os.path.join(model_dir, batch + ".txt")
        if not os.path.exists(path):
            log[batch] = "no file"
            got = None
        else:
            got = extract(open(path, encoding="utf-8").read())
            log[batch] = "parsed %d entries" % len(got) if got is not None else "no parsable list"
        answers = {}
        for a in got or []:
            if isinstance(a, dict) and str(a.get("id", "")).strip() in ids:
                answers[str(a["id"]).strip()] = a
        for wid in ids:
            parsed[wid] = normalize(answers[wid], wid[0]) if wid in answers else {"label": "MISSING"}
    return parsed, log


def main(model_dir):
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    plan = json.load(open(os.path.join(here, "prompts", "batch_plan.json"), encoding="utf-8"))
    parsed, log = parse_model(model_dir, plan)
    with open(os.path.join(model_dir, "parsed.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"answers": parsed, "log": log}, fh, ensure_ascii=False, indent=1)
    print(json.dumps(log, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
