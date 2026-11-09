#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Builds seed_registry.json, the tower of test 5, in description language v0.5.

The tower holds the old kinds that the ladder starts from (test-5 draft, decision 8):
  f01 / k01  the real numbers, with list v1 (Q10 page, 11.8; q1-q14);
  f02 / k02  the complex numbers, with their own list (list v1 without the order
             bundle q14), and the generator e1 with e1*e1 = -1;
  f03        a frame floor: "the elements act on a state"; one theorem, t1,
             composition is associative (Q10 7.3 and 7.5; v0.5 page 15.6).
Ids are neutral (test-4 decision R3): names carry no meaning, and seed_notes.md
says what each id is. The kernel's procedure never reads the notes.

Decisions applied (all by the project owner, 2026-10-21, v0.5 page section 15.8):
  * q2 keeps 0 1 + - * ^-1 (and > on f01): the negative was added to the list;
  * q14's third part is written "a > 0 & b > 0 -> a*b > 0" (it has no side);
  * on f02, e1*e1 = -1 is the kind's relation, not a rule (q2 protects it);
  * t1 is declared by the human seed: v0.5 cannot write its proof (a declared gap).
Usage: python make_seed.py   (writes seed_registry.json next to this file)
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "lang"))
import reader_v0 as R  # noqa: E402

# list v1 without q2 (q2 is written by keeps, and differs between the two floors)
LIST_V1 = [
    ("q1", True, ["1 != 0"]),
    ("q3", False, ["(a + b) + c = a + (b + c)"]),
    ("q4", False, ["a + b = b + a"]),
    ("q5", False, ["(a*b)*c = a*(b*c)"]),
    ("q6", False, ["a*b = b*a"]),
    ("q7", False, ["a*(b + c) = a*b + a*c"]),
    ("q8", False, ["(a + b)*c = a*c + b*c"]),
    ("q9", False, ["a + 0 = a"]),
    ("q10", False, ["1*a = a", "a*1 = a"]),
    ("q11", False, ["a + (-a) = 0"]),
    ("q12", False, ["a*b = 0 -> a = 0 | b = 0"]),
    ("q13", False, ["a != 0 -> a*a^-1 = 1", "a != 0 -> a^-1*a = 1"]),
]
Q14 = ("q14", False, [
    "a > b -> a != b",              # strict total order: irreflexive,
    "a > b & b > c -> a > c",       # transitive,
    "a > b | a = b | b > a",        # and total
    "a > b -> a + c > b + c",       # sums keep the order
    "a > 0 & b > 0 -> a*b > 0",     # a positive times a positive is positive
])
def rule(rid, protected, sentences):
    # every name in a floor rule is a free variable; in list v1 each ranges over the whole candidate
    used = sorted(set().union(*(R.parse_sentence(s)[1] for s in sentences)))
    return {"id": rid, "protected": protected, "vars": {v: "new" for v in used},
            "sentences": sentences, "keeps": [], "src": "seed"}


def keeps_rule(letters):
    return {"id": "q2", "protected": True, "vars": {}, "sentences": [], "keeps": letters, "src": "seed"}


def floor_rules(with_order):
    rules = [rule(*LIST_V1[0])]
    rules.append(keeps_rule(["0", "1", "+", "-", "*", "^-1"] + ([">"] if with_order else [])))
    rules += [rule(*r) for r in LIST_V1[1:]]
    if with_order:
        rules.append(rule(*Q14))
    return rules


SEED = {
    "v0": "0.5", "file": "registry", "id": "t5_tower", "catalog": "1",
    "dimensions": [],
    "floors": [
        {"id": "f01", "depends_on": [], "rules_version": "1", "rules": floor_rules(True), "src": "seed"},
        {"id": "f02", "depends_on": ["f01"], "rules_version": "1", "rules": floor_rules(False), "src": "seed"},
        {"id": "f03", "depends_on": [], "rules_version": "1",
         "rules": [dict(rule("t1", True, ["(a*b)*c = a*(b*c)"]))], "src": "seed"},
    ],
    "kinds": [
        {"id": "k01", "floor": "f01", "over": "reals", "shape": [], "generators": [], "relations": [],
         "under": {}, "src": "seed"},
        {"id": "k02", "floor": "f02", "over": "reals", "shape": [2], "generators": ["e1"],
         "relations": ["e1*e1 = -1"], "under": {}, "src": "seed"},
    ],
    "transformations": [], "instruments": [], "meanings": [], "definitions": [], "body_types": [],
}


def write(path):
    lines = ["{"]
    for key in ("v0", "file", "id", "catalog"):
        lines.append(f'  "{key}": {json.dumps(SEED[key])},')
    lines.append('  "dimensions": [],')
    lines.append('  "floors": [')
    for fi, f in enumerate(SEED["floors"]):
        lines.append(f'    {{"id": "{f["id"]}", "depends_on": {json.dumps(f["depends_on"])}, '
                     f'"rules_version": "{f["rules_version"]}", "rules": [')
        lines.append(",\n".join("      " + json.dumps(r, ensure_ascii=False) for r in f["rules"]))
        lines.append('    ], "src": "seed"}' + ("," if fi < len(SEED["floors"]) - 1 else ""))
    lines.append("  ],")
    lines.append('  "kinds": [')
    lines.append(",\n".join("    " + json.dumps(k, ensure_ascii=False) for k in SEED["kinds"]))
    lines.append("  ],")
    for key in ("transformations", "instruments", "meanings", "definitions"):
        lines.append(f'  "{key}": [],')
    lines.append('  "body_types": []')
    lines.append("}")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    out = os.path.join(HERE, "seed_registry.json")
    write(out)
    print("wrote", out)
