#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Blind test 4: the world generator's builder (separate Claude session, 2026-10-07).

    python key/make_worlds.py          writes worlds/W-01.json ... W-30.json and key/key.json

Every world is first written with readable labels (in this file only), then every id is renamed to a
neutral random name. Observation values are computed exactly: old observations from the law (or from the
described filler where its new thing was present all along), placed close to the edge of the observer's
precision; new observations from the intended explanation. The verdicts in the key are the design intent;
key/verify_key.py recomputes them from the protocol, and the sealed validator checks them again.
"""
import json
import os
import random
import sys
from fractions import Fraction as Fr

import sympy as sp

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import verify_key as V  # noqa: E402

REG = V.Registry()
SAME, ANOTHER, INVALID, COND = V.SAME, V.ANOTHER, V.INVALID, V.COND

E = {"M": 1, "L": 2, "T": -2}
FD = {"M": 1, "L": 1, "T": -2}
LD = {"L": 1}
MD = {"M": 1}
QD = {"Q": 1}
TD = {"T": 1}
EF = {"M": 1, "L": 1, "T": -2, "Q": -1}
BF = {"M": 1, "T": -1, "Q": -1}
VEL = {"L": 1, "T": -1}
ACC = {"L": 1, "T": -2}


def NQ(id, kind, meaning, owner, dims, value, old, route, under=None, comps=None):
    if under is None:
        under = json.loads(json.dumps(REG.meanings[meaning]["under"]))
    if comps is None:
        comps = "?" if kind == "?" else ([] if kind == "scalar" else None)
    return {"id": id, "kind": kind, "meaning": meaning, "owner": owner, "dims": dims, "components": comps,
            "under": under, "value": value, "old_value": old, "route": route}


def vec(p):
    return [p + "x", p + "y", p + "z"]


# =====================================================================================================
# world specifications (readable labels; renamed before writing)
# quantities: (id, meaning, owner, dims, value, components or None)
# obs: (observer, state, epoch, truth, offset as a fraction of the precision)
#      truth None = the law; ("fid", {new name: value}) = that filler with these values of its new quantities
# =====================================================================================================

SPECS = []


def spec(f):
    SPECS.append(f())
    return f


@spec
def S1():
    return dict(
        label="S1", note="T1: a second charge sharing the probe's place; conj_c needs it to flip with the charge.",
        bodies=[("pb", "ty03")],
        quantities=[("en", "m03", "world", E, "var", None), ("w0", "m03", "world", E, "-41/8", None),
                    ("kd", "m07", "world", {"L": 2, "Q": -2}, "5/7", None), ("qa", "m04", "pb", QD, "-9/4", None),
                    ("e", "m17", "world", EF, "var", vec("e")), ("h", "m12", "pb", LD, "var", vec("h")),
                    ("dd", "m11", "world", LD, "var", None)],
        law=("lw", "en = w0 + kd*qa^3*ez*hz/dd^2", 2),
        observers=[("o1", "i04", "1/40", []), ("o2", "i04", "3/200", ["o1"])],
        fillers=[("f1", "en = w0 + kd*(qa + qn)*qa^2*ez*hz/dd^2", [("nb", "ty06")],
                  [NQ("qn", "scalar", "m04", "nb", "?", "?", "0", "i05")])],
        obs=[("o1", {"ez": "3/2", "hz": "1/3", "dd": "2"}, 0, None, "9/10"),
             ("o2", {"ez": "5/2", "hz": "-1/2", "dd": "7/4"}, 3, ("f1", {"qn": "7/5"}), "1/4"),
             ("o1", {"ez": "-2", "hz": "2/5", "dd": "3/2"}, 1, None, "-23/25"),
             ("o2", {"ez": "5/4", "hz": "-3/4", "dd": "5/2"}, 1, None, "87/100"),
             ("o1", {"ez": "2", "hz": "1/2", "dd": "3/2"}, 3, ("f1", {"qn": "7/5"}), "-3/10"),
             ("o2", {"ez": "7/3", "hz": "1", "dd": "9/4"}, 2, None, "-4/5"),
             ("o2", {"ez": "-3/2", "hz": "2/3", "dd": "2"}, 4, ("f1", {"qn": "7/5"}), "0")],
        intent={"f1": SAME})


@spec
def S2():
    return dict(
        label="S2", note="T1: a charge present all along in the surroundings (old_value same), seen only when the probe charge is large.",
        bodies=[("pb", "ty01"), ("sb", "ty05")],
        quantities=[("p", "m12", "pb", LD, "var", vec("p")), ("qa", "m04", "pb", QD, "var", None),
                    ("qb", "m04", "sb", QD, "5/3", None), ("mb", "m02", "pb", MD, "3/7", None),
                    ("g", "m21", "world", ACC, "var", vec("g")),
                    ("kc", "m07", "world", {"M": 1, "L": 2, "T": -2, "Q": -2}, "2/9", None),
                    ("p0", "m11", "world", LD, "13/4", None)],
        law=("lw", "pz = p0 + kc*qa*qb/(mb*gz)", 3),
        observers=[("o1", "i02", "1/1000", []), ("o2", "i02", "1/800", [])],
        fillers=[("f1", "pz = p0 + kc*qa*(qb + qn)/(mb*gz)", [],
                  [NQ("qn", "scalar", "m04", "world", QD, "?", "same", "i05")])],
        obs=[("o1", {"qa": "1/50", "gz": "-49/5"}, 0, None, "9/10"),
             ("o1", {"qa": "-3/100", "gz": "-49/5"}, 1, None, "-93/100"),
             ("o2", {"qa": "1/40", "gz": "-10"}, 2, None, "4/5"),
             ("o2", {"qa": "-1/25", "gz": "-19/2"}, 3, None, "-9/10"),
             ("o1", {"qa": "3/2", "gz": "-49/5"}, 4, ("f1", {"qn": "-2/5"}), "1/5"),
             ("o2", {"qa": "-2", "gz": "-10"}, 4, ("f1", {"qn": "-2/5"}), "-1/4"),
             ("o1", {"qa": "5/2", "gz": "-39/4"}, 5, ("f1", {"qn": "-2/5"}), "0")],
        intent={"f1": SAME})


@spec
def S3():
    return dict(
        label="S3", note="T3: a uniform field switched on after acceptance, coupled to the angular momentum through the charge.",
        bodies=[("rb", "ty02")],
        quantities=[("en", "m03", "world", E, "var", None),
                    ("l", "m19", "rb", {"M": 1, "L": 2, "T": -1}, "var", vec("l")),
                    ("qa", "m04", "rb", QD, "4/3", None), ("ma", "m02", "rb", MD, "5/2", None),
                    ("kr", "m07", "world", {"M": 2}, "3/8", None), ("dd", "m11", "world", LD, "var", None)],
        law=("lw", "en = kr*lz^2/(ma^3*dd^2)", 1),
        observers=[("o1", "i04", "1/50", [])],
        fillers=[("f1", "en = kr*lz^2/(ma^3*dd^2) + qa*(lx*bx + ly*by + lz*bz)/ma", [],
                  [NQ("b", "vec3", "m18", "world", "?", "?", ["0", "0", "0"], "i08", comps=vec("b"))])],
        obs=[("o1", {"lx": "1/2", "ly": "-1", "lz": "2", "dd": "3/2"}, 0, None, "-9/10"),
             ("o1", {"lx": "0", "ly": "2", "lz": "-3", "dd": "2"}, 0, None, "91/100"),
             ("o1", {"lx": "-1", "ly": "1/2", "lz": "5/2", "dd": "5/4"}, 1, None, "-17/20"),
             ("o1", {"lx": "1", "ly": "-1", "lz": "2", "dd": "3/2"}, 2, ("f1", {"bx": "1/3", "by": "-1/2", "bz": "3/4"}), "1/5"),
             ("o1", {"lx": "2", "ly": "1/2", "lz": "-1", "dd": "2"}, 2, ("f1", {"bx": "1/3", "by": "-1/2", "bz": "3/4"}), "-1/3"),
             ("o1", {"lx": "-1/2", "ly": "3", "lz": "3/2", "dd": "5/4"}, 3, ("f1", {"bx": "1/3", "by": "-1/2", "bz": "3/4"}), "1/10"),
             ("o1", {"lx": "1", "ly": "1", "lz": "1", "dd": "1"}, 3, ("f1", {"bx": "1/3", "by": "-1/2", "bz": "3/4"}), "0")],
        intent={"f1": SAME})


@spec
def S4():
    return dict(
        label="S4", note="T4: the observer moves (w, at rest before); the force gains a term (v.w) hz, mirror-even only if w is a polar vector.",
        bodies=[("kb", "ty05")],
        quantities=[("f", "m16", "kb", FD, "var", vec("f")),
                    ("kp", "m05", "world", {"M": 1, "L": -2, "T": -2}, "7/4", None),
                    ("h", "m12", "kb", LD, "var", vec("h")), ("ma", "m02", "kb", MD, "6/5", None),
                    ("g", "m21", "world", ACC, ["0", "0", "-49/5"], vec("g")),
                    ("v", "m13", "kb", VEL, "var", vec("v")),
                    ("kq", "m07", "world", {"M": 1, "L": -2}, "2/3", None)],
        law=("lw", "fz = ma*gz - kp*hz^3", 4),
        observers=[("o1", "i06", "1/100", []), ("o2", "i06", "1/250", ["o1"])],
        fillers=[("f1", "fz = ma*gz - kp*hz^3 + kq*(vx*wx + vy*wy + vz*wz)*hz", [],
                  [NQ("w", "vec3", "m22", "world", "?", "?", ["0", "0", "0"], "?", comps=vec("w"))])],
        obs=[("o1", {"hz": "1/2", "vx": "1", "vy": "0", "vz": "-1"}, 0, None, "93/100"),
             ("o1", {"hz": "-1", "vx": "2", "vy": "1", "vz": "1/2"}, 1, None, "-21/25"),
             ("o2", {"hz": "3/4", "vx": "-1", "vy": "2", "vz": "0"}, 2, None, "-9/10"),
             ("o2", {"hz": "1", "vx": "0", "vy": "-1", "vz": "2"}, 4, None, "4/5"),
             ("o1", {"hz": "-1/2", "vx": "1/2", "vy": "1/2", "vz": "1/2"}, 4, None, "-24/25"),
             ("o2", {"hz": "1", "vx": "2", "vy": "1", "vz": "-1"}, 5, ("f1", {"wx": "3/10", "wy": "-1/5", "wz": "1/2"}), "1/5"),
             ("o1", {"hz": "-3/2", "vx": "1", "vy": "-2", "vz": "1"}, 6, ("f1", {"wx": "3/10", "wy": "-1/5", "wz": "1/2"}), "-1/2"),
             ("o2", {"hz": "2", "vx": "-1", "vy": "1", "vz": "3"}, 6, ("f1", {"wx": "3/10", "wy": "-1/5", "wz": "1/2"}), "0")],
        intent={"f1": SAME})


@spec
def S5():
    return dict(
        label="S5", note="T3: a magnetic field present all along (old_value same) seen by an observer that was at rest at the old observations; motional field (w x b)_z.",
        bodies=[("cb", "ty04")],
        quantities=[("u", "m17", "cb", EF, "var", vec("u")), ("e", "m17", "world", EF, "var", vec("e")),
                    ("w", "m22", "world", VEL, "var", vec("w")), ("h", "m12", "cb", LD, "var", vec("h")),
                    ("ka", "m07", "world", {"L": -2}, "-3/16", None)],
        law=("lw", "uz = ez*(1 + ka*hz^2)", 2),
        observers=[("o1", "i07", "1/200", [])],
        fillers=[("f1", "uz = ez*(1 + ka*hz^2) + wx*by - wy*bx", [],
                  [NQ("b", "vec3", "m18", "world", "?", "?", "same", "i08", comps=vec("b"))])],
        obs=[("o1", {"ez": "2", "hz": "1", "wx": "0", "wy": "0"}, 0, None, "-9/10"),
             ("o1", {"ez": "-3/2", "hz": "2", "wx": "0", "wy": "0"}, 1, None, "22/25"),
             ("o1", {"ez": "1", "hz": "-3", "wx": "0", "wy": "0"}, 2, None, "-19/20"),
             ("o1", {"ez": "2", "hz": "1", "wx": "3/2", "wy": "-1"}, 3, ("f1", {"bx": "2/5", "by": "-7/10", "bz": "1"}), "1/4"),
             ("o1", {"ez": "1", "hz": "2", "wx": "-2", "wy": "1/2"}, 3, ("f1", {"bx": "2/5", "by": "-7/10", "bz": "1"}), "-1/5"),
             ("o1", {"ez": "-1", "hz": "1/2", "wx": "1", "wy": "1"}, 4, ("f1", {"bx": "2/5", "by": "-7/10", "bz": "1"}), "0")],
        intent={"f1": SAME})


@spec
def S6():
    return dict(
        label="S6", note="T4: an observer velocity w (new) in a known field b; energy term qa (w x b).h, mirror-even only with w polar.",
        bodies=[("cb", "ty07")],
        quantities=[("en", "m03", "world", E, "var", None), ("w0", "m03", "world", E, "17/6", None),
                    ("ks", "m07", "world", {"M": -1, "L": 2, "Q": 2}, "1/5", None),
                    ("b", "m18", "world", BF, "var", vec("b")), ("qa", "m04", "cb", QD, "-5/4", None),
                    ("h", "m12", "cb", LD, "var", vec("h"))],
        law=("lw", "en = w0 + ks*(bx^2 + by^2 + bz^2)", 2),
        observers=[("o1", "i04", "1/80", [])],
        fillers=[("f1", "en = w0 + ks*(bx^2 + by^2 + bz^2) + qa*((wy*bz - wz*by)*hx + (wz*bx - wx*bz)*hy + (wx*by - wy*bx)*hz)", [],
                  [NQ("w", "vec3", "m22", "world", "?", "?", ["0", "0", "0"], "?", comps=vec("w"))])],
        obs=[("o1", {"bx": "1", "by": "-1/2", "bz": "2", "hx": "1", "hy": "0", "hz": "-1"}, 0, None, "47/50"),
             ("o1", {"bx": "-2", "by": "1", "bz": "0", "hx": "1/2", "hy": "2", "hz": "1"}, 1, None, "-22/25"),
             ("o1", {"bx": "1/2", "by": "3/2", "bz": "-1", "hx": "-1", "hy": "1", "hz": "1/2"}, 2, None, "9/10"),
             ("o1", {"bx": "1", "by": "2", "bz": "-1", "hx": "2", "hy": "-1", "hz": "1"}, 3, ("f1", {"wx": "1/4", "wy": "1/2", "wz": "-3/4"}), "-1/5"),
             ("o1", {"bx": "-1", "by": "1", "bz": "3", "hx": "1", "hy": "1", "hz": "-2"}, 3, ("f1", {"wx": "1/4", "wy": "1/2", "wz": "-3/4"}), "3/10"),
             ("o1", {"bx": "2", "by": "0", "bz": "1", "hx": "0", "hy": "3", "hz": "1"}, 4, ("f1", {"wx": "1/4", "wy": "1/2", "wz": "-3/4"}), "0")],
        intent={"f1": SAME})


@spec
def S7():
    return dict(
        label="S7", note="Unknown action that does not matter: the law is already changed by rev_t (its vz*hz term), so the new quantity's unknown rev_t sign cannot change the card.",
        bodies=[("tb", "ty08")],
        quantities=[("en", "m03", "world", E, "var", None), ("ka", "m05", "world", {"M": 1, "T": -2}, "5/2", None),
                    ("kb", "m07", "world", {"M": 1, "T": -1}, "-1/3", None),
                    ("h", "m12", "tb", LD, "var", vec("h")), ("v", "m13", "tb", VEL, "var", vec("v"))],
        law=("lw", "en = ka*hz^2 + kb*vz*hz", 1),
        observers=[("o1", "i04", "1/25", [])],
        fillers=[("f1", "en = ka*hz^2 + kb*vz*hz + un*hz^3", [],
                  [NQ("un", "scalar", "?", "world", "?", "?", "0", "?",
                      under={"rev_t": "?", "refl_x": "1", "conj_c": "1"})])],
        obs=[("o1", {"hz": "1", "vz": "2"}, 0, None, "-9/10"),
             ("o1", {"hz": "-1/2", "vz": "3"}, 0, None, "87/100"),
             ("o1", {"hz": "3/2", "vz": "-1"}, 1, None, "-93/100"),
             ("o1", {"hz": "2", "vz": "1"}, 2, ("f1", {"un": "3/7"}), "1/3"),
             ("o1", {"hz": "-2", "vz": "1/2"}, 3, ("f1", {"un": "3/7"}), "-1/4")],
        intent={"f1": SAME})


@spec
def A1():
    return dict(
        label="A1", note="F3 alone: a quadratic stiffness present all along (old_value same); the value the deficit needs breaks the old observations at small hz.",
        bodies=[("sb", "ty03")],
        quantities=[("f", "m16", "sb", FD, "var", vec("f")), ("kk", "m05", "world", {"M": 1, "T": -2}, "9/2", None),
                    ("kb", "m07", "world", {"L": -2}, "2/5", None), ("h", "m12", "sb", LD, "var", vec("h"))],
        law=("lw", "fz = -kk*hz/(1 + kb*hz^2)", 3),
        observers=[("o1", "i06", "1/50", []), ("o2", "i06", "1/100", ["o1"])],
        fillers=[("f1", "fz = -kk*hz/(1 + kb*hz^2) + cs*hz^2", [],
                  [NQ("cs", "scalar", "m05", "world", "?", "?", "same", "?")])],
        obs=[("o1", {"hz": "1/5"}, 0, None, "-9/10"),
             ("o1", {"hz": "-1/4"}, 1, None, "-17/20"),
             ("o2", {"hz": "3/10"}, 2, None, "-4/5"),
             ("o1", {"hz": "-1/6"}, 3, None, "-19/20"),
             ("o2", {"hz": "2"}, 4, ("f1", {"cs": "3/4"}), "1/5"),
             ("o2", {"hz": "5/2"}, 4, ("f1", {"cs": "3/4"}), "-1/4"),
             ("o2", {"hz": "-3/2"}, 5, ("f1", {"cs": "3/4"}), "0")],
        intent={"f1": ANOTHER})


@spec
def A2():
    return dict(
        label="A2", note="F3 alone: a delay that the filler says was already 1/40 at the old observations (a variable with a known old value).",
        bodies=[("tb", "ty01")],
        quantities=[("tp", "m01", "world", TD, "var", None), ("ka", "m07", "world", {}, "6/5", None),
                    ("dd", "m11", "world", LD, "var", None), ("v", "m13", "tb", VEL, "var", vec("v"))],
        law=("lw", "tp = ka*dd/vz", 4),
        observers=[("o1", "i01", "1/100", [])],
        fillers=[("f1", "tp = ka*dd/vz + tn", [],
                  [NQ("tn", "scalar", "m01", "tb", "?", "var", "1/40", "i01")])],
        obs=[("o1", {"dd": "3", "vz": "2"}, 0, None, "-9/10"),
             ("o1", {"dd": "5/2", "vz": "-1"}, 1, None, "-17/20"),
             ("o1", {"dd": "4", "vz": "3/2"}, 2, None, "3/10"),
             ("o1", {"dd": "1", "vz": "1/2"}, 4, None, "-24/25"),
             ("o1", {"dd": "2", "vz": "1"}, 5, ("f1", {"tn": "3/25"}), "1/5"),
             ("o1", {"dd": "3", "vz": "-2"}, 6, ("f1", {"tn": "-1/20"}), "-1/2")],
        intent={"f1": ANOTHER})


@spec
def A3():
    return dict(
        label="A3", note="T2 with m06 under rev_t: a damping-like term gd*vz*hz; the damping card is +1 under time reversal, so the term breaks it.",
        bodies=[("db", "ty06")],
        quantities=[("en", "m03", "world", E, "var", None), ("ka", "m07", "world", {}, "3/5", None),
                    ("ma", "m02", "db", MD, "7/2", None),
                    ("kb", "m07", "world", {"M": 1, "L": -1, "T": -2}, "-2/9", None),
                    ("v", "m13", "db", VEL, "var", vec("v")), ("h", "m12", "db", LD, "var", vec("h"))],
        law=("lw", "en = ka*ma*vz^2 + kb*hz^3", 2),
        observers=[("o1", "i04", "1/60", []), ("o2", "i04", "1/90", ["o1"])],
        fillers=[("f1", "en = ka*ma*vz^2 + kb*hz^3 + gd*vz*hz", [],
                  [NQ("gd", "scalar", "m06", "db", "?", "?", "0", "?")])],
        obs=[("o1", {"vz": "1", "hz": "2"}, 0, None, "9/10"),
             ("o2", {"vz": "-1/2", "hz": "3/2"}, 1, None, "-83/100"),
             ("o1", {"vz": "2", "hz": "-1"}, 2, None, "-23/25"),
             ("o2", {"vz": "3/2", "hz": "1"}, 3, ("f1", {"gd": "4/5"}), "1/4"),
             ("o2", {"vz": "-1", "hz": "2"}, 3, ("f1", {"gd": "4/5"}), "-1/5"),
             ("o1", {"vz": "1/2", "hz": "-3"}, 4, ("f1", {"gd": "4/5"}), "0")],
        intent={"f1": ANOTHER})


@spec
def A4():
    return dict(
        label="A4", note="T2 + T8 (axial, refl_x): a torque n (axial) dotted with a position: a pseudoscalar term in an energy; l.s keeps the mirror.",
        bodies=[("ab", "ty01"), ("bb", "ty08")],
        quantities=[("en", "m03", "world", E, "var", None), ("w0", "m03", "world", E, "-7/3", None),
                    ("ks", "m07", "world", {"M": -1, "L": -2}, "1/6", None),
                    ("l", "m19", "ab", {"M": 1, "L": 2, "T": -1}, "var", vec("l")),
                    ("s", "m19", "bb", {"M": 1, "L": 2, "T": -1}, ["1/2", "-1", "3/2"], vec("s")),
                    ("h", "m12", "ab", LD, "var", vec("h"))],
        law=("lw", "en = w0 + ks*(lx*sx + ly*sy + lz*sz)", 1),
        observers=[("o1", "i04", "1/100", [])],
        fillers=[("f1", "en = w0 + ks*(lx*sx + ly*sy + lz*sz) + nx*hx + ny*hy + nz*hz", [],
                  [NQ("n", "vec3", "m20", "bb", "?", "?", ["0", "0", "0"], "?", comps=vec("n"))])],
        obs=[("o1", {"lx": "2", "ly": "1", "lz": "-1", "hx": "1", "hy": "0", "hz": "1/2"}, 0, None, "-9/10"),
             ("o1", {"lx": "-1", "ly": "3", "lz": "2", "hx": "-1", "hy": "1", "hz": "0"}, 1, None, "21/25"),
             ("o1", {"lx": "1/2", "ly": "-2", "lz": "1", "hx": "2", "hy": "1", "hz": "-1"}, 2, ("f1", {"nx": "1/2", "ny": "-1/3", "nz": "1/4"}), "1/5"),
             ("o1", {"lx": "1", "ly": "1", "lz": "1", "hx": "1", "hy": "-2", "hz": "3"}, 2, ("f1", {"nx": "1/2", "ny": "-1/3", "nz": "1/4"}), "-1/4"),
             ("o1", {"lx": "0", "ly": "-1", "lz": "2", "hx": "-3", "hy": "1", "hz": "1"}, 3, ("f1", {"nx": "1/2", "ny": "-1/3", "nz": "1/4"}), "0")],
        intent={"f1": ANOTHER})


@spec
def A5():
    return dict(
        label="A5", note="T5 (rot_z, kind-reading): the law is anisotropic (hx^2 only); the filler restores the quarter-turn symmetry; a gained symmetry is a change.",
        bodies=[("rb", "ty02")],
        quantities=[("en", "m03", "world", E, "var", None), ("kr", "m07", "world", {"T": -2}, "5/3", None),
                    ("ma", "m02", "rb", MD, "4/5", None), ("kv", "m07", "world", FD, "-3/2", None),
                    ("h", "m12", "rb", LD, "var", vec("h"))],
        law=("lw", "en = kr*hx^2*ma + kv*hz", 3),
        observers=[("o1", "i04", "1/30", [])],
        fillers=[("f1", "en = kr*(hx^2 + hy^2)*ma + kv*hz + cn*hz^2", [],
                  [NQ("cn", "scalar", "?", "world", "?", "?", "0", "?",
                      under={"rev_t": "1", "refl_x": "1", "conj_c": "1"})])],
        obs=[("o1", {"hx": "1", "hy": "0", "hz": "2"}, 0, None, "9/10"),
             ("o1", {"hx": "-1/2", "hy": "0", "hz": "1"}, 1, None, "-22/25"),
             ("o1", {"hx": "3/2", "hy": "0", "hz": "-1"}, 2, None, "19/20"),
             ("o1", {"hx": "2", "hy": "0", "hz": "1/2"}, 3, None, "-17/20"),
             ("o1", {"hx": "1", "hy": "1", "hz": "1"}, 4, ("f1", {"cn": "-1/4"}), "1/5"),
             ("o1", {"hx": "1/2", "hy": "-3/2", "hz": "2"}, 5, ("f1", {"cn": "-1/4"}), "-1/3"),
             ("o1", {"hx": "-1", "hy": "2", "hz": "-1/2"}, 5, ("f1", {"cn": "-1/4"}), "0")],
        intent={"f1": ANOTHER})


@spec
def A6():
    return dict(
        label="A6", note="T5 + T2 + T8 (m23, rev_t): the law's qa*fa*fb term breaks time reversal (not charge conjugation); the filler multiplies it by wz (rev_t odd), a gained symmetry.",
        bodies=[("fb0", "ty03")],
        quantities=[("en", "m03", "world", E, "var", None),
                    ("ka", "m07", "world", {"M": 1, "L": 2, "T": -2, "Q": -3}, "3/4", None),
                    ("qa", "m04", "fb0", QD, "-6/5", None),
                    ("ps", "m23", "world", QD, "var", ["fa", "fb"]), ("kb", "m07", "world", FD, "5/2", None),
                    ("h", "m12", "fb0", LD, "var", vec("h"))],
        law=("lw", "en = ka*qa*fa*fb + kb*hz", 2),
        observers=[("o1", "i04", "1/40", [])],
        fillers=[("f1", "en = ka*qa*fa*fb*wz + kb*hz", [],
                  [NQ("w", "vec3", "m22", "world", "?", "?", ["0", "0", "1"], "?", comps=vec("w"))])],
        obs=[("o1", {"fa": "1", "fb": "2", "hz": "1/2"}, 0, None, "-9/10"),
             ("o1", {"fa": "-3/2", "fb": "1", "hz": "1"}, 1, None, "23/25"),
             ("o1", {"fa": "2", "fb": "-1/2", "hz": "-1"}, 2, None, "-19/20"),
             ("o1", {"fa": "1", "fb": "1", "hz": "2"}, 3, ("f1", {"wx": "0", "wy": "0", "wz": "-2/3"}), "1/5"),
             ("o1", {"fa": "2", "fb": "3/2", "hz": "-1/2"}, 4, ("f1", {"wx": "0", "wy": "0", "wz": "-2/3"}), "-1/4")],
        intent={"f1": ANOTHER})


@spec
def A7():
    return dict(
        label="A7", note="T6: two identical bodies; the filler's pair (c1 on one, c2 on the other) enters asymmetrically: c1*(m1+m2) + c2*m0. FIX (never exchanged) misses it.",
        bodies=[("ba", "ty02"), ("bb", "ty02")],
        quantities=[("en", "m03", "world", E, "var", None), ("m1", "m02", "ba", MD, "var", None),
                    ("m2", "m02", "bb", MD, "var", None), ("m0", "m02", "world", MD, "5/4", None),
                    ("kg", "m07", "world", {"M": -1, "L": 3, "T": -2}, "2/7", None),
                    ("kh", "m07", "world", {"M": -1, "L": 4, "T": -2}, "-3/5", None),
                    ("dd", "m11", "world", LD, "var", None)],
        law=("lw", "en = kg*(m1^2 + m2^2)/dd + kh*m1*m2/dd^2", 2),
        observers=[("o1", "i04", "1/50", []), ("o2", "i04", "1/70", [])],
        fillers=[("f1", "en = kg*(m1^2 + m2^2)/dd + kh*m1*m2/dd^2 + c1*(m1 + m2) + c2*m0", [],
                  [NQ("c1", "scalar", "m07", "ba", "?", "?", "0", "?"),
                   NQ("c2", "scalar", "m07", "bb", "?", "?", "0", "?")])],
        obs=[("o1", {"m1": "1", "m2": "2", "dd": "3"}, 0, None, "9/10"),
             ("o2", {"m1": "3/2", "m2": "1/2", "dd": "2"}, 1, None, "-91/100"),
             ("o1", {"m1": "2", "m2": "2", "dd": "5/2"}, 2, None, "-4/5"),
             ("o2", {"m1": "1", "m2": "3", "dd": "2"}, 3, ("f1", {"c1": "1/3", "c2": "-1/2"}), "1/5"),
             ("o1", {"m1": "5/2", "m2": "1", "dd": "3/2"}, 3, ("f1", {"c1": "1/3", "c2": "-1/2"}), "-1/3"),
             ("o2", {"m1": "1/2", "m2": "1/2", "dd": "1"}, 4, ("f1", {"c1": "1/3", "c2": "-1/2"}), "0")],
        intent={"f1": ANOTHER})


@spec
def A8():
    return dict(
        label="A8", note="T6: a new charged body near one of two identical charged bodies only.",
        bodies=[("ca", "ty04"), ("cb", "ty04")],
        quantities=[("en", "m03", "world", E, "var", None), ("q1", "m04", "ca", QD, "var", None),
                    ("q2", "m04", "cb", QD, "var", None), ("d1", "m11", "ca", LD, "var", None),
                    ("d2", "m11", "cb", LD, "var", None), ("dd", "m11", "world", LD, "5/2", None),
                    ("kc", "m07", "world", {"M": 1, "L": 3, "T": -2, "Q": -2}, "1/9", None),
                    ("ke", "m07", "world", {"M": 1, "L": 3, "T": -2, "Q": -2}, "1/4", None)],
        law=("lw", "en = kc*q1*q2/dd + ke*(q1^2/d1 + q2^2/d2)", 1),
        observers=[("o1", "i04", "1/30", [])],
        fillers=[("f1", "en = kc*q1*q2/dd + ke*(q1^2/d1 + q2^2/d2) + kc*qn*q1/d1", [("nb", "ty07")],
                  [NQ("qn", "scalar", "m04", "nb", QD, "?", "0", "i05")])],
        obs=[("o1", {"q1": "1", "q2": "-1", "d1": "2", "d2": "3"}, 0, None, "-9/10"),
             ("o1", {"q1": "2", "q2": "1/2", "d1": "1", "d2": "2"}, 1, None, "17/20"),
             ("o1", {"q1": "-1", "q2": "2", "d1": "3/2", "d2": "1"}, 2, ("f1", {"qn": "3/2"}), "1/5"),
             ("o1", {"q1": "3", "q2": "1", "d1": "2", "d2": "5/2"}, 2, ("f1", {"qn": "3/2"}), "-1/4"),
             ("o1", {"q1": "2", "q2": "-2", "d1": "1/2", "d2": "1"}, 3, ("f1", {"qn": "3/2"}), "0")],
        intent={"f1": ANOTHER})


@spec
def I1():
    return dict(
        label="I1", note="INVALID: a new velocity (m13) whose written dims are those of an acceleration; the filled law is consistent with the written dims, not with the meaning.",
        bodies=[("ib", "ty05")],
        quantities=[("f", "m16", "ib", FD, "var", vec("f")), ("ma", "m02", "ib", MD, "9/5", None),
                    ("a", "m14", "ib", ACC, "var", vec("a")),
                    ("kk", "m05", "world", {"M": 1, "T": -2}, "11/4", None), ("h", "m12", "ib", LD, "var", vec("h"))],
        law=("lw", "fz = ma*az + kk*hz", 2),
        observers=[("o1", "i06", "1/20", [])],
        fillers=[("f1", "fz = ma*(az + unz) + kk*hz", [],
                  [NQ("un", "vec3", "m13", "ib", ACC, "?", ["0", "0", "0"], "?", comps=vec("un"))])],
        obs=[("o1", {"az": "1", "hz": "2"}, 0, None, "9/10"),
             ("o1", {"az": "-2", "hz": "1/2"}, 1, None, "-21/25"),
             ("o1", {"az": "3/2", "hz": "-1"}, 2, None, "-19/20"),
             ("o1", {"az": "1", "hz": "1"}, 3, ("f1", {"unx": "0", "uny": "0", "unz": "3/2"}), "1/5"),
             ("o1", {"az": "-1/2", "hz": "3"}, 4, ("f1", {"unx": "0", "uny": "0", "unz": "3/2"}), "-1/4")],
        intent={"f1": INVALID})


@spec
def I2():
    return dict(
        label="I2", note="INVALID: one new coupling multiplies a velocity term and a position term with equal world dims; no dims of xn fit both.",
        bodies=[("jb", "ty06")],
        quantities=[("en", "m03", "world", E, "var", None), ("kb", "m05", "world", {"M": 1, "T": -2}, "7/3", None),
                    ("v", "m13", "jb", VEL, "var", vec("v")), ("h", "m12", "jb", LD, "var", vec("h")),
                    ("kc", "m06", "world", {"M": 1, "T": -1}, "1/2", None),
                    ("kd", "m07", "world", {"M": 1, "T": -1}, "-4/3", None)],
        law=("lw", "en = kb*hz^2", 1),
        observers=[("o1", "i04", "1/45", [])],
        fillers=[("f1", "en = kb*hz^2 + xn*kc*vz + xn*kd*hz", [],
                  [NQ("xn", "scalar", "m07", "world", "?", "?", "0", "?")])],
        obs=[("o1", {"hz": "1", "vz": "1"}, 0, None, "-9/10"),
             ("o1", {"hz": "-3/2", "vz": "2"}, 1, None, "22/25"),
             ("o1", {"hz": "2", "vz": "-1"}, 2, ("f1", {"xn": "2/3"}), "1/5"),
             ("o1", {"hz": "1/2", "vz": "3"}, 3, ("f1", {"xn": "2/3"}), "-1/4")],
        intent={"f1": INVALID})


@spec
def I3():
    return dict(
        label="I3", note="INVALID: a new charge-like quantity of unknown meaning with written dims Q T; the term qn*ez*hz^2/dd is then not an energy.",
        bodies=[("kb0", "ty02")],
        quantities=[("en", "m03", "world", E, "var", None), ("qa", "m04", "kb0", QD, "3/2", None),
                    ("e", "m17", "world", EF, "var", vec("e")), ("h", "m12", "kb0", LD, "var", vec("h")),
                    ("w0", "m03", "world", E, "-5/6", None), ("dd", "m11", "world", LD, "var", None)],
        law=("lw", "en = qa*ez*hz + w0", 2),
        observers=[("o1", "i04", "1/35", [])],
        fillers=[("f1", "en = qa*ez*hz + w0 + qn*ez*hz^2/dd", [],
                  [NQ("qn", "scalar", "?", "world", {"Q": 1, "T": 1}, "?", "0", "i05",
                      under={"rev_t": "1", "refl_x": "1", "conj_c": "-1"})])],
        obs=[("o1", {"ez": "1", "hz": "1", "dd": "2"}, 0, None, "9/10"),
             ("o1", {"ez": "-2", "hz": "1/2", "dd": "1"}, 1, None, "-9/10"),
             ("o1", {"ez": "3/2", "hz": "-1", "dd": "3"}, 2, None, "4/5"),
             ("o1", {"ez": "2", "hz": "2", "dd": "1"}, 3, ("f1", {"qn": "-1/2"}), "1/5"),
             ("o1", {"ez": "-1", "hz": "3", "dd": "2"}, 4, ("f1", {"qn": "-1/2"}), "0")],
        intent={"f1": INVALID})


@spec
def C1():
    return dict(
        label="C1", note="T7 (registry m10): a world field sv with untested time reversal enters the filler as cn*sv*vz; keeping assignment sv:rev_t = -1.",
        bodies=[("gb", "ty07")],
        quantities=[("f", "m16", "gb", FD, "var", vec("f")), ("kk", "m05", "world", {"M": 1, "T": -2}, "13/5", None),
                    ("h", "m12", "gb", LD, "var", vec("h")), ("ma", "m02", "gb", MD, "2/3", None),
                    ("g", "m21", "world", ACC, ["0", "0", "-19/2"], vec("g")),
                    ("sv", "m10", "world", {"M": 1, "L": -1, "Q": 1}, "var", None),
                    ("v", "m13", "gb", VEL, "var", vec("v"))],
        law=("lw", "fz = ma*gz - kk*hz", 2),
        observers=[("o1", "i06", "1/40", [])],
        fillers=[("f1", "fz = ma*gz - kk*hz + cn*sv*vz", [],
                  [NQ("cn", "scalar", "m07", "world", "?", "?", "0", "?")])],
        obs=[("o1", {"hz": "1", "sv": "2", "vz": "1"}, 0, None, "-9/10"),
             ("o1", {"hz": "-1/2", "sv": "-1", "vz": "3"}, 1, None, "21/25"),
             ("o1", {"hz": "2", "sv": "1/2", "vz": "-2"}, 2, None, "-24/25"),
             ("o1", {"hz": "1", "sv": "2", "vz": "2"}, 3, ("f1", {"cn": "5/6"}), "1/5"),
             ("o1", {"hz": "3/2", "sv": "-3", "vz": "1"}, 4, ("f1", {"cn": "5/6"}), "-1/4")],
        intent={"f1": COND})


@spec
def C2():
    return dict(
        label="C2", note="T7 (registry m09) + T8 (axial, refl_x): a coupling with untested mirror behaviour times the torque's z part; keeping cp:refl_x = -1.",
        bodies=[("nb0", "ty01")],
        quantities=[("en", "m03", "world", E, "var", None), ("w0", "m03", "world", E, "5/8", None),
                    ("kn", "m07", "world", {"M": -1, "L": -2, "T": 2}, "3/2", None),
                    ("n", "m20", "nb0", E, "var", vec("n"))],
        law=("lw", "en = w0 + kn*(nx^2 + ny^2 + nz^2)", 1),
        observers=[("o1", "i04", "1/40", []), ("o2", "i04", "1/64", ["o1"])],
        fillers=[("f1", "en = w0 + kn*(nx^2 + ny^2 + nz^2) + cp*nz", [],
                  [NQ("cp", "scalar", "m09", "world", "?", "?", "0", "?")])],
        obs=[("o1", {"nx": "1/2", "ny": "1", "nz": "-1/2"}, 0, None, "9/10"),
             ("o2", {"nx": "0", "ny": "-1", "nz": "1"}, 1, None, "-22/25"),
             ("o1", {"nx": "1", "ny": "1/2", "nz": "2"}, 1, None, "-9/10"),
             ("o2", {"nx": "1", "ny": "0", "nz": "1"}, 2, ("f1", {"cp": "-3/10"}), "1/5"),
             ("o1", {"nx": "-1/2", "ny": "1", "nz": "-2"}, 3, ("f1", {"cp": "-3/10"}), "-1/4"),
             ("o2", {"nx": "0", "ny": "1/2", "nz": "3/2"}, 3, ("f1", {"cp": "-3/10"}), "0")],
        intent={"f1": COND})


@spec
def C3():
    return dict(
        label="C3", note="T7 (new '?', conj_c): an unknown quantity zq times ez*dd; keeping zq:conj_c = -1 (it would act like a charge).",
        bodies=[("zb", "ty03")],
        quantities=[("en", "m03", "world", E, "var", None), ("qa", "m04", "zb", QD, "-2/3", None),
                    ("e", "m17", "world", EF, "var", vec("e")), ("h", "m12", "zb", LD, "var", vec("h")),
                    ("kv", "m07", "world", {}, "5/9", None), ("ma", "m02", "zb", MD, "3/2", None),
                    ("v", "m13", "zb", VEL, "var", vec("v")), ("dd", "m11", "world", LD, "var", None)],
        law=("lw", "en = qa*ez*hz + kv*ma*vz^2", 2),
        observers=[("o1", "i04", "1/50", [])],
        fillers=[("f1", "en = qa*ez*hz + kv*ma*vz^2 + zq*ez*dd", [],
                  [NQ("zq", "scalar", "?", "world", "?", "?", "0", "i05",
                      under={"rev_t": "1", "refl_x": "1", "conj_c": "?"})])],
        obs=[("o1", {"ez": "1", "hz": "2", "vz": "1", "dd": "1"}, 0, None, "-9/10"),
             ("o1", {"ez": "-3/2", "hz": "1", "vz": "-2", "dd": "2"}, 1, None, "23/25"),
             ("o1", {"ez": "2", "hz": "-1/2", "vz": "1/2", "dd": "3"}, 2, None, "-21/25"),
             ("o1", {"ez": "1", "hz": "1", "vz": "1", "dd": "2"}, 3, ("f1", {"zq": "7/4"}), "1/5"),
             ("o1", {"ez": "-2", "hz": "3/2", "vz": "1", "dd": "1"}, 4, ("f1", {"zq": "7/4"}), "-1/4")],
        intent={"f1": COND})


@spec
def C4():
    return dict(
        label="C4", note="T7 (new '?', unknown kind, rot_z): uq*(hx^2 - hy^2) is odd under a quarter turn, so the keeping assignment is uq:rot_z = -1.",
        bodies=[("qb0", "ty04")],
        quantities=[("en", "m03", "world", E, "var", None), ("ka", "m05", "world", {"M": 1, "T": -2}, "3/2", None),
                    ("kb", "m05", "world", {"M": 1, "T": -2}, "7/5", None), ("h", "m12", "qb0", LD, "var", vec("h"))],
        law=("lw", "en = ka*(hx^2 + hy^2) + kb*hz^2", 2),
        observers=[("o1", "i04", "1/30", [])],
        fillers=[("f1", "en = ka*(hx^2 + hy^2) + kb*hz^2 + uq*(hx^2 - hy^2)", [],
                  [NQ("uq", "?", "?", "world", "?", "?", "0", "?",
                      under={"rev_t": "1", "refl_x": "1", "conj_c": "1"})])],
        obs=[("o1", {"hx": "1", "hy": "1", "hz": "1"}, 0, None, "9/10"),
             ("o1", {"hx": "2", "hy": "-1", "hz": "0"}, 1, None, "-9/10"),
             ("o1", {"hx": "-1/2", "hy": "1/2", "hz": "2"}, 2, None, "93/100"),
             ("o1", {"hx": "2", "hy": "1", "hz": "1"}, 3, ("f1", {"uq": "2/5"}), "1/5"),
             ("o1", {"hx": "1", "hy": "-2", "hz": "1/2"}, 3, ("f1", {"uq": "2/5"}), "-1/4"),
             ("o1", {"hx": "3", "hy": "1", "hz": "-1"}, 4, ("f1", {"uq": "2/5"}), "0")],
        intent={"f1": COND})


@spec
def C5():
    return dict(
        label="C5", note="T7, two branches: rev_t through the world field sv (registry m10, keeping +1), refl_x through pq (new '?', keeping -1).",
        bodies=[("hb", "ty05")],
        quantities=[("en", "m03", "world", E, "var", None), ("w0", "m03", "world", E, "-11/4", None),
                    ("kk", "m05", "world", {"M": 1, "T": -2}, "2/5", None), ("h", "m12", "hb", LD, "var", vec("h")),
                    ("sv", "m10", "world", {"T": 1, "Q": -1}, "var", None), ("n", "m20", "hb", E, "var", vec("n"))],
        law=("lw", "en = w0 + kk*hz^2", 3),
        observers=[("o1", "i04", "1/20", [])],
        fillers=[("f1", "en = w0 + kk*hz^2 + c1*sv*hz + pq*nz", [],
                  [NQ("c1", "scalar", "m07", "world", "?", "?", "0", "?"),
                   NQ("pq", "scalar", "?", "world", "?", "?", "0", "?",
                      under={"rev_t": "1", "refl_x": "?", "conj_c": "1"})])],
        obs=[("o1", {"hz": "1", "sv": "1", "nz": "2"}, 0, None, "-9/10"),
             ("o1", {"hz": "2", "sv": "-2", "nz": "1"}, 1, None, "4/5"),
             ("o1", {"hz": "-1", "sv": "1/2", "nz": "-1"}, 2, None, "-19/20"),
             ("o1", {"hz": "1/2", "sv": "3", "nz": "0"}, 3, None, "22/25"),
             ("o1", {"hz": "1", "sv": "2", "nz": "1"}, 4, ("f1", {"c1": "-1/3", "pq": "1/2"}), "1/5"),
             ("o1", {"hz": "2", "sv": "1", "nz": "-2"}, 5, ("f1", {"c1": "-1/3", "pq": "1/2"}), "-1/4"),
             ("o1", {"hz": "-1", "sv": "-1", "nz": "3"}, 5, ("f1", {"c1": "-1/3", "pq": "1/2"}), "0")],
        intent={"f1": COND})


@spec
def C6():
    return dict(
        label="C6", note="T7: the law itself holds an untested-time field (sv, m10); the filler scales its term by un (new '?', old value 1). Only un matters; keeping un:rev_t = +1 for both signs of sv.",
        bodies=[("lb", "ty06")],
        quantities=[("en", "m03", "world", E, "var", None), ("w0", "m03", "world", E, "9/7", None),
                    ("kb", "m05", "world", {"M": 1, "T": -2}, "4/3", None), ("h", "m12", "lb", LD, "var", vec("h")),
                    ("sv", "m10", "world", {"M": 1, "L": 1, "T": -1}, "var", None),
                    ("v", "m13", "lb", VEL, "var", vec("v")), ("ka", "m07", "world", {}, "-5/6", None)],
        law=("lw", "en = w0 + kb*hz^2 + ka*sv*vz", 2),
        observers=[("o1", "i04", "1/50", [])],
        fillers=[("f1", "en = w0 + kb*hz^2 + ka*sv*vz*un", [],
                  [NQ("un", "scalar", "?", "world", "?", "?", "1", "?",
                      under={"rev_t": "?", "refl_x": "1", "conj_c": "1"})])],
        obs=[("o1", {"hz": "1", "sv": "1", "vz": "2"}, 0, None, "9/10"),
             ("o1", {"hz": "-2", "sv": "2", "vz": "-1"}, 1, None, "-23/25"),
             ("o1", {"hz": "1/2", "sv": "-1", "vz": "3"}, 2, None, "-4/5"),
             ("o1", {"hz": "1", "sv": "2", "vz": "1"}, 3, ("f1", {"un": "-3/5"}), "1/5"),
             ("o1", {"hz": "3/2", "sv": "1", "vz": "-2"}, 4, ("f1", {"un": "-3/5"}), "-1/4")],
        intent={"f1": COND})


@spec
def C7():
    return dict(
        label="C7", note="T7 + T8 (m23, rev_t): gq*fa*fb with gq of unknown meaning; rev_t and conj_c are each conditional, keeping -1 for each.",
        bodies=[("mb0", "ty08")],
        quantities=[("en", "m03", "world", E, "var", None),
                    ("ps", "m23", "world", {"Q": 1, "L": -1}, "var", ["fa", "fb"]),
                    ("kz", "m07", "world", {"M": 1, "L": 4, "T": -2, "Q": -2}, "2/3", None),
                    ("kh", "m07", "world", FD, "-7/4", None), ("h", "m12", "mb0", LD, "var", vec("h"))],
        law=("lw", "en = kz*(fa^2 + fb^2) + kh*hz", 1),
        observers=[("o1", "i04", "1/40", [])],
        fillers=[("f1", "en = kz*(fa^2 + fb^2) + kh*hz + gq*fa*fb", [],
                  [NQ("gq", "scalar", "?", "world", "?", "?", "0", "?",
                      under={"rev_t": "?", "refl_x": "1", "conj_c": "?"})])],
        obs=[("o1", {"fa": "1", "fb": "1", "hz": "1"}, 0, None, "-9/10"),
             ("o1", {"fa": "2", "fb": "-1", "hz": "1/2"}, 1, None, "21/25"),
             ("o1", {"fa": "1", "fb": "2", "hz": "2"}, 2, ("f1", {"gq": "6/5"}), "1/5"),
             ("o1", {"fa": "-3/2", "fb": "1", "hz": "-1"}, 3, ("f1", {"gq": "6/5"}), "-1/4")],
        intent={"f1": COND})


@spec
def M1():
    nn = {"qn": "2/5"}
    return dict(
        label="M1", note="T9 + T1: two kept fillers: a second charge with the body ((qa+qn)*ez) or a cubic stiffness (cm*hz^3); the new data have ez = 2*hz^3.",
        bodies=[("pb", "ty02")],
        quantities=[("f", "m16", "pb", FD, "var", vec("f")), ("qa", "m04", "pb", QD, "3/4", None),
                    ("e", "m17", "world", EF, "var", vec("e")),
                    ("kk", "m05", "world", {"M": 1, "T": -2}, "5/2", None), ("h", "m12", "pb", LD, "var", vec("h"))],
        law=("lw", "fz = qa*ez - kk*hz", 2),
        observers=[("o1", "i06", "1/100", []), ("o2", "i06", "1/150", ["o1"])],
        fillers=[("f1", "fz = (qa + qn)*ez - kk*hz", [("nb", "ty05")],
                  [NQ("qn", "scalar", "m04", "nb", "?", "?", "0", "i05")]),
                 ("f2", "fz = qa*ez - kk*hz + cm*hz^3", [],
                  [NQ("cm", "scalar", "m05", "world", "?", "?", "0", "?")])],
        obs=[("o1", {"ez": "1", "hz": "1"}, 0, None, "9/10"),
             ("o2", {"ez": "-2", "hz": "1/2"}, 1, None, "-22/25"),
             ("o1", {"ez": "3", "hz": "-1"}, 2, None, "-9/10"),
             ("o2", {"ez": "2", "hz": "1"}, 3, ("f1", nn), "1/10"),
             ("o1", {"ez": "-2", "hz": "-1"}, 3, ("f1", nn), "-1/10"),
             ("o2", {"ez": "1/4", "hz": "1/2"}, 4, ("f1", nn), "1/20"),
             ("o1", {"ez": "27/4", "hz": "3/2"}, 4, ("f1", nn), "0")],
        decisive=[(("f1", "f2"), {"ez": "3", "hz": "0"}, "o2")],
        intent={"f1": SAME, "f2": SAME})


@spec
def M2():
    nn = {"c1": "1/2"}
    return dict(
        label="M2", note="T9: two kept fillers (c1*hz, c2*hz^3) and a third that breaks the quarter turn (c3*hx^2); new data at hz = 3/2, hx = 1/2.",
        bodies=[("ob", "ty07")],
        quantities=[("en", "m03", "world", E, "var", None), ("kb", "m07", "world", {}, "2/3", None),
                    ("ma", "m02", "ob", MD, "5/3", None), ("tc", "m01", "world", TD, "3/2", None),
                    ("h", "m12", "ob", LD, "var", vec("h"))],
        law=("lw", "en = kb*(hx^2 + hy^2 + hz^2)*ma/tc^2", 2),
        observers=[("o1", "i04", "1/25", [])],
        fillers=[("f1", "en = kb*(hx^2 + hy^2 + hz^2)*ma/tc^2 + c1*hz", [],
                  [NQ("c1", "scalar", "m07", "world", "?", "?", "0", "?")]),
                 ("f2", "en = kb*(hx^2 + hy^2 + hz^2)*ma/tc^2 + c2*hz^3", [],
                  [NQ("c2", "scalar", "m07", "world", "?", "?", "0", "?")]),
                 ("f3", "en = kb*(hx^2 + hy^2 + hz^2)*ma/tc^2 + c3*hx^2", [],
                  [NQ("c3", "scalar", "m05", "world", "?", "?", "0", "?")])],
        obs=[("o1", {"hx": "1", "hy": "2", "hz": "-1"}, 0, None, "9/10"),
             ("o1", {"hx": "-1/2", "hy": "1", "hz": "2"}, 1, None, "-21/25"),
             ("o1", {"hx": "2", "hy": "0", "hz": "1"}, 2, None, "-24/25"),
             ("o1", {"hx": "1/2", "hy": "0", "hz": "3/2"}, 3, ("f1", nn), "1/5"),
             ("o1", {"hx": "1/2", "hy": "1", "hz": "3/2"}, 4, ("f1", nn), "-1/5"),
             ("o1", {"hx": "1/2", "hy": "-2", "hz": "3/2"}, 4, ("f1", nn), "0")],
        decisive=[(("f1", "f2"), {"hx": "0", "hy": "0", "hz": "3"}, "o1")],
        intent={"f1": SAME, "f2": SAME, "f3": ANOTHER})


@spec
def M3():
    nn = {"cm": "3/10"}
    return dict(
        label="M3", note="T9: a hidden mass (cm) or an unaccounted constant force (cf) both fit at az = 1/5; a third filler adds kr*cq with cq a distance: not a mass (INVALID).",
        bodies=[("wb", "ty03")],
        quantities=[("mb", "m02", "wb", MD, "var", None), ("ka", "m07", "world", {}, "5/4", None),
                    ("f", "m16", "wb", FD, "var", vec("f")), ("a", "m14", "wb", ACC, "var", vec("a")),
                    ("kg", "m07", "world", ACC, "49/5", None), ("kr", "m07", "world", {"M": 1, "L": -2}, "3/2", None)],
        law=("lw", "mb = ka*fz/(az + kg)", 1),
        observers=[("o1", "i03", "1/200", []), ("o2", "i03", "1/300", ["o1"])],
        fillers=[("f1", "mb = ka*fz/(az + kg) + cm", [("nb", "ty06")],
                  [NQ("cm", "scalar", "m02", "nb", "?", "?", "0", "i03")]),
                 ("f2", "mb = ka*fz/(az + kg) + kr*cq", [],
                  [NQ("cq", "scalar", "m11", "world", "?", "?", "0", "i02")]),
                 ("f3", "mb = ka*(fz + cf)/(az + kg)", [],
                  [NQ("cf", "scalar", "m07", "world", "?", "?", "0", "i06")])],
        obs=[("o1", {"fz": "8", "az": "0"}, 0, None, "-9/10"),
             ("o2", {"fz": "15", "az": "1/5"}, 1, None, "22/25"),
             ("o1", {"fz": "-4", "az": "-1"}, 1, None, "4/5"),
             ("o2", {"fz": "5", "az": "1/5"}, 2, ("f1", nn), "1/10"),
             ("o1", {"fz": "-3", "az": "1/5"}, 3, ("f1", nn), "-1/10"),
             ("o2", {"fz": "12", "az": "1/5"}, 3, ("f1", nn), "0")],
        decisive=[(("f1", "f3"), {"fz": "1", "az": "-9"}, "o2")],
        intent={"f1": SAME, "f2": INVALID, "f3": SAME})


@spec
def M4():
    nn = {"qn": "-1/2"}
    return dict(
        label="M4", note="T9 + T1: three kept fillers (a second charge qn, a hidden mass mn, a 1/dd^2 interaction cx) fit new data taken at dd = 1 with hz = qa/2.",
        bodies=[("ab", "ty04"), ("bb", "ty01")],
        quantities=[("en", "m03", "world", E, "var", None),
                    ("kc", "m07", "world", {"M": 1, "L": 3, "T": -2, "Q": -2}, "1/3", None),
                    ("qa", "m04", "ab", QD, "var", None), ("qb", "m04", "bb", QD, "-4/5", None),
                    ("dd", "m11", "world", LD, "var", None), ("ma", "m02", "ab", MD, "7/4", None),
                    ("g", "m21", "world", ACC, ["0", "0", "-10"], vec("g")), ("h", "m12", "ab", LD, "var", vec("h"))],
        law=("lw", "en = kc*qa*qb/dd + ma*gz*hz", 2),
        observers=[("o1", "i04", "1/40", [])],
        fillers=[("f1", "en = kc*qa*(qb + qn)/dd + ma*gz*hz", [("nb", "ty06")],
                  [NQ("qn", "scalar", "m04", "nb", "?", "?", "0", "i05")]),
                 ("f2", "en = kc*qa*qb/dd + (ma + mn)*gz*hz", [("nc", "ty06")],
                  [NQ("mn", "scalar", "m02", "nc", "?", "?", "0", "i03")]),
                 ("f3", "en = kc*qa*qb/dd + ma*gz*hz + cx*qa*qb/dd^2", [],
                  [NQ("cx", "scalar", "m07", "world", "?", "?", "0", "?")])],
        obs=[("o1", {"qa": "1", "dd": "2", "hz": "1"}, 0, None, "-9/10"),
             ("o1", {"qa": "-2", "dd": "3/2", "hz": "-1/2"}, 1, None, "22/25"),
             ("o1", {"qa": "3", "dd": "1", "hz": "2"}, 2, None, "-21/25"),
             ("o1", {"qa": "1", "dd": "1", "hz": "1/2"}, 3, ("f1", nn), "1/10"),
             ("o1", {"qa": "-2", "dd": "1", "hz": "-1"}, 3, ("f1", nn), "-1/10"),
             ("o1", {"qa": "3", "dd": "1", "hz": "3/2"}, 4, ("f1", nn), "1/20"),
             ("o1", {"qa": "1/2", "dd": "1", "hz": "1/4"}, 4, ("f1", nn), "0")],
        decisive=[(("f1", "f2"), {"qa": "4", "dd": "1", "hz": "0"}, "o1"),
                  (("f1", "f3"), {"qa": "2", "dd": "1/4", "hz": "1"}, "o1"),
                  (("f2", "f3"), {"qa": "4", "dd": "1", "hz": "0"}, "o1")],
        intent={"f1": SAME, "f2": SAME, "f3": SAME})


@spec
def M5():
    nn = {"cz": "1/2"}
    return dict(
        label="M5", note="T9 + T6: identical bodies; fa (pair used asymmetrically: ANOTHER by exchange, though its fitted values look symmetric), fb (pair used symmetrically; FIX misses it), fc (one symmetric constant).",
        bodies=[("ba", "ty06"), ("bb", "ty06")],
        quantities=[("en", "m03", "world", E, "var", None), ("ks", "m05", "world", {"M": 1, "T": -2}, "3/4", None),
                    ("kg", "m07", "world", FD, "-5/2", None),
                    ("h1", "m12", "ba", LD, "var", vec("h1")), ("h2", "m12", "bb", LD, "var", vec("h2"))],
        law=("lw", "en = ks*(h1z - h2z)^2 + kg*(h1z + h2z)", 2),
        observers=[("o1", "i04", "1/60", [])],
        fillers=[("fa", "en = ks*(h1z - h2z)^2 + kg*(h1z + h2z) + ca1*h1z^2 + ca2*h1z*h2z", [],
                  [NQ("ca1", "scalar", "m07", "ba", "?", "?", "0", "?"),
                   NQ("ca2", "scalar", "m07", "bb", "?", "?", "0", "?")]),
                 ("fb", "en = ks*(h1z - h2z)^2 + kg*(h1z + h2z) + cb1*h1z^2 + cb2*h2z^2", [],
                  [NQ("cb1", "scalar", "m07", "ba", "?", "?", "0", "?"),
                   NQ("cb2", "scalar", "m07", "bb", "?", "?", "0", "?")]),
                 ("fc", "en = ks*(h1z - h2z)^2 + kg*(h1z + h2z) + cz*h1z*h2z", [],
                  [NQ("cz", "scalar", "m07", "world", "?", "?", "0", "?")])],
        obs=[("o1", {"h1z": "1", "h2z": "2"}, 0, None, "9/10"),
             ("o1", {"h1z": "-1", "h2z": "1/2"}, 1, None, "-22/25"),
             ("o1", {"h1z": "2", "h2z": "-1"}, 2, None, "-9/10"),
             ("o1", {"h1z": "1", "h2z": "2"}, 3, ("fc", nn), "1/10"),
             ("o1", {"h1z": "2", "h2z": "1"}, 3, ("fc", nn), "-1/8"),
             ("o1", {"h1z": "2", "h2z": "4"}, 4, ("fc", nn), "1/20")],
        decisive=[(("fb", "fc"), {"h1z": "1", "h2z": "-1"}, "o1")],
        intent={"fa": ANOTHER, "fb": SAME, "fc": SAME})


# =====================================================================================================
# building, renaming, writing
# =====================================================================================================

def sp_eval(eq, values):
    rhs = V.to_sp(V.parse_eq(eq)[1])
    val = rhs.xreplace({sp.Symbol(k): sp.Rational(v) for k, v in values.items()})
    if not val.is_Rational:
        raise ValueError(f"cannot evaluate {eq} at {values}: {val}")
    return Fr(int(val.p), int(val.q))


def constants(s):
    out = {}
    for qid, _m, _o, _d, value, comps in s["quantities"]:
        if value == "var":
            continue
        if comps:
            for c, v in zip(comps, value):
                out[c] = v
        else:
            out[qid] = value
    return out


def build(s):
    doc = {"v0": "0.4", "file": "world", "id": "wxx", "registry": "test4_registry", "registry_sha256": REG.sha,
           "bodies": [{"id": b, "type": t, "src": "seed"} for b, t in s["bodies"]], "quantities": [],
           "relations": [], "laws": [], "observers": [], "observations": [], "fillers": []}
    for qid, m, owner, dims, value, comps in s["quantities"]:
        doc["quantities"].append({"id": qid, "meaning": m, "owner": owner, "dims": dims,
                                  "components": comps or [], "value": value, "src": "seed"})
    lid, leq, acc = s["law"]
    doc["laws"].append({"id": lid, "eq": leq, "accepted_at": acc, "src": "seed"})
    prec = {}
    for oid, inst, p, cal in s["observers"]:
        doc["observers"].append({"id": oid, "instrument": inst, "precision": p, "calibrated_against": cal,
                                 "src": "seed"})
        prec[oid] = Fr(p)
    feqs = {}
    for fid, feq, nbs, news in s["fillers"]:
        doc["fillers"].append({"id": fid, "of": lid, "eq": feq,
                               "new_bodies": [{"id": b, "type": t} for b, t in nbs], "new": news, "src": "seed"})
        feqs[fid] = feq
    consts = constants(s)
    yname = leq.split("=")[0].strip()
    for i, (oid, state, epoch, truth, off) in enumerate(s["obs"]):
        vals = {**consts, **state}
        if truth is None:
            pred = sp_eval(leq, vals)
        else:
            fid, params = truth
            pred = sp_eval(feqs[fid], {**vals, **params})
        value = pred + Fr(off) * prec[oid]
        doc["observations"].append({"id": f"ob{i + 1}", "observer": oid, "of": yname, "state": state,
                                    "value": str(value), "epoch": epoch, "src": oid})
    return doc


CONS = "bdfgklmnprstvz"
VOWS = "aeiou"
AVOID = {"mas", "vel", "pos", "tim", "rot", "spin", "law", "fil", "mass", "time", "rate", "force", "field",
         "tor", "tork", "pot", "kin", "ener", "nul", "zero", "same", "var", "seed", "world", "law", "obs",
         "mol", "pol", "axi", "dip", "mag", "mov", "dam", "rev", "ref", "con", "fit", "new", "old"}


def make_namer(rng, taken):
    def name():
        while True:
            k = rng.choice((2, 2, 3))
            s = "".join(rng.choice(CONS) + rng.choice(VOWS) for _ in range(k))
            if rng.random() < 0.35:
                s += rng.choice(CONS)
            if rng.random() < 0.2:
                s += str(rng.randint(2, 9))
            s = s[:6]
            if (len(s) >= 3 and s not in taken and s not in REG.ids and not any(a in s for a in AVOID)
                    and not s.startswith(("ex", "ob", "co"))):
                taken.add(s)
                return s
    return name


def rename_doc(doc, rng):
    taken = set()
    name = make_namer(rng, taken)
    labels = []
    for b in doc["bodies"]:
        labels.append(b["id"])
    for q in doc["quantities"]:
        labels.append(q["id"])
        labels += q["components"]
    for l in doc["laws"]:
        labels.append(l["id"])
    for o in doc["observers"]:
        labels.append(o["id"])
    for o in doc["observations"]:
        labels.append(o["id"])
    for f in doc["fillers"]:
        labels.append(f["id"])
        labels += [b["id"] for b in f["new_bodies"]]
        for nq in f["new"]:
            labels.append(nq["id"])
            if isinstance(nq["components"], list):
                labels += nq["components"]
    order = list(dict.fromkeys(labels))
    rng.shuffle(order)
    mp = {lab: name() for lab in order}
    # bodies keep file order = sorted order of their new names, so exch(b1,b2) is unambiguous
    bnames = sorted(mp[b["id"]] for b in doc["bodies"])
    for b, nm in zip(doc["bodies"], bnames):
        mp[b["id"]] = nm

    def r(x):
        return mp.get(x, x)

    def req(eq):
        import re
        return re.sub(r"\b[a-z][a-z0-9_]*\b", lambda m: r(m.group(0)), eq)

    for b in doc["bodies"]:
        b["id"] = r(b["id"])
    for q in doc["quantities"]:
        q["id"], q["owner"] = r(q["id"]), r(q["owner"])
        q["components"] = [r(c) for c in q["components"]]
    for l in doc["laws"]:
        l["id"], l["eq"] = r(l["id"]), req(l["eq"])
    for o in doc["observers"]:
        o["id"] = r(o["id"])
        o["calibrated_against"] = [r(c) for c in o["calibrated_against"]]
    for o in doc["observations"]:
        o["id"], o["observer"], o["of"], o["src"] = r(o["id"]), r(o["observer"]), r(o["of"]), r(o["src"])
        o["state"] = {r(k): v for k, v in o["state"].items()}
    for f in doc["fillers"]:
        f["id"], f["of"], f["eq"] = r(f["id"]), r(f["of"]), req(f["eq"])
        for b in f["new_bodies"]:
            b["id"] = r(b["id"])
        for nq in f["new"]:
            nq["id"], nq["owner"] = r(nq["id"]), r(nq["owner"])
            if isinstance(nq["components"], list):
                nq["components"] = [r(c) for c in nq["components"]]
    return mp


def reorder_fields(doc):
    out = {k: doc[k] for k in ("v0", "file", "id", "registry", "registry_sha256", "bodies", "quantities",
                               "relations", "laws", "observers", "observations", "fillers")}
    for f in out["fillers"]:
        f["new"] = [{k: nq[k] for k in ("id", "kind", "meaning", "owner", "dims", "components", "under", "value",
                                         "old_value", "route")} for nq in f["new"]]
    return out


def main():
    rng = random.Random(20261007)
    order = list(range(len(SPECS)))
    rng.shuffle(order)
    assert len(SPECS) == 30, len(SPECS)
    os.makedirs(os.path.join(ROOT, "worlds"), exist_ok=True)
    key = []
    mapping_log = {}
    for slot, idx in enumerate(order, start=1):
        s = SPECS[idx]
        wid = f"W-{slot:02d}"
        doc = build(s)
        doc["id"] = f"w{slot:02d}"
        mp = rename_doc(doc, random.Random(1000 + slot))
        doc = reorder_fields(doc)
        path = os.path.join(ROOT, "worlds", f"{wid}.json")
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        W, cards, groups = V.analyze_world(REG, doc, path, with_group=False)
        fillers = {}
        for F in W.fillers:
            c = cards[F.id]
            ent = {"verdict": s["intent"][next(k for k, v in mp.items() if v == F.id)]}
            if c["verdict"] != INVALID:
                ent["F2"] = {t: res["status"] for t, res in c["F2"].items()}
            fillers[F.id] = ent
        multi = len(W.fillers) > 1
        # the sealed validator's reference lists kept fillers sorted by id (run 1 of the validator)
        kept = sorted(F.id for F in W.fillers if fillers[F.id]["verdict"] == SAME) if multi else None
        decisive = None
        if multi:
            decisive = []
            for (a, b), state, obs in s.get("decisive", []):
                decisive.append({"pair": [mp[a], mp[b]], "state": {mp[k]: v for k, v in state.items()},
                                 "observer": mp[obs]})
        traps = sorted({t for F in W.fillers for t in V.trap_flags(W, F, cards[F.id], None)})
        key.append({"id": wid, "fillers": fillers, "kept": kept, "decisive": decisive, "traps": traps,
                    "notes": f"[{s['label']}] {s['note']}"})
        mapping_log[wid] = {"label": s["label"], "names": mp}
        print(wid, s["label"], {F.id: (cards[F.id]["verdict"], s["intent"][next(k for k, v in mp.items() if v == F.id)])
                                 for F in W.fillers}, traps)
    with open(os.path.join(HERE, "key.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(key, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    with open(os.path.join(HERE, "name_map.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(mapping_log, fh, ensure_ascii=False, indent=1)
        fh.write("\n")


if __name__ == "__main__":
    main()
