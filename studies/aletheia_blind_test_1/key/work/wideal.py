# Truncated two-sided ideal engine in the free associative algebra over Q.
# I_D = span{u*r*v : r relation, |u|+deg(r)+|v| <= D}  (always a subset of the true ideal),
# kept in echelon form with deglex leading words. Membership found in I_D is a proof.
from fractions import Fraction as F
import itertools


def dkey(w):
    return (len(w), w)


def family_relations(grades, fam):
    n = len(grades)
    rels = []
    if fam == "comm":
        for i in range(n):
            for j in range(i + 1, n):
                rels.append({(i, j): F(1), (j, i): F(-1)})
    elif fam == "graded":
        for i in range(n):
            for j in range(i, n):
                odd = (grades[i] * grades[j]) % 2 == 1
                if i == j:
                    if odd:
                        rels.append({(i, i): F(1)})
                else:
                    rels.append({(i, j): F(1), (j, i): F(1) if odd else F(-1)})
    elif fam != "assoc":
        raise ValueError(fam)
    return rels


class TruncIdeal:
    def __init__(self, ngens, rels, D, max_rows=None):
        self.n = ngens
        self.D = D
        self.piv = {}
        self.rows_used = 0
        rels = [r for r in rels if r]
        # insert low-degree products first (keeps echelon small)
        items = []
        for idx, r in enumerate(rels):
            d = max(len(w) for w in r)
            for s in range(0, D - d + 1):
                items.append((d + s, idx, s))
        items.sort()
        for tot, idx, s in items:
            r = rels[idx]
            for ulen in range(0, s + 1):
                vlen = s - ulen
                for u in itertools.product(range(ngens), repeat=ulen):
                    for v in itertools.product(range(ngens), repeat=vlen):
                        self.insert({u + w + v: c for w, c in r.items()})
                        self.rows_used += 1
                        if max_rows and self.rows_used > max_rows:
                            raise RuntimeError("row budget exceeded")
            if () in self.piv:
                # 1 is in the ideal: everything is; stop early
                self.contradiction = True
                return
        self.contradiction = () in self.piv

    def insert(self, row):
        row = {w: c for w, c in row.items() if c != 0}
        piv = self.piv
        while row:
            lw = max(row, key=dkey)
            p = piv.get(lw)
            if p is None:
                c = row[lw]
                piv[lw] = {w: v / c for w, v in row.items()}
                return True
            c = row[lw]
            for w, v in p.items():
                nv = row.get(w, 0) - c * v
                if nv == 0:
                    row.pop(w, None)
                else:
                    row[w] = nv
        return False

    def reduce(self, poly):
        row = {w: F(c) for w, c in poly.items() if c != 0}
        out = {}
        piv = self.piv
        while row:
            lw = max(row, key=dkey)
            c = row.pop(lw)
            p = piv.get(lw)
            if p is None:
                out[lw] = c
                continue
            for w, v in p.items():
                if w == lw:
                    continue
                nv = row.get(w, 0) - c * v
                if nv == 0:
                    row.pop(w, None)
                else:
                    row[w] = nv
        return out

    def contains(self, poly):
        if self.contradiction:
            return True
        return len(self.reduce(poly)) == 0

    def dim_upper_bound(self):
        """If some length k<=D has all words as leading words, the presented algebra is
        spanned by the non-leading words of length < k: return that count (else None)."""
        if self.contradiction:
            return 0
        for k in range(0, self.D + 1):
            if all(w in self.piv for w in itertools.product(range(self.n), repeat=k)):
                cnt = 0
                for L in range(0, k):
                    for w in itertools.product(range(self.n), repeat=L):
                        if w not in self.piv:
                            cnt += 1
                return cnt
        return None


def poly_mul(p, q):
    out = {}
    for a, c in p.items():
        for b, d in q.items():
            w = a + b
            out[w] = out.get(w, F(0)) + c * d
    return {w: v for w, v in out.items() if v != 0}


def poly_add(p, q, c=F(1)):
    out = dict(p)
    for w, v in q.items():
        out[w] = out.get(w, F(0)) + c * v
    return {w: v for w, v in out.items() if v != 0}


def regular_rep(n, rels, D):
    """Left regular representation of the presented algebra on its normal words
    (valid when the truncation closes; the caller re-verifies laws, family and dimension)."""
    T = TruncIdeal(n, rels, D)
    if T.contradiction:
        return None, None
    k = None
    for L in range(0, D + 1):
        if all(w in T.piv for w in itertools.product(range(n), repeat=L)):
            k = L
            break
    if k is None:
        return None, None
    normal = [w for L in range(k) for w in itertools.product(range(n), repeat=L) if w not in T.piv]
    idx = {w: i for i, w in enumerate(normal)}
    m = len(normal)
    mats = []
    for g in range(n):
        M = [[F(0)] * m for _ in range(m)]
        for j, w in enumerate(normal):
            red = T.reduce({(g,) + w: F(1)})
            for w2, c in red.items():
                M[idx[w2]][j] = c
        mats.append(M)
    return mats, normal
