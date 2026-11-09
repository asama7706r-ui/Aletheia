"""Fetch English Wikipedia articles as raw wikitext at their current revision, following redirects.
Writes <out>/<slug>.json (the API answer) and <out>/<slug>_wikitext.txt, and prints title, revision id,
timestamp and SHA-256. Standard library only. The request carries no personal data."""
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

UA = "AletheiaResearch/0.1 (history test; no contact data)"


def fetch(title, out):
    q = urllib.parse.urlencode({"action": "query", "prop": "revisions", "titles": title, "redirects": 1,
                                "rvprop": "ids|timestamp|content", "rvslots": "main",
                                "format": "json", "formatversion": 2})
    req = urllib.request.Request("https://en.wikipedia.org/w/api.php?" + q, headers={"User-Agent": UA})
    for wait in (0, 20, 60, 120):       # polite backoff on HTTP 429
        time.sleep(wait)
        try:
            data = json.load(urllib.request.urlopen(req, timeout=60))
            break
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
    else:
        print(f"GAVE UP (429)  {title}")
        return
    page = data["query"]["pages"][0]
    if "missing" in page:
        print(f"MISSING  {title}")
        return
    rev = page["revisions"][0]
    slug = page["title"].replace(" ", "_").replace("/", "_")
    with open(os.path.join(out, slug + ".json"), "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False)
    text = rev["slots"]["main"]["content"]
    path = os.path.join(out, slug + "_wikitext.txt")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
    redirected = data["query"].get("redirects", [])
    via = f" (redirect from {redirected[0]['from']})" if redirected else ""
    print(f"{page['title']}{via} | rev {rev['revid']} | {rev['timestamp']} | {len(text)} chars | sha256 {sha}")


if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    for t in sys.argv[2:]:
        fetch(t, out)
        time.sleep(5)
