#!/usr/bin/env python3
"""Run every view in this realm against a live host and require rows.

The declarative half of a realm has no unit tests. Producers, virtual joins and views are only
exercised by a running host against the real source, and the normal failure — YAML that parses,
types that load, and every query silently returning nothing — looks exactly like "the source has
no data". So: call the host's own endpoints, never re-implement them, and fail on zero rows.

    python3 scripts/test-views.py [PORT] [--token TOKEN]

PORT defaults to 11043. The token defaults to $EMBABEL_TOKEN.

NOT YET RUN GREEN ON A LIVE HOST. The /api/v1/admin endpoints want the appliance's ADMIN
credentials — the ones the setup wizard prints — and an MCP session bearer is rejected with a
401, so this script has never completed a pass here. Every case below was instead verified
one at a time through the MCP `view_run` tool, which runs the same engine, and every one
returned rows. Treat the script as unproven plumbing around proven cases: the first person
with the admin credentials should run it, and fix it rather than trusting it.
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
    ("mtb-web",            {"topic": "enduro", "limit": 10}),
    ("mtb-pinkbike",       {"topic": "enduro", "limit": 10}),
    ("mtb-singletracks",   {"topic": "trail", "limit": 10}),
    ("mtb-vitalmtb",       {"topic": "downhill", "limit": 10}),
    ("mtb-bikeradar",      {"topic": "mountain bike", "limit": 10}),
    ("mtb-reddit",         {"topic": "brakes", "limit": 10}),
    # mtb-tracked-topics reads stored nodes; it is allowed to be empty on a fresh install, so it
    # is checked for a clean run rather than for rows. See ALLOW_EMPTY.
    ("mtb-tracked-topics", {}),
]
ALLOW_EMPTY = {"mtb-tracked-topics"}


# A figure the engine marks short is not the realm's figure, and a battery that counts it reports
# drift that is the source's. short(d) reads an answer's own error, reason, warnings and outcome and
# is None when the answer is whole, else the line that stands in for the figure: "REFUSED: <why>"
# or "PARTIAL <n>: <the engine's reason>". It reads both wires: a query answer (`rows`, `warnings`
# as strings opening with the engine's code) and a view envelope (`status`, `outcome`, `warnings`
# as {code, message}).
# Raw warning codes that mean rows or values may be missing (the engine's incompleteness kinds).
# Cost notes (FILTERED_IN_GRAPH, AGGREGATE_NOT_PUSHED, EMPTY_NOT_KEPT, PUSHDOWN_VALUE_UNMATCHED),
# FILTER_STARVED (an honest empty), STALE_COPY, FIELDS_WITHHELD and UNKNOWN_VIA leave every row in place.
SHORT_CODES = (
    "PARTIAL_RESULT", "PRODUCER_ERROR", "NEEDS_FILTER", "NEEDS_PRODUCER", "FILTER_REJECTED",
    "UNPUSHED_FILTER", "AMBIGUOUS_LABEL", "INCOMPLETE_TRAVERSAL", "INCOMPLETE_RANKING",
    "INCOMPLETE_AGGREGATE", "INCOMPLETE_INPUT", "MATERIALIZATION_FAILED", "REDUCTION_FAILED",
    "UNPARSEABLE_ANSWER", "TERMS_UNAVAILABLE", "COMPUTE_FAILED", "PROPERTY_NOT_STORED",
    "FOLLOW_CAPPED", "UNLINKED_CHILDREN", "RESOLUTION_DROPPED", "AGENTIC_DEGRADED",
    "SOURCE_UNANSWERED",
)
# The typed `reason` a query result carries when it is not a clean answer and not an honest empty.
SHORT_REASONS = ("UNBOUNDED", "PARTIAL_NOT_MATCHED", "UNPUSHED_FILTER", "DISCONNECTED",
                 "INTERNAL_ERROR", "WRITE_IN_PROGRESS", "KILLED", "TOO_EXPENSIVE")
# Public warning codes on a view envelope that mean the same.
SHORT_PUBLIC = ("PARTIAL", "REDUCTION_FAILED", "COMPUTE_FAILED", "PROPERTY_NOT_STORED",
                "AGENTIC_DEGRADED", "RATE_LIMITED", "SOURCE_UNAVAILABLE", "SOURCE_REJECTED",
                "INVALID_FILTER", "UNPUSHED_FILTER", "TOO_BROAD", "FETCH_CAPPED",
                "INDEX_UNAVAILABLE", "ARGUMENT_REFUSED")


def short(d, figure=None):
    tag = "PARTIAL" if figure is None else "PARTIAL %s" % (figure,)
    if not isinstance(d, dict):
        return "REFUSED: not an engine answer: " + str(d)[:160]
    if "outcome" in d or "status" in d:  # a view envelope
        err = d.get("error") or {}
        if d.get("status") != "SUCCEEDED":
            return "REFUSED: %s %s" % (d.get("status"), (err.get("code", "") + " " + err.get("message", "")).strip()[:160] if isinstance(err, dict) else str(err)[:160])
        ws = [w for w in d.get("warnings") or [] if isinstance(w, dict) and w.get("code") in SHORT_PUBLIC]
        if d.get("outcome") not in ("OK", "EMPTY") or ws:
            why = ws[0]["code"] + ": " + ws[0].get("message", "") if ws else "outcome " + str(d.get("outcome"))
            return "%s: %s" % (tag, why[:200])
        return None
    if d.get("error"):
        return "REFUSED: " + str(d["error"])[:160]
    if d.get("run"):
        return "%s: the run had not finished (%s)" % (tag, d["run"])
    ws = [w for w in d.get("warnings") or [] if isinstance(w, str) and w.split(":", 1)[0].strip() in SHORT_CODES]
    if ws:
        return "%s: %s" % (tag, ws[0][:200])
    if d.get("reason") in SHORT_REASONS:
        return "%s: reason %s" % (tag, d["reason"])
    return None


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
        s = short(res, len(rows))
        if s:
            # Rows and a warning that says some are missing: reported above, and failed here.
            failures.append(f"{label}: {s}")
            print(f"FAIL {label} — {s}")
        elif not rows and name not in ALLOW_EMPTY:
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
