"""Build the paste-ready prompt files: one per batch, each = task sheet + the batch's worlds.

Two conditions on the same worlds: N (sheet_N, the question only) and M (sheet_M, the question
plus the method). Batches follow the world ids in order: N1/M1 = W-01..W-07, N2/M2 = W-08..W-14,
N3/M3 = W-15..W-21, N4/M4 = W-22..W-27.
A world is rendered with its protocol fields only, in a fixed order. "possible_observations" is
dropped: the verdict does not use it. "experiment" is dropped: it is always "A".
Usage:  python tools/make_prompts.py
"""
import json
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORLDS = os.path.join(os.path.dirname(HERE), "aletheia_blind_test_3", "worlds")
SIZE = 7
FIELDS = ("id", "observable", "quantities", "constants", "observers", "base_law", "visible",
          "ledger", "symmetries", "old_observations", "new_observations")


def batches():
    ids = sorted(fn[:-5] for fn in os.listdir(WORLDS) if fn.startswith("W-") and fn.endswith(".json"))
    plan = {}
    for cond in ("N", "M"):
        for n in range(0, len(ids), SIZE):
            plan["%s%d" % (cond, n // SIZE + 1)] = ids[n:n + SIZE]
    return plan


def render(world):
    missing = [f for f in FIELDS if f not in world]
    if missing:
        raise SystemExit("world %s lacks %s" % (world.get("id"), missing))
    return json.dumps({f: world[f] for f in FIELDS}, ensure_ascii=False)


def main():
    os.makedirs(os.path.join(HERE, "prompts"), exist_ok=True)
    plan = batches()
    for name, ids in plan.items():
        sheet = open(os.path.join(HERE, "instructions", "sheet_%s.md" % name[0]), encoding="utf-8").read()
        worlds = [json.load(open(os.path.join(WORLDS, i + ".json"), encoding="utf-8")) for i in ids]
        body = "\n".join(render(w) for w in worlds)
        text = "%s\n\nWORLDS (%d, one JSON object per line):\n%s\n" % (sheet.rstrip(), len(worlds), body)
        with open(os.path.join(HERE, "prompts", name + ".txt"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    with open(os.path.join(HERE, "prompts", "batch_plan.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(plan, fh, indent=1)
    print(json.dumps({k: len(v) for k, v in plan.items()}))


if __name__ == "__main__":
    main()
