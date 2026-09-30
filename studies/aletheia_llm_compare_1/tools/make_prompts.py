"""Build the paste-ready prompt files: one per batch, each = task sheet + the batch's worlds.

Batches follow the world ids in order (the ids are already mixed across answer classes):
A1 = A-01..A-06, A2 = A-07..A-12, ..., A5 = A-25..A-30; B1 = B-01..B-06, B2, B3.
Usage:  python tools/make_prompts.py
"""
import json
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORLDS = os.path.join(os.path.dirname(HERE), "aletheia_blind_test_2", "worlds")
SIZE = 6


def batches():
    ids = sorted(fn[:-5] for fn in os.listdir(WORLDS) if fn.endswith(".json"))
    out = {}
    for part in ("A", "B"):
        pid = [i for i in ids if i.startswith(part + "-")]
        for n in range(0, len(pid), SIZE):
            out["%s%d" % (part, n // SIZE + 1)] = pid[n:n + SIZE]
    return out


def main():
    os.makedirs(os.path.join(HERE, "prompts"), exist_ok=True)
    plan = batches()
    for name, ids in plan.items():
        sheet = open(os.path.join(HERE, "instructions", "sheet_%s.md" % name[0]), encoding="utf-8").read()
        worlds = [json.load(open(os.path.join(WORLDS, i + ".json"), encoding="utf-8")) for i in ids]
        body = "\n".join(json.dumps(w, ensure_ascii=False) for w in worlds)
        text = "%s\n\nWORLDS (%d, one JSON object per line):\n%s\n" % (sheet.rstrip(), len(worlds), body)
        with open(os.path.join(HERE, "prompts", name + ".txt"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    with open(os.path.join(HERE, "prompts", "batch_plan.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(plan, fh, indent=1)
    print(json.dumps({k: len(v) for k, v in plan.items()}))


if __name__ == "__main__":
    main()
