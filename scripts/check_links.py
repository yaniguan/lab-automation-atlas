"""Print the HTTP status of every link in README.md."""
import re
import sys
import urllib.request

urls = sorted(set(re.findall(r"\]\((https?://[^)]+)\)", open("README.md").read())))
bad = 0
for url in urls:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        code = urllib.request.urlopen(req, timeout=20).status
    except Exception as exc:  # noqa: BLE001
        code = getattr(exc, "code", str(exc))
    ok = code == 200 or code == 403  # some vendor sites block scripts
    bad += not ok
    print(code, url)
print(f"{len(urls)} links, {bad} not reachable")
sys.exit(0)
