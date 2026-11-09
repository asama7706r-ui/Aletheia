"""Turn GDZ full-text page files (<p><span>word</span>...</p>) into plain text, one block per page.
Usage: python -I gdz_to_text.py PAGES_DIR OUT.txt"""
import html
import os
import re
import sys

pages_dir, out = sys.argv[1], sys.argv[2]
parts = []
for name in sorted(os.listdir(pages_dir)):
    raw = open(os.path.join(pages_dir, name), encoding="utf-8", errors="replace").read()
    lines = []
    for p in re.findall(r"<p[^>]*>(.*?)</p>", raw, flags=re.S):
        words = re.findall(r"<span[^>]*>(.*?)</span>", p, flags=re.S)
        line = " ".join(html.unescape(w).strip() for w in words if w.strip())
        if line:
            lines.append(line)
    parts.append(f"=== file {name} ===\n" + "\n".join(lines))
with open(out, "w", encoding="utf-8", newline="\n") as fh:
    fh.write("\n\n".join(parts) + "\n")
print("pages:", len(parts), "chars:", sum(len(p) for p in parts))
