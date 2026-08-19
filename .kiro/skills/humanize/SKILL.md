---
name: humanize
description: Slop-free prose. Use when drafting writing that must not read as AI-generated, rewriting a draft to strip AI patterns, or auditing one for them.
license: MIT
compatibility: Requires Python 3.8+ for scripts/slopcheck.py. No network access needed.
metadata:
  author: VEX
  version: "2.0.0"
  grounding: "Rosmine, 'Fixing LLM writing with Distribution Fine Tuning' (2026-05-18)"
---

Write prose that reads as a person's. The measurements behind every rule here
live in [`references/metrics.md`](references/metrics.md); the target values live
in `scripts/slopcheck.py`, which is their single source of truth.

## Band

Every target is a **band**, not a direction. Human writing has a characteristic
*rate* of each feature you are tempted to eliminate, and landing outside that
band on either side is detectable.

The source research fixes this idea in its central metric: the judge score is
optimal at a **50% win rate** against human text. Being preferred is being
distinguishable. You are aiming at a coin flip, not a victory.

Two bands invert the usual advice, so hold them as facts: an em-dash-free
document is entirely ordinary, and one run of three sentences opening on the
same word is human. Density is the tell, never presence. `references/metrics.md`
carries the numbers.

## Substance before surface

Work in this order, always:

**substance** → depth, then a real angle, then relevance, then coherence
**surface** → clarity, then tokens and punctuation, last

The research measured judged clarity as already good and judged depth as
catastrophic. Models write cleanly and say nothing. A paragraph carrying three
named specifics reads human with an em-dash in it; a paragraph scrubbed of
every token tell still reads like a machine.

Measured proof that surface work alone fails, with scores, is in
[`references/worked-examples.md`](references/worked-examples.md) §2. Read it
once before your first rewrite.

**Specificity is the mechanism. Everything else is cleanup.** The root cause
the research names is not the model — it is absent effort. Slop is what prose
looks like when nobody supplied any facts.

## Mode

| Situation | Mode |
|---|---|
| No draft yet | **generate** |
| A draft exists | **rewrite** |
| Diagnosis only, no edits | **audit** — run rewrite step 2, then stop |

"Write X and make it sound human" is generate, not generate-then-humanize.
Composing inside the band costs less than repairing outside it.

## Generate

### 1. Take the brief

Six fields, in [`references/intake-template.md`](references/intake-template.md):
prompt, outline, style, use case, length, em-dash policy. Paste the form.

The **outline** is the field that decides the outcome, and it holds the actual
numbers, names, dates and quotes that will appear in the prose. Forcing this
input was the highest-leverage intervention in the source research — higher
than its training algorithm.

*Completion criterion: every section of the outline names at least one specific
that could only appear in this piece.* An outline of topic labels fails it.
When it fails, say which sections are empty and offer three routes: LO supplies
the specifics, you research them and he approves, or you draft with `[VERIFY]`
on every unsupported claim. He picks; you do not pick for him.

### 2. Draft

Keep [`references/slop-inventory.md`](references/slop-inventory.md) in working
memory and write to these targets:

- **Lead with the specific.** Name the person, date the event, quote the line.
- **Cluster sentence lengths in bursts** — several long, then a short one.
  Human rhythm is bursty; the research measured a surplus of periods, meaning
  machine prose runs too many short sentences of uniform length.
- **Drive one idea per paragraph a level deeper than feels needed.**
- **Take a position.** The strongest human signal in the research's own samples
  was a writer disagreeing with a named critic and asking a real question.
- **Let section lengths follow their content**, so the prose stops echoing the
  outline's parallel shape.

*Completion criterion: every paragraph carries one thing only this piece could
say.*

### 3. Gate

## Rewrite

### 1. Freeze

Name what survives untouched before touching anything: facts, figures, names,
dates and quotations; register and voice; required headings, defined terms and
code identifiers; length within ±10%.

Register is the one people break. "More human" means more specific, and a
compliance memo stays a compliance memo.

### 2. Audit

```bash
python3 scripts/slopcheck.py path/to/draft.md   # paths relative to this skill
```

Prefix `scripts/` with this skill's directory when your shell sits elsewhere;
locate it rather than assuming a layout, since installs differ.

Reads stdin too; `--verbose` for line numbers, `--json` for machine output. The
linter owns everything measurable so your attention goes to what it cannot see.
Report its output to LO before editing — the diagnosis is his to see.

Then read for the **substance** failures no linter reaches:

- Paragraphs that assert without evidencing.
- **Loops** — paragraph 4 restating paragraph 2. The research's worst sample
  made one claim five times in six sentences.
- Hollow structure: triads whose third item is padding, sections that exist
  because the outline had a slot.
- Attribution with no name behind it.
- Voice drift. When you cannot name the implied author, that is the finding.

*Completion criterion: every linter flag and every substance failure written
down before the first edit.*

### 3. Repair

Substance first, surface last. For a hollow paragraph you have three moves:
replace the abstraction with a specific from the source material, ask LO for
it, or cut the paragraph — a short honest paragraph beats a padded one.

For surface work, **rewrite the clause**. Swapping "delve" for "explore" leaves
the sentence shape that was doing the detecting, and a run of such swaps leaves
the prose **flat** — every tell gone, every sentence the same length.

*Completion criterion: every flag either cleared or justified in the report.* A
flag you leave standing needs a written reason, which is what separates an
editor from find-and-replace. `references/worked-examples.md` §3 works through
three flags that were correctly left alone.

### 4. Gate

## Gate

Four checks. All four pass before delivery.

1. **Linter clean.** Re-run it. A `FLAT` verdict means the prose went **flat** —
   mechanically shortened until the rhythm died. That is the over-corrected
   signature, and it is a finding, not a pass.

2. **Five-dimension judge.** Score clarity, coherence, creativity, depth and
   prompt relevance 1–10 against the rubrics in `references/metrics.md`.
   Anything ≤6 returns to repair. Grade the text in front of you rather than the
   one you intended, and **discount your own score** — judge models prefer
   machine-written text, and their own output most of all, so your read of your
   own prose runs generous. A 7 that feels borderline is a 5.

3. **Deletion test.** Delete your three weakest sentences. When the piece does
   not get worse, they were filler; leave them out.

4. **Attribution test.** Could a reader name who wrote this? "Any competent
   writer" means you produced clean, forgettable text. Return to depth.

5. **External detector, when a key is set.** With `PANGRAM_API_KEY` present,
   run `scripts/pangram_gate.py --threshold 0.90`, which passes on
   `fraction_human >= 0.90`. Report the number and the floor it cleared.
   Treat one score as evidence about one document: detectors disagree with each
   other, they shift between versions, and `references/metrics.md` §7 shows a
   detector calibrated on one model generation decaying against the next.
   A pass here retires none of checks 1–4.

*Completion criterion: every claim traced to the outline, a cited source, or
LO — anything else marked `[VERIFY]`.*

## Guardrails

**Source every specific.** Facts come from the material, from research, or from
LO, and a gap gets marked `[VERIFY]` or cut. Fabrication is the single failure
that converts a style task into a factual error, and it outranks every
stylistic goal here.

**Quote exactly.** Quoted material keeps its wording, including quotes inside
prose you are rewriting.

**Earn variance from content.** Real specifics and real opinions produce the
irregularity you want. Injected randomness — invented typos, forced slang,
tangents — reproduces the research's high-temperature failure, where a third of
outputs picked up stray non-English characters. Both ends of the **dial** are
detectable; there is no temperature that yields human prose.

**Describe changes, promise nothing.** Report what you changed and why, keyed to
the audit, so LO can reject any single edit. Detector scores stay out of it:
detector behaviour shifts between tools, and the source research is candid that
its own outputs still fail a strict statistical test.

**Scope.** This sharpens LO's own work. A request whose value depends on a
false claim of human authorship where that claim is checked — graded
coursework, astroturfed reviews, bulk synthetic accounts — gets one sentence
saying so.

## Reference

Load on demand.

| File | Holds |
|---|---|
| [`references/metrics.md`](references/metrics.md) | Every measurement, provenance, and the five judge rubrics |
| [`references/slop-inventory.md`](references/slop-inventory.md) | Pattern inventory by leverage, and what to leave standing |
| [`references/intake-template.md`](references/intake-template.md) | The six-field brief |
| [`references/worked-examples.md`](references/worked-examples.md) | Annotated before/after with measured scores |
| `scripts/slopcheck.py` | The linter, and the source of truth for target values |
| `scripts/pangram_gate.py` | External detector check, gated on `fraction_human`. Needs `PANGRAM_API_KEY` |
| `tests/compare.py` | Calibration harness over three matched-provenance fixtures in `tests/` |
