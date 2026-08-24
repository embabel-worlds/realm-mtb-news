#!/usr/bin/env python3
"""Run every view in this realm against a live host and require rows.

The declarative half of a realm has no unit tests. Producers, virtual joins and views are only
exercised by a running host against the real source, and the normal failure — YAML that parses,
types that load, and every query silently returning nothing — looks exactly like "the source has
no data". So: call the host's own endpoints, never re-implement them, and fail on zero rows.

    python3 scripts/test-views.py [PORT] [--token TOKEN]

PORT defaults to 11043. The token defaults to $EMBABEL_TOKEN.
"""
import json
import os
import sys
import urllib.error
import urllib.request

REALM = "mtb-news"

# One case per view, with real params. A view with no case is untested.
CASES = [
    ("mtb-news",           {"topic": "enduro", "limit": 10}),
    ("mtb-news",           {"topic": "mountain biking", "limit": 10}),
    ("mtb-news-by-source", {"topic": "enduro"}),
    ("mtb-news-from-site", {"topic": "enduro", "site": "pinkbike", "limit": 10}),
    ("mtb-news-from-site", {"topic": "trail", "site": "singletracks", "limit": 10}),
    # mtb-tracked-topics reads stored nodes; it is allowed to be empty on a fresh install, so it
    # is checked for a clean run rather than for rows. See ALLOW_EMPTY.
    ("mtb-tracked-topics", {}),
]
ALLOW_EMPTY = {"mtb-tracked-topics"}


def post(base, path, token, payload):
    req = urllib.request.Request(
        base + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    port = args[0] if args else "11043"
    token = os.environ.get("EMBABEL_TOKEN", "")
    if "--token" in sys.argv:
        token = sys.argv[sys.argv.index("--token") + 1]
    if not token:
        sys.exit("no token: set EMBABEL_TOKEN or pass --token")

    base = f"http://localhost:{port}"
    failures = []
    for name, params in CASES:
        label = f"{name}({', '.join(f'{k}={v}' for k, v in params.items()) or 'defaults'})"
        try:
            res = post(base, f"/api/v1/admin/kg/views/{name}/run", token, {"args": params})
        except urllib.error.HTTPError as e:
            failures.append(f"{label}: HTTP {e.code} {e.read()[:200].decode(errors='replace')}")
            print(f"FAIL {label} — HTTP {e.code}")
            continue
        rows = res.get("rows", [])
        warnings = res.get("warnings", []) or []
        # A warning is the host saying the answer is not what it appears to be. Report it even on
        # a run that returned rows — a partial sweep that reads as complete is the failure mode
        # this harness exists to catch.
        for w in warnings:
            print(f"  warn {label}: {w}")
        if not rows and name not in ALLOW_EMPTY:
            failures.append(f"{label}: 0 rows" + (f" with warnings {warnings}" if warnings else " and NO warning"))
            print(f"FAIL {label} — 0 rows")
        else:
            print(f"ok   {label} — {len(rows)} row(s)")

    print()
    if failures:
        print(f"{len(failures)} failure(s) in {REALM}:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    print(f"all {len(CASES)} case(s) passed")


if __name__ == "__main__":
    main()
