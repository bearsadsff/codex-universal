# Worked examples

Three examples. The first shows what the two failure modes actually look like
in model output. The second is the important one: a measured demonstration that
surface editing does not work. The third is a full rewrite walkthrough.

---

## Example 1: the two failure modes, from the source paper

All three outputs answer the same prompt — explore the coherence and
contradictions in Adam Smith's philosophical and economic systems, as presented
in Andrew Skinner's edited collection — with an outline supplied.

### SFT at T=0.7 — the low-temperature failure

Short excerpt, paraphrased structure: the passage asserts that Smith's economic
theory is unsupported by evidence, then that his theory describes people acting
in their own self-interest, then that his concept of self-interest describes
people acting in their own self-interest, then that self-interest claims people
pursue self-interest in a way that promotes community welfare, then that
self-interest is *thus* a description of people acting in their own
self-interest.

Two defects, both diagnosable without reading closely:

1. **Every sentence but two opens with "Smith's."** This is the anaphora
   pattern measured at 53.3% of documents at this temperature, against 17.4%
   for humans.
2. **The paragraph makes one claim five times.** It circles a definition
   without ever developing it. No named critic, no date, no title, no
   counter-argument. This is Depth scoring 35.5.

Note what is *not* wrong: it is grammatical, clear, and on topic. Clarity
scored 70.5 at baseline. Fluency was never the problem.

### SFT at T=1.0 — the high-temperature failure

The same prompt at maximum temperature produces the opposite pathology: the
text lurches from a "systematic way of thinking about synergy" to "The natural
world or organisms" to economic theory within a few sentences, and drops the
characters `拭엥` mid-flow — a Chinese character meaning roughly "to wipe"
followed by Korean for "huh?".

Repetition is fixed. Everything else broke. 36.45% of outputs at this setting
contain non-English characters against a human baseline of 0.1%.

**The pair is the lesson.** There is no dial position that gives you human
prose. Bland at one end, incoherent at the other.

### DFT — what the target looks like

The improved output engages with a specific interpretive dispute: it reports
that Skinner replies there was a "hidden hand" behind Smith's scientific
arguments, distinguishes that from the "invisible hand", calls the distinction
odd, and then asks directly whether Skinner really believes "invisible hand"
is a better label for Smith's economic ideas than materialism, naturalism,
determinism, or mechanism.

What changed, in order of importance:

- **Named participants and positions.** Real critics with real arguments —
  across the paper's samples, Julian Hoppit, Alistair McMillan, George Davie,
  David Mitchison, with dates and book titles attached.
- **It takes a position and asks a real question.** "Does Skinner really
  believe…" is a writer thinking, not a model summarising.
- **Sentence openers vary.** No anaphora run.
- **It commits to specifics that could only appear in this piece.**

Surface tokens barely feature in that list. Which brings us to:

---

## Example 2: measured proof that surface editing fails

The claim in `SKILL.md` is that depth beats punctuation. Here is the
measurement, produced with the bundled linter on three versions of the same
200-word passage about machine learning.

### Version A — the original slop

```
In today's rapidly-evolving digital landscape, the realm of machine learning is
a testament to human ingenuity. It's not just a tool — it's a paradigm shift.

The importance of robust metrics cannot be overstated. The models are trained on
vast datasets. The results are compelling. The implications are profound.
Experts say that alignment is crucial, and studies show that engagement metrics
are a vital cornerstone of any holistic strategy.
[...]
```

**Score: 67.8/100 — HIGH.** Twelve checks failing.

### Version B — surface-only cleanup

Every item from `slop-inventory.md` §4 and §5 addressed, aggressively:

- all em-dashes removed
- every flagged vocabulary item replaced with a plain synonym — "landscape" →
  "world", "robust" → "strong", "leverage" → "use", "delve" → "examine",
  "tapestry" → "structure", "metrics" → "measurement"
- negative parallelism removed: "It's not just a tool — it's a paradigm shift"
  → "It is a major shift"
- "In conclusion" → "To summarise"

This is exactly what a conventional humanizer skill does, done thoroughly.

**Score: 47.3/100 — still HIGH.** Eight checks still failing, and critically:

```
specificity: 0.00/100 words (0 proper nouns, 0 numerals, 0 quotations)
```

Zero. Unchanged from Version A. Every banned word is gone and the text still
says nothing. Also still failing: copular verb rate, sentences opening "The",
connective scaffolding, filler n-grams, vague attribution, hollow sentences —
because those are *structural*, and synonym substitution does not touch
structure. The `the`-rate actually got worse, since the replacements were
wordier.

### Version C — depth-first rewrite

Same subject, but rewritten after asking what the passage was actually about
and getting real material: names, dollar figures, model sizes, dataset counts,
the actual metric values, the temperature tables.

```
Ben Rosmine bought six RTX 6000 Ada cards, put them in a server in his house,
and spent roughly $48,000 finding out that supervised fine-tuning has a
measurement problem nobody had bothered to name.

His setup was ordinary. Start from Qwen3 instruct checkpoints at 4B, 8B, and
14B. Train on 185,000 FineWeb documents, cleaned line by line with Qwen3-32B to
strip the junk that clings to scraped web pages: contact footers, image
captions with no image. Hold out 2,000 samples. [...]
```

**Score: 8.6/100 — LOW.** Specificity 6.47 per 100 words.

### The three numbers side by side

| Version | What was done | Score | Specificity |
|---|---|---|---|
| A — original | nothing | 67.8 HIGH | 0.00 |
| B — surface only | every word/punctuation tell fixed | **47.3 HIGH** | 0.00 |
| C — depth first | content supplied, then rewritten | **8.6 LOW** | 6.47 |

Surface cleanup recovered 30% of the distance. Rewriting for content recovered
87%. **This is why the priority order runs Depth → Creativity → Relevance →
Coherence → Clarity → Surface, and not the other way round.**

### The uncomfortable corollary

Version B was only possible as a mechanical edit. Version C required
*information that was not in the original text*. You cannot humanize
contentless prose without adding content, and you must never invent that
content. Which is why GENERATE mode refuses to draft from an outline with no
specifics, and REWRITE mode's first move on a hollow paragraph is to ask LO for
the facts or cut the paragraph.

If a rewrite request arrives with text this empty and no source material, say
so plainly: *this passage contains no verifiable content, so the most I can do
is surface cleanup that will take it from 68 to 47. Give me the specifics and I
can take it to single digits.*

---

## Example 3: reading linter output like an editor

Version C still had three flags:

```
ELEVATED  measured-overuse vocabulary: 2.31/1k   -> metrics x1 (27.2x)
ELEVATED  conventional AI vocabulary: 2.31/1k    -> synergy x1
ELEVATED  rule-of-three triads: 4.62/1k          -> 2 triad(s)
```

All three are correct detections and all three should be left alone:

- **`metrics`** appears because the passage is *about* evaluation metrics. The
  word is load-bearing. Replacing a technical term with a vaguer one to satisfy
  a linter makes the writing worse.
- **`synergy`** appears inside a report of what the model actually generated
  ("a systematic way of thinking about synergy"). It is quoted material.
  Quoted material is frozen.
- **The triads** are "learning rates, LoRA against full fine-tuning, every
  sampler setting" and one other. That is a real enumeration of three real
  things, not padding. §7 of the inventory covers this: if all three items
  carry information, keep all three.

**The linter produces evidence, not verdicts.** A flag means look; it does not
mean edit. When you leave a flag standing, say why in your report to LO — that
is the difference between an editor and a find-and-replace script.

Conversely, `OK` on every check does not mean the text is good. Version B would
pass a naive vocabulary check while saying nothing whatsoever. The linter
cannot see whether an argument is any good. That is what the five-dimension
self-judge and the deletion test are for.

---

## Quick reference: the transformation moves

| Symptom | Move |
|---|---|
| "The X is Y" chains | concrete subject + real verb |
| paragraph restates itself | delete all but the strongest version, then develop it |
| "experts say" | name the expert or cut the claim |
| no numbers anywhere | ask for the numbers |
| every sentence 12–15 words | merge two, then follow with a four-word one |
| abstract nouns (alignment, engagement) | name the concrete thing happening |
| "In this section we will…" | delete; the next sentence is your opener |
| triad where item 3 is filler | cut to two |
| em-dash in every paragraph | vary the substitute: comma, colon, full stop, parens |
| reads competent but anonymous | add the one opinion only this author would hold |
