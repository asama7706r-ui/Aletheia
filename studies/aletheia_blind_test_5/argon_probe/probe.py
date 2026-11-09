"""Environment probe for the test-5 world generator (run once, before any real task).

It checks only what the real task will need:
  1. the Python version and the standard-library modules we use;
  2. whether an uploaded file can be opened from code, and where;
  3. exact SHA-256 hashing of that file (the result must match the value the
     project computed locally, which proves the file was really read);
  4. roughly how long a fixed amount of exact-fraction arithmetic takes.
It writes nothing and needs no network. Standard library only.
"""
import glob
import hashlib
import json
import os
import platform
import sys
import time
from fractions import Fraction
from itertools import product

print("python:", sys.version.split()[0], "|", platform.system(), platform.machine())
print("modules: hashlib, json, fractions, itertools imported OK")
print("cwd:", os.getcwd())

# 2-3. find the uploaded input file
candidates = ["probe_input.txt", "/mnt/data/probe_input.txt", "/content/probe_input.txt"]
candidates += glob.glob("**/probe_input.txt", recursive=True)
found = None
for path in candidates:
    if os.path.isfile(path):
        found = path
        break
if found is None:
    print("probe_input.txt: NOT FOUND. Files visible from here:")
    for root, _dirs, files in os.walk("."):
        for name in files[:50]:
            print("   ", os.path.join(root, name))
else:
    data = open(found, "rb").read()
    print("probe_input.txt found at:", found)
    print("bytes:", len(data), "| sha256:", hashlib.sha256(data).hexdigest())

# 4. timing: exact fraction arithmetic (the same 4x4 product, repeated;
#    the inputs stay fixed, so the numbers do not grow)
a = [[Fraction(i - j, i + j + 1) for j in range(4)] for i in range(4)]
b = [[Fraction(i + 2 * j + 1, 7) for j in range(4)] for i in range(4)]
start = time.time()
for _ in range(2000):
    c = [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]
elapsed = time.time() - start
print("timing: 2000 exact 4x4 products in %.2f s (c[0][0] = %s)" % (elapsed, c[0][0]))

# a small combinatorial loop, like a brute-force check over tiny structures
start = time.time()
count = sum(1 for t in product(range(3), repeat=9) if (t[0] + t[4] + t[8]) % 3 == 0)
print("timing: 3^9 loop in %.2f s (count %d)" % (time.time() - start, count))

print(json.dumps({"probe": "OK"}))
