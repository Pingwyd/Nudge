"""Test update check with certifi SSL context."""
import ssl
try:
    import certifi
    ctx = ssl.create_default_context(cafile=certifi.where())
    print(f"Using certifi CA: {certifi.where()}")
except Exception:
    ctx = ssl.create_default_context()
    print("Using system default SSL context")

from urllib.request import urlopen, Request
url = "https://api.github.com/repos/Pingwyd/Nudge/releases/latest"
try:
    req = Request(url, headers={"Accept": "application/json", "User-Agent": "Nudge/1.0"})
    with urlopen(req, timeout=10, context=ctx) as resp:
        data = __import__("json").loads(resp.read().decode("utf-8"))
        print(f"tag: {data.get('tag_name')}")
        print("STATUS: OK")
except Exception as e:
    print(f"FAILED: {type(e).__name__}: {e}")
