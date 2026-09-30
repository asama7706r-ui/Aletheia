# Calculator check for ladder step 3 (Grassmann, two generators). Scratch only, not project code.
import sympy as sp

def mono_mul(m1, m2):
    """Wedge product of two basis monomials (tuples of generator indices). Returns (sign, monomial) or (0, None)."""
    seq = list(m1) + list(m2)
    if len(set(seq)) < len(seq):
        return 0, None                      # repeated generator -> zero (theta_i^2 = 0)
    sign = 1
    arr = seq[:]
    for i in range(len(arr)):               # bubble sort, count swaps
        for j in range(len(arr) - 1 - i):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                sign = -sign
    return sign, tuple(arr)

class G:
    def __init__(self, d): self.d = {k: sp.expand(v) for k, v in d.items() if sp.expand(v) != 0}
    def __add__(s, o): o = o if isinstance(o, G) else G({(): o}); r = dict(s.d); [r.__setitem__(k, r.get(k, 0) + v) for k, v in o.d.items()]; return G(r)
    def __neg__(s): return G({k: -v for k, v in s.d.items()})
    def __sub__(s, o): return s + (-(o if isinstance(o, G) else G({(): o})))
    def __mul__(s, o):
        o = o if isinstance(o, G) else G({(): o}); r = {}
        for k1, v1 in s.d.items():
            for k2, v2 in o.d.items():
                sg, m = mono_mul(k1, k2)
                if sg: r[m] = r.get(m, 0) + sg * v1 * v2
        return G(r)
    __rmul__ = lambda s, o: G({(): o}) * s
    def is_zero(s): return len(s.d) == 0
    def __repr__(s): return ' + '.join(f'({v})*{"th"+"".join(map(str,k)) if k else "1"}' for k, v in sorted(s.d.items())) or '0'

one = G({(): 1}); t1 = G({(1,): 1}); t2 = G({(2,): 1})
a, b, c, d, p, q, r, s = sp.symbols('a b c d p q r s')
print('th1*th2 + th2*th1 = 0 :', (t1*t2 + t2*t1).is_zero())
print('th1^2, th2^2          :', t1*t1, '|', t2*t2)
o = b*t1 + c*t2
print('general odd o^2       :', o*o)
print('(a th1+b th2)(c th1+d th2) =', (a*t1 + b*t2)*(c*t1 + d*t2))
z = a*one + b*t1 + c*t2 + d*(t1*t2)
w = p*one + q*t1 + r*t2 + s*(t1*t2)
n = z - a*one
print('nilpotent part n^2    :', n*n)
conj = lambda x: G({k: (v if len(k) == 0 else -v) for k, v in x.d.items()})   # a - n
grade = lambda x: G({k: (v if len(k) % 2 == 0 else -v) for k, v in x.d.items()})  # theta -> -theta
print('z*conj(z)             :', z*conj(z))
print('conj anti-automorphism conj(zw) == conj(w)conj(z):', (conj(z*w) - conj(w)*conj(z)).is_zero())
print('conj is NOT automorphism (conj(zw) == conj(z)conj(w))?:', (conj(z*w) - conj(z)*conj(w)).is_zero())
print('grade involution is automorphism:', (grade(z*w) - grade(z)*grade(w)).is_zero(), '| z*grade(z) =', z*grade(z))
Nz = (z*conj(z)).d.get((), 0); Nw = (w*conj(w)).d.get((), 0)
print('N multiplicative      :', sp.simplify(((z*w)*conj(z*w)).d.get((), 0) - Nz*Nw) == 0)
inv = conj(z) * (1/a**2)
print('z * conj(z)/a^2 == 1  :', (z*inv - one).is_zero())
print('even th1th2 commutes with z:', ((t1*t2)*z - z*(t1*t2)).is_zero())
