from fractions import Fraction as F
from wcore import *
from wcore import _reduce_vec
def kernel_dim(rows, ncols):
    piv = []
    r = 0
    for row in rows:
        v = _reduce_vec(list(row), piv)
        for k, x in enumerate(v):
            if x:
                piv.append((k, [y / x for y in v])); r += 1; break
    return ncols - r
def socle_dim(mats):
    """dim of {x : g x = 0 for every generator matrix g} (generators assumed to span the radical)."""
    m = len(mats[0])
    rows = [row for M in mats for row in M]
    return kernel_dim(rows, m)
