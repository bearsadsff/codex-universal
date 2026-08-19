#!/usr/bin/env python3
"""Compare slopcheck output across the matched-provenance fixtures.

Usage: python3 tests/compare.py   (run from the skill root)
"""
import json
import subprocess
import sys

ORDER = [("tests/human.md", "HUMAN"),
         ("tests/ai-and-human.md", "AI+HUMAN"),
         ("tests/ai.md", "AI")]

out = subprocess.run(
    [sys.executable, "scripts/slopcheck.py"] + [p for p, _ in ORDER] + ["--json"],
    capture_output=True, text=True)
data = json.loads(out.stdout)

print(f"{'variant':<10}{'score':>8}{'words':>7}   verdict")
print("-" * 66)
for path, label in ORDER:
    v = data[path]
    print(f"{label:<10}{v['score']:>8}{v['words']:>7}   {v['verdict']}")

scores = [data[p]["score"] for p, _ in ORDER]
ranked = scores[0] <= scores[1] <= scores[2]
print(f"\nranking human <= hybrid <= ai : {'CORRECT' if ranked else 'WRONG'}"
      f"  ({scores[0]} <= {scores[1]} <= {scores[2]})")
print(f"human-to-ai separation        : {scores[2] - scores[0]:.1f} points\n")

names = [c["name"] for c in data[ORDER[0][0]]["checks"]]
print(f"{'check':<36}{'HUMAN':>8}{'AI+HUM':>8}{'AI':>8}  discriminates")
print("-" * 76)
rows = []
for n in names:
    vals = []
    for path, _ in ORDER:
        c = next(x for x in data[path]["checks"] if x["name"] == n)
        vals.append(c["value"])
    rows.append((n, vals))
rows.sort(key=lambda r: -(r[1][2] - r[1][0]))
for n, vals in rows:
    delta = vals[2] - vals[0]
    if delta > 0:
        verdict = f"yes  (+{delta:.2f} toward AI)"
    elif delta < 0:
        verdict = f"INVERTED ({delta:.2f})"
    else:
        verdict = "flat"
    print(f"{n:<36}{vals[0]:>8}{vals[1]:>8}{vals[2]:>8}  {verdict}")
