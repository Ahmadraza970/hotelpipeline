import json, urllib.request, urllib.error

BASE = "http://127.0.0.1:8000"

def get(path):
    with urllib.request.urlopen(BASE + path, timeout=60) as r:
        return r.status, json.loads(r.read().decode())

def post(path, payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(BASE + path, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

# 1) health
s, b = get("/health")
print("[1] health:", s, b)
assert s == 200 and b["ok"] is True

# 2) scan (lint-only, no LLM key) -> expect findings
snippet = "import os\n\ndef add(a, b):\n    return a + b\n\nprint(missing_var)\n"
s, b = post("/scan", {"files": {"add.py": snippet}})
print("[2] scan:", s, "total=", b["summary"]["total"])
assert s == 200 and b["summary"]["total"] >= 1
project_id = b["project_id"]

# 3) fix without LLM key -> graceful 503
bug_id = b["bugs"][0]["id"]
s, body = post("/fix", {"project_id": project_id, "bug_id": bug_id})
print("[3] fix (no key):", s, "(expect 503)")
assert s == 503, f"expected 503 without LLM key, got {s}"

# 4) export empty patch set -> 200 with empty patch
s, b = post("/export", {"project_id": project_id})
print("[4] export (empty):", s, "bytes=", b["bytes"])
assert s == 200 and b["bytes"] == 0

print("SMOKE OK: health/scan(503-fix)/export all behave correctly")
