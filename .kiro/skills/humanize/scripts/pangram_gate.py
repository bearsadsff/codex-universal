#!/usr/bin/env python3
"""
pangram_gate - submit text to the Pangram detector and enforce a human floor.

Complements scripts/slopcheck.py. slopcheck measures known patterns offline and
owns the target bands; this asks an external classifier and gates on its answer.
Neither one certifies the other.

Requires an API key. Get one at https://www.pangram.com (free research credits
are available for non-commercial work), then:

    export PANGRAM_API_KEY=...
    pip install pangram-sdk

Usage:
    python3 pangram_gate.py draft.md
    python3 pangram_gate.py draft.md --threshold 0.95
    cat draft.md | python3 pangram_gate.py
    python3 pangram_gate.py a.md b.md --json

Gate: passes when fraction_human >= threshold (default 0.90) for every input.

Exit codes: 0 = every input passed, 1 = at least one below the floor,
3 = usage error, 4 = missing or rejected API key, 5 = SDK not installed.

Response fields used, per pangram-sdk 0.1.11 PangramText.predict():
    fraction_human       0.0-1.0 share of text classified human-written
    fraction_ai          0.0-1.0 share classified AI-written
    fraction_ai_assisted 0.0-1.0 share classified AI-assisted
    prediction_short     "AI" | "AI-Assisted" | "Human" | "Mixed"
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

DEFAULT_THRESHOLD = 0.90
MIN_WORDS = 50


def words(text: str) -> int:
    return len(re.findall(r"[A-Za-z][A-Za-z'\u2019-]*", text))


def strip_markup(text: str) -> str:
    """Drop fenced code and inline code so the classifier sees prose."""
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"`[^`\n]*`", " ", text)
    text = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.S)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def load_client():
    try:
        from pangram import PangramText
    except ImportError:
        print("pangram-sdk is not installed. Run: pip install pangram-sdk",
              file=sys.stderr)
        sys.exit(5)
    if not os.getenv("PANGRAM_API_KEY"):
        print("PANGRAM_API_KEY is not set. Export it and retry.",
              file=sys.stderr)
        sys.exit(4)
    try:
        return PangramText()
    except ValueError as exc:
        print(f"{exc}", file=sys.stderr)
        sys.exit(4)


def check(client, label: str, raw: str, threshold: float) -> dict:
    prose = strip_markup(raw)
    n = words(prose)
    if n < MIN_WORDS:
        return {"label": label, "skipped": True, "words": n,
                "reason": f"under {MIN_WORDS} words; too short to classify"}
    try:
        res = client.predict(prose)
    except ValueError as exc:
        msg = str(exc)
        if "Invalid API key" in msg or "401" in msg:
            print(f"API rejected the key: {msg}", file=sys.stderr)
            sys.exit(4)
        return {"label": label, "error": msg, "words": n}

    human = res.get("fraction_human")
    if human is None:                      # short endpoint shape fallback
        likelihood = res.get("ai_likelihood")
        human = None if likelihood is None else 1.0 - float(likelihood)

    return {
        "label": label,
        "words": n,
        "fraction_human": human,
        "fraction_ai": res.get("fraction_ai"),
        "fraction_ai_assisted": res.get("fraction_ai_assisted"),
        "prediction": res.get("prediction_short") or res.get("prediction"),
        "threshold": threshold,
        "passed": (human is not None and human >= threshold),
    }


def render(r: dict) -> None:
    if r.get("skipped"):
        print(f"  SKIP  {r['label']}  ({r['reason']})")
        return
    if r.get("error"):
        print(f"  ERROR {r['label']}  {r['error']}")
        return
    human = r["fraction_human"]
    verdict = "PASS" if r["passed"] else "FAIL"
    pct = "n/a" if human is None else f"{human:.1%}"
    print(f"  {verdict}  {r['label']}")
    print(f"        human {pct} (floor {r['threshold']:.0%})"
          f"  ai {_pct(r.get('fraction_ai'))}"
          f"  ai-assisted {_pct(r.get('fraction_ai_assisted'))}")
    print(f"        prediction: {r.get('prediction')}   words: {r['words']}")


def _pct(v) -> str:
    return "n/a" if v is None else f"{float(v):.1%}"


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Gate text on Pangram's human fraction.")
    ap.add_argument("paths", nargs="*", help="files to check; omit for stdin")
    ap.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD,
                    help=f"human floor, 0-1 (default {DEFAULT_THRESHOLD})")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()

    if not 0.0 <= args.threshold <= 1.0:
        print("--threshold must be between 0 and 1", file=sys.stderr)
        return 3

    docs: list[tuple[str, str]] = []
    if args.paths:
        for p in args.paths:
            try:
                with open(p, encoding="utf-8") as fh:
                    docs.append((p, fh.read()))
            except OSError as exc:
                print(f"cannot read {p}: {exc}", file=sys.stderr)
                return 3
    else:
        data = sys.stdin.read()
        if not data.strip():
            print("no input", file=sys.stderr)
            return 3
        docs.append(("<stdin>", data))

    client = load_client()
    results = [check(client, label, raw, args.threshold) for label, raw in docs]

    if args.as_json:
        print(json.dumps(results, indent=2))
    else:
        print(f"pangram gate  (floor: human >= {args.threshold:.0%})")
        for r in results:
            render(r)

    scored = [r for r in results if "passed" in r]
    if not scored:
        return 3
    return 0 if all(r["passed"] for r in scored) else 1


if __name__ == "__main__":
    sys.exit(main())
