import time
from fractions import Fraction as F
from wcore import *
from wideal import *
from wrat import *
w = {"generators":[{"name":"a","grade":0}],"variables":["t","x"],"laws":["(t + a*x)*(t - a*x) = t**2 + 3*x**2"]}
print("rels", relations(w))
q = {"generators":[{"name":"i","grade":0},{"name":"j","grade":0}],"laws":["i*i = -1","j*j = -1","i*j = -j*i"]}
R = relations(q)
for D in (3,4,5):
    T = TruncIdeal(2, R, D); print("quat assoc D",D,"ub",T.dim_upper_bound(),"contr",T.contradiction)
T = TruncIdeal(2, R + family_relations([0,0],"comm"), 4); print("quat comm contr", T.contradiction)
x = {"generators":[{"name":"p","grade":1},{"name":"q","grade":1},{"name":"r","grade":1}],"variables":["s","t","u"],"laws":["(s*p + t*q + u*r)**2 = 0"]}
R = relations(x); print("ext rels", len(R))
T = TruncIdeal(3, R, 4); print("ext3 assoc ub", T.dim_upper_bound())
T = TruncIdeal(3, R + family_relations([1,1,1],"comm"), 4); print("ext3 comm ub", T.dim_upper_bound(), "pq in ideal", T.contains({(0,1):F(1)}))
x4 = {"generators":[{"name":n,"grade":1} for n in ["p","q","r","v"]],"variables":["s","t","u","k"],"laws":["(s*p + t*q + u*r + k*v)**2 = 0"]}
R = relations(x4)
for D in (5,6):
    t0=time.time(); T = TruncIdeal(4, R, D); print("ext4 D",D,"ub",T.dim_upper_bound(),"rows",T.rows_used,"piv",len(T.piv),"sec",round(time.time()-t0,2))
print("pow test", expr_poly(q, "(i*j)**2 - (i + j)**2"))
print("ratpts", rational_points(relations({"generators":[{"name":"a","grade":0},{"name":"b","grade":0}],"laws":["a*a + b*b = 13","a*b = 6"]}),2))
