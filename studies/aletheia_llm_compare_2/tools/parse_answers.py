"""Extract a model's answers from the raw replies pasted into runs/<model>/<batch>.txt.

Pre-registered rules (protocol_llm2.md, section 5):
 R1 Use the LAST fenced block marked json; else the last fenced block of any kind; else the last
    substring starting with '[' that parses as a JSON list of objects with ids. Nothing found ->
    every world of the batch is MISSING.
 R2 The only repair allowed: delete trailing commas before ']' or '}'.
 R3 A dict holding one list is unwrapped; a single answer dict is wrapped in a list.
 R4 Only ids of that batch count (compared after stripping spaces and upper-casing). If an id
    repeats, the LAST occurrence counts.
 R5 The verdict is read from "verdict" (or "label" if "verdict" is absent), upper-cased, with spaces
    and hyphens turned into underscores. It must be NO_DEFICIT, KNOWN, NEW or FORK; otherwise the
    answer is INVALID. Candidate ids are stripped and upper-cased.
 R6 KNOWN needs "relation": one candidate id (a list holding exactly one id is accepted).
    FORK needs "branches": a list of candidate ids (duplicates removed, then sorted). A missing or
    malformed field -> INVALID. Other fields are ignored, except R7.
 R7 Condition M only, exploratory: "excluded" maps candidate ids to lists of reason names
    (upper-cased); names other than TYPE, SYMMETRY, SCOPE, SHAPE, BOUND are dropped and counted.
 Worlds of the batch with no answer -> MISSING. MISSING and INVALID count as wrong.
Usage:  python tools/parse_answers.py <model_dir>      (writes <model_dir>/parsed.json)
"""
import json
import os
import re
import sys

FENCE = re.compile(r"```([^\n`]*)\n(.*?)```", re.S)
VERDICTS = {"NO_DEFICIT", "KNOWN", "NEW", "FORK"}
REASONS = {"TYPE", "SYMMETRY", "SCOPE", "SHAPE", "BOUND"}
CAND = re.compile(r"R\d+")


def _loads(s):
    s = re.sub(r",\s*([\]}])", r"\1", s.strip())
    return json.loads(s)


def _norm_container(obj):
    if isinstance(obj, dict):
        if "id" in obj:
            return [obj]
        lists = [v for v in obj.values() if isinstance(v, list)]
        if len(lists) == 1:
            return lists[0]
        raise TypeError("no answer list")
    if isinstance(obj, list):
        return obj
    raise TypeError("not a list")


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


def _cand(x):
    if isinstance(x, list) and len(x) == 1:
        x = x[0]
    if not isinstance(x, str):
        raise ValueError(x)
    s = x.strip().upper()
    if not CAND.fullmatch(s):
        raise ValueError(x)
    return s


def normalize(a, cond):
    raw = a.get("verdict", a.get("label", ""))
    verdict = re.sub(r"[\s\-]+", "_", str(raw).strip()).upper()
    if verdict not in VERDICTS:
        return {"verdict": "INVALID"}
    out = {"verdict": verdict}
    try:
        if verdict == "KNOWN":
            out["relation"] = _cand(a.get("relation"))
        if verdict == "FORK":
            br = a.get("branches")
            if not isinstance(br, list):
                raise ValueError(br)
            out["branches"] = sorted(set(_cand(b) for b in br))
    except ValueError:
        return {"verdict": "INVALID"}
    if cond == "M" and isinstance(a.get("excluded"), dict):
        exc, dropped = {}, 0
        for rid, reasons in a["excluded"].items():
            try:
                rid = _cand(rid)
            except ValueError:
                dropped += 1
                continue
            names = [str(r).strip().upper() for r in (reasons if isinstance(reasons, list) else [reasons])]
            dropped += sum(n not in REASONS for n in names)
            exc[rid] = sorted(set(n for n in names if n in REASONS))
        out["excluded"] = exc
        if dropped:
            out["dropped_reason_entries"] = dropped
    return out


def parse_model(model_dir, plan):
    parsed, log = {"N": {}, "M": {}}, {}
    for batch, ids in plan.items():
        cond = batch[0]
        path = os.path.join(model_dir, batch + ".txt")
        if not os.path.exists(path):
            log[batch] = "no file"
            got = None
        else:
            got = extract(open(path, encoding="utf-8").read())
            log[batch] = "parsed %d entries" % len(got) if got is not None else "no parsable list"
        answers = {}
        for a in got or []:
            if isinstance(a, dict):
                wid = str(a.get("id", "")).strip().upper()
                if wid in ids:
                    answers[wid] = a
        for wid in ids:
            parsed[cond][wid] = normalize(answers[wid], cond) if wid in answers else {"verdict": "MISSING"}
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
