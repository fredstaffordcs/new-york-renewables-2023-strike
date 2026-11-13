#!/usr/bin/env python3
"""Recompute the headline numbers quoted in README.md from data/derived/roster_117.csv.

    python3 scripts/verify_headline_numbers.py data/derived/roster_117.csv

Exits non-zero if any number differs from the published value. Standard library only.
"""
import csv
import statistics
import sys
from collections import Counter

EXPECTED_FATES = {
    "Re-bid into RESRFP23-1 (2023)": 20,
    "Re-bid into RESRFP24-1 (2024)": 18,
    "Re-bid into RESRFP25-1 (2025) and won": 6,
    "Re-bid into RESRFP25-1 (2025), not awarded": 2,
    "Built on original contract": 6,
    "Abandoned (cancelled, never re-bid)": 34,
}


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def main(path):
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    r86 = [r for r in rows if r["in_petition_86"] == "Yes"]
    ok = True

    def check(label, got, want, tol=0):
        nonlocal ok
        good = abs(got - want) <= tol
        ok &= good
        print(f"{'OK  ' if good else 'FAIL'} {label}: {got:g} (expected {want:g})")

    check("roster rows", len(rows), 117)
    check("petition projects", len(r86), 86)
    fates = Counter(r["fate"] for r in r86)
    for k, v in EXPECTED_FATES.items():
        check(f"fate: {k}", fates.get(k, 0), v)
    check("re-bid total", sum(v for k, v in fates.items() if k.startswith("Re-bid")), 46)
    check("total MW of the 86", sum(num(r["mw"]) for r in r86), 7535.99, 0.01)
    check("built MW", sum(num(r["mw"]) for r in r86 if r["fate"] == "Built on original contract"), 377, 5)
    check("abandoned MW", sum(num(r["mw"]) for r in r86 if r["fate"].startswith("Abandoned")), 2405, 5)

    steps = []
    for r in r86:
        a, b = num(r["orig_rec_usd_mwh"]), num(r["rebid_rec_usd_mwh"])
        if a and b:
            steps.append((b / a - 1, num(r["mw"]), a, b))
    check("comparable strike pairs", len(steps), 18)
    if steps:
        check("median step-up (%)", round(100 * statistics.median(s[0] for s in steps)), 50, 1)
        check("mean step-up (%)", round(100 * statistics.mean(s[0] for s in steps)), 47, 1)
        w = sum(s[1] for s in steps)
        check("MW-weighted step-up (%)", round(100 * sum(s[0] * s[1] for s in steps) / w), 47, 1)
        check("min step-up (%)", round(100 * min(s[0] for s in steps)), 20, 1)
        check("max step-up (%)", round(100 * max(s[0] for s in steps)), 64, 1)

    st = Counter(r["contract_status_2026_09_30"] for r in r86)
    print("contract status 9/30/2026 (86):", dict(st))
    return 0 if ok else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
