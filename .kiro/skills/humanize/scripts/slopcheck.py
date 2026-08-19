#!/usr/bin/env python3
"""
slopcheck - deterministic linter for AI-writing patterns.

Measures the tells that are measurable, so the agent's judgment can be spent
on the ones that are not (depth, argument, voice).

Bands are tagged with provenance:
  [P] derived from Rosmine, "Fixing LLM writing with Distribution Fine Tuning"
      (rosmine.ai, 18 May 2026)
  [E] calibrated estimate for general English prose; tune to your corpus

Usage:
    python3 slopcheck.py draft.md
    cat draft.md | python3 slopcheck.py
    python3 slopcheck.py draft.md --verbose      # show every match + line no.
    python3 slopcheck.py draft.md --json         # machine-readable
    python3 slopcheck.py a.md b.md --json        # batch

Exit codes: 0 = clean/low risk, 1 = elevated, 2 = high risk, 3 = usage error.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
import unicodedata
from dataclasses import dataclass, field, asdict
from typing import Iterable

# ---------------------------------------------------------------------------
# Pattern data
# ---------------------------------------------------------------------------

# Grammatical filler n-grams. Counts are occurrences across the source paper's
# SFT-vs-DFT output comparison; the ratio is the overuse signal. [P]
# NOTE "one of the" is included as INFORMATIONAL ONLY: 430 vs 408 is ~1.05x,
# i.e. it is NOT a discriminating signal. Kept to prevent it being added later.
FILLER_NGRAMS = {
    "be used to": 11.3,
    "can be used": 7.2,
    "it is a": 12.4,
    "the number of": 3.7,
}
NON_SIGNAL_NGRAMS = {"one of the": 1.05}

# Vocabulary overused by frontier models relative to human text. Values are
# relative-frequency multipliers vs human writing. [P]
MEASURED_VOCAB = {
    "corridors": 45.2,
    "norms": 43.1,
    "align": 36.0,
    "aligns": 36.0,
    "aligned": 36.0,
    "alignment": 36.0,
    "metrics": 27.2,
    "engagement": 26.5,
    "targeted": 5.1,
    "identity": 5.0,
    "trust": 4.9,
}

# Widely documented LLM vocabulary tells. Not measured in the source paper;
# treat as weaker evidence than MEASURED_VOCAB. [E]
CONVENTIONAL_VOCAB = [
    "delve", "delving", "underscore", "underscores", "underscoring",
    "pivotal", "crucial", "vital", "testament", "tapestry", "realm",
    "landscape", "nuanced", "multifaceted", "holistic", "robust",
    "seamless", "seamlessly", "leverage", "leveraging", "utilize",
    "utilizing", "foster", "fostering", "navigate", "navigating",
    "unlock", "unlocking", "unleash", "elevate", "empower", "embark",
    "myriad", "plethora", "paradigm", "synergy", "cornerstone",
    "beacon", "intricate", "meticulous", "meticulously", "profound",
    "transformative", "groundbreaking", "cutting-edge", "game-changer",
    "ever-evolving", "rapidly-evolving", "cannot be overstated",
    "in today's", "in the realm of", "it's worth noting",
    "it is important to note", "when it comes to", "at the end of the day",
    "the world of", "dive into", "deep dive", "unpack",
]

# Negative parallelism: "it's not X, it's Y" and relatives. [P] named
# explicitly as a slop sign in the source paper.
NEG_PARALLEL = [
    (r"\b(?:it|this|that|he|she|they)\s?(?:'s|s|\sis|\swas|\sare)\s+not\s+"
     r"(?:just|merely|only|simply|about)?[^.!?;]{2,60}?[,;:]\s*"
     r"(?:it|this|that|he|she|they)?\s?(?:'s|s|\sis|\swas|\sare)?\s*",
     "it's not X, it's Y"),
    (r"\bnot\s+(?:just|merely|only|simply)\b[^.!?]{2,70}?\b(?:but|it'?s)\b",
     "not just X but Y"),
    (r"\bisn'?t\s+(?:about|just|simply)\b[^.!?]{2,60}?\bit'?s\b",
     "isn't about X, it's Y"),
    (r"\bless\s+about\b[^.!?]{2,50}?\bmore\s+about\b",
     "less about X, more about Y"),
    (r"\bnot\s+because\b[^.!?]{2,60}?\bbut\s+because\b",
     "not because X but because Y"),
]

# Vague attribution with no named source. [E]
VAGUE_ATTRIB = [
    r"\bexperts?\s+(?:say|agree|believe|argue|note|warn)\b",
    r"\bstudies\s+(?:show|suggest|indicate|have shown)\b",
    r"\bresearch\s+(?:shows|suggests|indicates)\b",
    r"\b(?:many|some|most|critics|observers|analysts|industry leaders)\s+"
    r"(?:say|argue|believe|note|contend|suggest|point out)\b",
    r"\bit\s+is\s+(?:widely|generally|often)\s+(?:believed|accepted|known|held)\b",
    r"\bsome\s+would\s+argue\b",
    r"\bgrowing\s+(?:body of|number of)\b",
]

# Sentence-opener scaffolding. [E]
SCAFFOLD_OPENERS = [
    "moreover", "furthermore", "additionally", "however", "nevertheless",
    "nonetheless", "consequently", "therefore", "thus", "indeed",
    "ultimately", "importantly", "notably", "overall", "in conclusion",
    "in summary", "firstly", "secondly", "lastly", "that said",
]

# Scripts whose presence indicates the high-temperature decode failure the
# source paper documents (human baseline: 0.1% of documents). [P]
FOREIGN_SCRIPT_RANGES = [
    (0x3040, 0x30FF, "Japanese kana"),
    (0x3400, 0x4DBF, "CJK ext A"),
    (0x4E00, 0x9FFF, "CJK"),
    (0xAC00, 0xD7AF, "Hangul"),
    (0x0400, 0x04FF, "Cyrillic"),
    (0x0600, 0x06FF, "Arabic"),
    (0x0590, 0x05FF, "Hebrew"),
    (0x0E00, 0x0E7F, "Thai"),
    (0x1F300, 0x1FAFF, "emoji"),
]

STOP_CAPS = {
    "I", "I'm", "I've", "I'd", "I'll", "A", "An", "The", "And", "But", "Or",
    "If", "It", "In", "On", "At", "To", "So", "As", "Of", "We", "You", "He",
    "She", "They", "This", "That", "These", "Those", "There", "Then", "When",
    "What", "Why", "How", "Who", "Where", "For", "By", "With", "From", "Not",
    "No", "Yes", "Is", "Was", "Are", "Be", "Do", "Did", "Does", "Can", "Will",
    "Would", "Should", "Could", "May", "Might", "Must", "Have", "Has", "Had",
    "One", "Two", "Three", "First", "Second", "Third", "Next", "Now", "Here",
    "Its", "His", "Her", "Their", "Our", "My", "Your", "All", "Some", "Many",
    "Most", "Each", "Every", "Both", "Because", "While", "Although", "After",
    "Before", "Since", "Until", "Unless", "However", "Moreover", "Instead",
}

STATUS_ORDER = ["OK", "LOW-RISK", "FLAT", "ELEVATED", "HIGH"]
STATUS_WEIGHT = {"OK": 0, "LOW-RISK": 1, "FLAT": 2, "ELEVATED": 3, "HIGH": 5}


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass
class Check:
    name: str
    value: float
    display: str
    band: str
    status: str
    provenance: str
    weight: float = 1.0
    note: str = ""
    matches: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# Text preparation
# ---------------------------------------------------------------------------

def strip_markup(text: str) -> str:
    """Remove fenced code, inline code, URLs, and image/link targets."""
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"~~~.*?~~~", " ", text, flags=re.S)
    text = re.sub(r"^(?: {4}|\t).*$", " ", text, flags=re.M)
    text = re.sub(r"`[^`\n]*`", " ", text)
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"<[^>\s]+>", " ", text)
    text = re.sub(r"https?://\S+", " ", text)
    return text


def split_paragraphs(text: str) -> list[str]:
    parts = [p.strip() for p in re.split(r"\n\s*\n", text)]
    return [p for p in parts if p and not re.fullmatch(r"[#>*\-=_\s|]+", p)]


_ABBREV = r"(?<!\bMr)(?<!\bMrs)(?<!\bMs)(?<!\bDr)(?<!\bProf)(?<!\bSt)" \
          r"(?<!\bvs)(?<!\betc)(?<!\be\.g)(?<!\bi\.e)(?<!\bFig)(?<!\bNo)"


def split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text)
    pieces = re.split(_ABBREV + r"(?<=[.!?])[\"')\]]*\s+(?=[A-Z0-9\"'(])", text)
    out = []
    for p in pieces:
        p = p.strip(" \t|#*->_")
        if len(re.findall(r"[A-Za-z]", p)) >= 3:
            out.append(p)
    return out


def words_of(text: str) -> list[str]:
    return re.findall(r"[A-Za-z][A-Za-z'\u2019-]*", text)


def line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


# ---------------------------------------------------------------------------
# Banding helper
# ---------------------------------------------------------------------------

def band_high(value, ok, elevated, band, name, prov, weight=1.0, note="",
              matches=None, fmt="{:.2f}"):
    """Higher value = worse."""
    if value <= ok:
        status = "OK"
    elif value <= elevated:
        status = "ELEVATED"
    else:
        status = "HIGH"
    return Check(name, round(float(value), 4), fmt.format(value), band, status,
                 prov, weight, note, matches or [])


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_emdash(clean, paragraphs, n_words, verbose, raw):
    hits = [m for m in re.finditer(r"\s[\u2014\u2013]\s|\w[\u2014\u2013]\w", clean)]
    per_1k = len(hits) / max(n_words, 1) * 1000
    paras_with = sum(1 for p in paragraphs if re.search(r"[\u2014\u2013]", p))
    pct_paras = paras_with / max(len(paragraphs), 1) * 100
    if pct_paras >= 60 or per_1k >= 6:
        status = "HIGH"
    elif pct_paras >= 35 or per_1k >= 3:
        status = "ELEVATED"
    else:
        status = "OK"
    note = ("Density is the tell, not presence. Em-dashes appear in 18.6% of "
            "human documents, so zero is unremarkable; one per paragraph is not.")
    return Check("em-dash density", round(per_1k, 3),
                 f"{per_1k:.2f}/1k words, in {pct_paras:.0f}% of paragraphs",
                 "<3/1k and <35% of paragraphs [P]", status, "[P]", 1.0, note,
                 [(line_of(raw, m.start()), m.group().strip()) for m in hits]
                 if verbose else [])


def check_sentence_rhythm(sentences):
    lengths = [len(words_of(s)) for s in sentences]
    lengths = [n for n in lengths if n > 0]
    if len(lengths) < 5:
        return [Check("sentence rhythm", 0, "too few sentences to judge",
                      "n/a", "OK", "[E]", 0.0)]
    mean = statistics.mean(lengths)
    sd = statistics.pstdev(lengths)
    cv = sd / mean if mean else 0
    if cv < 0.35:
        status, note = "FLAT", ("Uniform sentence length. This is the "
                                "over-correction signature: prose that has "
                                "been mechanically shortened. Human rhythm is "
                                "bursty - long, long, short.")
    elif cv > 1.10:
        status, note = "ELEVATED", "Erratic length; check for dropped transitions."
    else:
        status, note = "OK", ""
    checks = [Check("sentence-length variation (CV)", round(cv, 3),
                    f"CV {cv:.2f} (mean {mean:.1f}w, sd {sd:.1f})",
                    "0.35-1.10 [E]", status, "[E]", 1.5, note)]
    long_pct = sum(1 for n in lengths if n > 34) / len(lengths) * 100
    short_pct = sum(1 for n in lengths if n <= 8) / len(lengths) * 100
    checks.append(Check("length mix", round(short_pct, 1),
                        f"{short_pct:.0f}% short (<=8w), {long_pct:.0f}% long (>34w)",
                        "some of each [E]",
                        "FLAT" if short_pct == 0 and long_pct == 0 else "OK",
                        "[E]", 0.5,
                        "No short and no long sentences means no rhythm."
                        if short_pct == 0 and long_pct == 0 else ""))
    return checks


def check_token_rates(clean, sentences, n_words):
    lower = [w.lower() for w in words_of(clean)]
    checks = []

    the_rate = lower.count("the") / max(n_words, 1) * 100
    checks.append(band_high(
        the_rate, 7.8, 9.0, "<7.8% of words [E]", "'the' rate", "[P]", 1.0,
        "Source paper measured 'the' at +19% and ' The' at +90% vs human.",
        fmt="{:.2f}%"))

    copula = sum(lower.count(w) for w in ("is", "are", "was", "were"))
    cop_rate = copula / max(n_words, 1) * 100
    checks.append(band_high(
        cop_rate, 3.6, 4.8, "<3.6% of words [E]", "copular verb rate", "[P]",
        1.5, "Measured overuse: ' is' +44%, ' was' +49%, ' are' +31%. "
             "High copula rate means 'X is Y' assertion instead of action.",
        fmt="{:.2f}%"))

    if sentences:
        init_the = sum(1 for s in sentences if re.match(r"^\W*The\b", s))
        pct = init_the / len(sentences) * 100
        checks.append(band_high(
            pct, 14.0, 22.0, "<14% of sentences [E]", "sentences opening 'The'",
            "[P]", 1.5, "' The' was the single most overused token measured "
                        "(+90% vs human).", fmt="{:.1f}%"))

        openers = [(w[0].lower() if (w := words_of(s)) else "") for s in sentences]
        scaffold = sum(1 for o in openers if o in SCAFFOLD_OPENERS)
        pct_s = scaffold / len(sentences) * 100
        checks.append(band_high(
            pct_s, 8.0, 15.0, "<8% of sentences [E]",
            "connective scaffolding openers", "[E]", 1.0,
            "Moreover/Furthermore/Additionally as sentence openers.",
            fmt="{:.1f}%"))
    return checks


def check_anaphora(sentences):
    """Runs of 3+ consecutive sentences starting with the same word."""
    firsts = []
    for s in sentences:
        w = words_of(s)
        firsts.append(w[0].lower() if w else "")
    runs, i = [], 0
    while i < len(firsts):
        j = i
        while j + 1 < len(firsts) and firsts[j + 1] == firsts[i] and firsts[i]:
            j += 1
        if j - i + 1 >= 3:
            runs.append((firsts[i], j - i + 1))
        i = j + 1
    n = len(runs)
    if n >= 4:
        status = "HIGH"
    elif n >= 2:
        status = "ELEVATED"
    else:
        status = "OK"
    note = ("17.4% of human documents contain one such run and inspection "
            "showed those were legitimate (lists, 'The islands...', 'The "
            "largest island...'). One run is human. SFT at T=0.7 hit 53.3%.")
    return Check("anaphora runs (3+ same opener)", n,
                 f"{n} run(s)" + (f": {', '.join(f'{w} x{c}' for w, c in runs)}"
                                  if runs else ""),
                 "0-1 runs [P]", status, "[P]", 1.5, note)


def check_paragraph_openings(paragraphs):
    if len(paragraphs) < 4:
        return Check("paragraph opening diversity", 1.0, "too few paragraphs",
                     "n/a", "OK", "[E]", 0.0)
    keys = []
    for p in paragraphs:
        w = words_of(p)[:2]
        keys.append(" ".join(x.lower() for x in w))
    ratio = len(set(keys)) / len(keys)
    if ratio < 0.6:
        status = "HIGH"
    elif ratio < 0.8:
        status = "ELEVATED"
    else:
        status = "OK"
    return Check("paragraph opening diversity", round(ratio, 3),
                 f"{ratio:.0%} unique first-two-words", ">=80% [E]", status,
                 "[E]", 1.0,
                 "Repeated paragraph openings are the structural form of the "
                 "repetition the source paper measured at sentence level.")


def check_specificity(clean, sentences, n_words):
    """Proxy for the Depth dimension (baseline scored 35.5/100)."""
    numerals = len(re.findall(r"\b\d[\d,.:/%-]*\b", clean))
    proper = 0
    for s in sentences:
        for w in words_of(s)[1:]:
            if w[0].isupper() and w not in STOP_CAPS and len(w) > 1:
                proper += 1
    quotes = len(re.findall(r"[\"\u201c][^\"\u201d]{12,}[\"\u201d]", clean))
    density = (numerals + proper + quotes) / max(n_words, 1) * 100
    if density >= 3.0:
        status = "OK"
    elif density >= 1.5:
        status = "ELEVATED"
    else:
        status = "HIGH"
    return Check("specificity density", round(density, 2),
                 f"{density:.2f}/100 words ({proper} proper nouns, "
                 f"{numerals} numerals, {quotes} quotations)",
                 ">=3.0/100 words [E]", status, "[E]", 2.5,
                 "The largest measured gap was Depth (35.5 -> 87.5) and "
                 "Creativity (32.5 -> 86.0). Low specificity is the primary "
                 "slop cause; surface tokens are secondary.")


def check_filler_ngrams(clean, n_words, verbose, raw):
    hits, detail = 0, []
    for gram, ratio in FILLER_NGRAMS.items():
        found = list(re.finditer(r"\b" + re.escape(gram) + r"\b", clean, re.I))
        if found:
            hits += len(found)
            detail.append(f"'{gram}' x{len(found)} ({ratio:.1f}x overused)")
    per_1k = hits / max(n_words, 1) * 1000
    c = band_high(per_1k, 1.0, 3.0, "<1/1k words [P]",
                  "grammatical filler n-grams", "[P]", 1.5,
                  "; ".join(detail) if detail else
                  "Measured SFT-vs-DFT ratios: 'it is a' 12.4x, 'be used to' "
                  "11.3x, 'can be used' 7.2x, 'the number of' 3.7x.",
                  fmt="{:.2f}/1k")
    return c


def check_vocab(clean, n_words, verbose, raw):
    checks = []
    m_hits, m_detail = 0, []
    for word, mult in MEASURED_VOCAB.items():
        found = list(re.finditer(r"\b" + word + r"\b", clean, re.I))
        if found:
            m_hits += len(found)
            m_detail.append(f"{word} x{len(found)} ({mult:.1f}x)")
    per_1k = m_hits / max(n_words, 1) * 1000
    checks.append(band_high(
        per_1k, 1.0, 2.5, "<1/1k words [P]", "measured-overuse vocabulary",
        "[P]", 1.5, "; ".join(m_detail) if m_detail else
        "Top measured multipliers vs human: corridors 45.2x, norms 43.1x, "
        "align 36.0x, metrics 27.2x, engagement 26.5x.", fmt="{:.2f}/1k"))

    c_hits, c_detail = 0, []
    for term in CONVENTIONAL_VOCAB:
        pat = r"\b" + re.escape(term).replace(r"\ ", r"\s+") + r"\b"
        found = list(re.finditer(pat, clean, re.I))
        if found:
            c_hits += len(found)
            c_detail.append(f"{term} x{len(found)}")
    per_1k_c = c_hits / max(n_words, 1) * 1000
    checks.append(band_high(
        per_1k_c, 1.5, 4.0, "<1.5/1k words [E]", "conventional AI vocabulary",
        "[E]", 1.0, "; ".join(c_detail[:14]) if c_detail else "",
        fmt="{:.2f}/1k"))
    return checks


def check_neg_parallel(clean, n_words, verbose, raw):
    hits, detail = 0, []
    for pat, label in NEG_PARALLEL:
        found = list(re.finditer(pat, clean, re.I))
        if found:
            hits += len(found)
            detail.append(f"{label} x{len(found)}")
    per_1k = hits / max(n_words, 1) * 1000
    return band_high(per_1k, 0.5, 1.5, "<0.5/1k words [P]",
                     "negative parallelism", "[P]", 1.5,
                     "; ".join(detail) if detail else
                     "'it's not X, it's Y' is named explicitly as a slop sign.",
                     fmt="{:.2f}/1k")


def check_rule_of_three(clean, n_words):
    triads = re.findall(r"\b[\w'\u2019-]+,\s+[\w'\u2019-]+,?\s+and\s+"
                        r"[\w'\u2019-]+\b", clean)
    per_1k = len(triads) / max(n_words, 1) * 1000
    return band_high(per_1k, 3.0, 6.0, "<3/1k words [E]",
                     "rule-of-three triads", "[E]", 1.0,
                     f"{len(triads)} triad(s). Check each: if the third item "
                     f"is padding, cut to two." if triads else "",
                     fmt="{:.2f}/1k")


def check_vague_attrib(clean, n_words):
    hits = sum(len(re.findall(p, clean, re.I)) for p in VAGUE_ATTRIB)
    per_1k = hits / max(n_words, 1) * 1000
    return band_high(per_1k, 0.4, 1.2, "<0.4/1k words [E]",
                     "vague attribution", "[E]", 1.5,
                     "'experts say' with no named expert. Replace with a name "
                     "or cut the claim." if hits else "", fmt="{:.2f}/1k")


def check_foreign_chars(clean):
    found = {}
    for ch in clean:
        cp = ord(ch)
        for lo, hi, label in FOREIGN_SCRIPT_RANGES:
            if lo <= cp <= hi:
                found.setdefault(label, []).append(ch)
                break
    total = sum(len(v) for v in found.values())
    status = "OK" if total == 0 else "HIGH"
    detail = "; ".join(f"{k}: {''.join(v[:8])}" for k, v in found.items())
    return Check("foreign-script characters", total,
                 f"{total} char(s)" + (f" - {detail}" if detail else ""),
                 "0 [P]", status, "[P]", 2.0,
                 "Human baseline is 0.1% of documents; SFT at T=1.0 hit 36.5%. "
                 "Any hit means a decode artefact or an unintended paste."
                 if total else "")


def check_hollow_sentences(sentences):
    """Sentences that are pure meta-commentary with no content."""
    pats = [
        r"^\W*(?:in\s+(?:this|the)\s+(?:section|article|post|guide|chapter))",
        r"^\W*(?:let'?s\s+(?:dive|explore|take a look|delve|unpack))",
        r"^\W*(?:it'?s\s+(?:important|worth|essential|crucial)\s+to\s+(?:note|remember|understand))",
        r"^\W*(?:this\s+(?:section|article|post)\s+will)",
        r"^\W*(?:by\s+understanding\b)",
        r"^\W*(?:whether\s+you'?re\s+a\b)",
        r"^\W*(?:in\s+(?:conclusion|summary)|to\s+(?:sum up|wrap up|conclude))",
        r"^\W*(?:in\s+today'?s\s+(?:fast-paced|digital|modern|ever-changing))",
    ]
    hits = [s for s in sentences if any(re.search(p, s, re.I) for p in pats)]
    pct = len(hits) / max(len(sentences), 1) * 100
    return band_high(pct, 1.5, 4.0, "<1.5% of sentences [E]",
                     "hollow / meta sentences", "[E]", 1.5,
                     "; ".join(f'"{s[:64]}..."' for s in hits[:4]) if hits
                     else "", fmt="{:.1f}%")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def analyse(raw: str, verbose: bool = False) -> dict:
    clean = strip_markup(raw)
    paragraphs = split_paragraphs(clean)
    sentences = split_sentences(" ".join(paragraphs))
    n_words = len(words_of(clean))

    if n_words < 40:
        return {"error": f"only {n_words} words; need >=40 for meaningful rates",
                "words": n_words, "checks": [], "score": 0, "verdict": "SKIPPED"}

    checks: list[Check] = [check_emdash(clean, paragraphs, n_words, verbose, raw)]
    checks += check_sentence_rhythm(sentences)
    checks += check_token_rates(clean, sentences, n_words)
    checks.append(check_anaphora(sentences))
    checks.append(check_paragraph_openings(paragraphs))
    checks.append(check_specificity(clean, sentences, n_words))
    checks.append(check_filler_ngrams(clean, n_words, verbose, raw))
    checks += check_vocab(clean, n_words, verbose, raw)
    checks.append(check_neg_parallel(clean, n_words, verbose, raw))
    checks.append(check_rule_of_three(clean, n_words))
    checks.append(check_vague_attrib(clean, n_words))
    checks.append(check_hollow_sentences(sentences))
    checks.append(check_foreign_chars(clean))

    max_pen = sum(c.weight * STATUS_WEIGHT["HIGH"] for c in checks if c.weight)
    pen = sum(c.weight * STATUS_WEIGHT[c.status] for c in checks)
    score = round(pen / max_pen * 100, 1) if max_pen else 0.0

    if score < 12:
        verdict = "LOW AI-PATTERN DENSITY"
    elif score < 28:
        verdict = "MODERATE - targeted fixes needed"
    else:
        verdict = "HIGH - substantive rewrite needed"

    return {
        "words": n_words,
        "sentences": len(sentences),
        "paragraphs": len(paragraphs),
        "score": score,
        "verdict": verdict,
        "checks": [asdict(c) for c in checks],
    }


def render(path: str, res: dict, verbose: bool) -> None:
    print("=" * 78)
    print(f"slopcheck: {path}")
    print("=" * 78)
    if "error" in res:
        print(f"  SKIPPED - {res['error']}")
        return
    print(f"{res['words']} words / {res['sentences']} sentences / "
          f"{res['paragraphs']} paragraphs\n")
    order = {s: i for i, s in enumerate(reversed(STATUS_ORDER))}
    rows = sorted(res["checks"], key=lambda c: (order.get(c["status"], 9),
                                                -c["weight"]))
    for c in rows:
        icon = {"OK": "  ok  ", "LOW-RISK": " low  ", "FLAT": " FLAT ",
                "ELEVATED": " ELEV ", "HIGH": " HIGH "}[c["status"]]
        print(f"[{icon}] {c['name']} {c['provenance']}")
        print(f"          measured: {c['display']}")
        print(f"          target:   {c['band']}")
        if c["note"] and (verbose or c["status"] != "OK"):
            for line in _wrap(c["note"], 64):
                print(f"          {line}")
        if verbose and c["matches"]:
            for ln, txt in c["matches"][:12]:
                print(f"          L{ln}: {txt}")
        print()
    print("-" * 78)
    print(f"AI-pattern density score: {res['score']}/100   ->  {res['verdict']}")
    print("-" * 78)
    print("Score is a weighted rollup, not a detector probability. Specificity "
          "and\nrhythm carry the most weight because they carry the most signal.")


def _wrap(text: str, width: int) -> Iterable[str]:
    words, line = text.split(), ""
    for w in words:
        if len(line) + len(w) + 1 > width:
            yield line
            line = w
        else:
            line = f"{line} {w}".strip()
    if line:
        yield line


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Deterministic linter for AI-writing patterns.")
    ap.add_argument("paths", nargs="*", help="files to check; omit to read stdin")
    ap.add_argument("--json", action="store_true", dest="as_json")
    ap.add_argument("--verbose", "-v", action="store_true")
    args = ap.parse_args()

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

    results = {}
    worst = 0.0
    for path, raw in docs:
        raw = unicodedata.normalize("NFC", raw)
        res = analyse(raw, args.verbose)
        results[path] = res
        worst = max(worst, res.get("score", 0.0))
        if not args.as_json:
            render(path, res, args.verbose)
            print()

    if args.as_json:
        print(json.dumps(results if len(results) > 1 else
                         next(iter(results.values())), indent=2))

    return 0 if worst < 12 else (1 if worst < 28 else 2)


if __name__ == "__main__":
    sys.exit(main())
