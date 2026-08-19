# Slop inventory

Ordered by leverage, worst first. Multipliers marked `[P]` are measured
overuse rates against human writing from the source paper; unmarked entries
are conventional tells with no measurement behind them — weaker evidence,
still worth fixing.

**Before using any of this, read the priority warning:** every item below is a
*surface* fix. Surface fixes were the smallest measured lever. If you work
this file top to bottom without first fixing depth and specificity, you will
produce clean text that still reads like a machine. See §1.

---

## 1. Structural tells (highest leverage)

### 1.1 Assertion instead of action

The strongest measured token signal was ` The` at **+90%** versus human text,
with ` is` +44%, ` was` +49%, ` are` +31% `[P]`. Together these describe one
habit: the **"The X is Y"** frame.

```
✗ The implementation is a critical component of the system. The results are
  significant. The approach is scalable.

✓ Rosmine ran the whole thing on six 6000 Ada cards in his house. It scaled
  to 14B parameters, which nobody expected from a home rig.
```

Fixes: concrete subject, real verb, and vary how sentences open. Watch for
`there is` / `there are` as the same disease.

### 1.2 Too many sentences

`.` was **+19%** overused `[P]`, which is a period surplus — chronically short,
uniform sentences. Human prose clusters: several long sentences, then a short
one for impact. Not alternating, not uniform.

```
✗ The model was trained. The data was cleaned. The results were measured.
  The findings were clear.

✓ The model trained on 185K FineWeb documents, cleaned line by line with
  Qwen3-32B to strip page furniture like contact footers and orphaned image
  captions. Then he measured it three ways. It failed all three.
```

### 1.3 Restatement loops

The paper's worst sample opened all but two of its sentences with "Smith's"
and restated one claim five times. Test: could you delete a sentence with no
information lost? If the paragraph survives, it was a loop.

### 1.4 Over-explicit complementiser

` that` +25% `[P]`. "He argued that it failed" → "He argued it failed."

### 1.5 Outline-shaped prose

If your section headings are parallel and your paragraphs are parallel and
each section is the same length, you have transcribed an outline rather than
written prose. Sections should be as long as their content requires.

### 1.6 Vague attribution

"Experts say", "studies show", "research suggests", "many argue", "a growing
body of research", "it is widely believed". Every one of these is a missing
citation wearing a disguise. Name the source or cut the claim.

---

## 2. Grammatical filler n-grams `[P]`

Ratios in `metrics.md` §4; the fixes are here.

| Phrase | Rewrite as |
|---|---|
| `it is a` | name the thing, or drop the copula |
| `be used to` | active verb — "engineers use X to…" |
| `can be used` | "X does Y" |
| `the number of` | give the number |

**Negative control:** `one of the` measures at 1.05x, so it carries no signal.
Leave it standing. It sits here to keep it from being added to the list later.

---

## 3. Negative parallelism

Named explicitly in the source paper as a slop sign `[P]`. The family:

- "It's not X, it's Y"
- "It's not just X — it's Y"
- "This isn't about X, it's about Y"
- "Not only X but also Y"
- "Less about X and more about Y"
- "Not because X, but because Y"

The construction is not inherently bad; **the density is**. One in a long piece
reads as emphasis. Three reads as a template. When cutting, say the positive
claim directly and delete the negated setup entirely — do not swap in another
contrastive frame.

```
✗ Slop isn't just annoying — it's exhausting.
✓ Slop is exhausting.
```

---

## 4. Vocabulary

### 4.1 Measured overuse `[P]`

Ranked list with multipliers in `metrics.md` §4: `corridors`, `norms`,
`align`/`alignment`, `metrics`, `engagement`, then `targeted`, `identity`,
`trust`. `slopcheck.py` carries the full set.

Note the shape of that list — abstract institutional nouns. They let a sentence
sound substantive while committing to nothing, which is why a synonym fixes
nothing. Name the concrete thing instead: "aligning stakeholder incentives" →
"getting the sales team to stop promising features".

### 4.2 Conventional tells (no measurement)

Named in the source paper: **delve**, **em-dash overuse**, **"it's not X, it's
Y"**, **"You're absolutely right"**, and — for invented character names —
**"Elara Voss"**, which multiple models converge on. Also documented: model
fixation on **goblins** when asked to be imaginative. If you need an invented
name or a whimsical example, deliberately reject your first instinct; that
instinct is shared across models.

Widely-observed, unmeasured:

*Verbs* — leverage, utilise, foster, navigate, unlock, unleash, elevate,
empower, embark, underscore, delve, dive into, unpack, harness, spearhead.

*Adjectives* — pivotal, crucial, vital, robust, seamless, nuanced,
multifaceted, holistic, intricate, meticulous, profound, transformative,
groundbreaking, cutting-edge, ever-evolving, comprehensive.

*Nouns* — testament, tapestry, realm, landscape, myriad, plethora, paradigm,
synergy, cornerstone, beacon, game-changer, deep dive, treasure trove.

*Phrases* — "in today's fast-paced world", "in the realm of", "when it comes
to", "it's worth noting", "it is important to note", "cannot be overstated",
"at the end of the day", "the world of", "whether you're a beginner or a
seasoned professional", "by understanding", "let's dive in", "in conclusion".

**Do not thesaurus-swap.** "Leverage" → "utilise" fixes nothing; both are
Latinate evasions of "use". And the sentence shape usually survives the swap,
which is what was actually detectable.

---

## 5. Punctuation and formatting

### 5.1 Em-dash

Two consequences people get wrong (figures in `metrics.md` §4):

1. **An em-dash-free document is normal.** Roughly four in five human documents
   contain none, so removing all of them raises nothing.
2. **It is a mid-ranking offender**, sitting below `corridors`, `norms` and
   `align`. Hunting em-dashes while writing "aligning norms across corridors"
   has the priorities inverted.

Band in `slopcheck.py`. Vary the substitute — comma, colon, full stop, or
parentheses, whichever matches the actual relationship — so one signature does
not simply replace another.

### 5.2 Rule of three

"Fast, cheap, and reliable." Fine once. As a reflex it is a tell, and the third
item is usually padding. Test each triad: if item three adds no information,
cut to two. If all three are real, keep all three.

### 5.3 Connective scaffolding as sentence openers

Moreover, Furthermore, Additionally, Consequently, Therefore, Thus, Indeed,
Ultimately, Importantly, Notably, Overall, Firstly/Secondly/Lastly. Human
writers carry logical flow in the sentences themselves and use these sparingly.
Under ~8% of sentences.

### 5.4 Other formatting tells

- Bold-lead bullets in a list where every item has identical shape
  (`**Term** — definition`) repeated more than about four times.
- Emoji section headers in technical prose.
- Every list having exactly three items.
- A summary paragraph that restates the section that just ended.
- Title-Case Headings Everywhere.
- Perfectly balanced paragraph lengths.

### 5.5 Foreign-script characters

Human baseline: 0.1% of documents `[P]`. Any CJK, Hangul, Cyrillic, or emoji
character in English prose that is not deliberate is a decode artefact. This
was the high-temperature failure mode — 36.45% of SFT outputs at T=1.0. Zero
tolerance.

---

## 6. Hollow sentences

Sentences that describe the document instead of saying anything:

- "In this section, we will explore…"
- "Let's dive into…" / "Let's delve into…"
- "It's important to note that…"
- "By understanding these dynamics…"
- "Whether you're a beginner or a seasoned professional…"
- "In today's fast-paced digital landscape…"
- "In conclusion," / "To sum up,"
- "This article will show you…"

Delete on sight. They are pure scaffolding — the sentence after them usually
starts the actual content, and works better as the opener.

---

## 7. Leave standing

Every item below is inside the human band already. Editing it moves the text
out of the band and produces the **flat** signature instead.

- **A single em-dash.** Common in human writing.
- **One run of three sentences opening on the same word.** 17.4% of human
  documents carry one, and inspection confirmed all of them legitimate — lists,
  or "The islands lie between…", "The largest island…" `[P]`.
- **`one of the`.** Measures at 1.05x, so it carries no signal `[P]`.
- **Long sentences.** The data says machine prose runs *too many short* ones.
- **Passive voice where it is correct** — the actor unknown, irrelevant, or
  deliberately de-emphasised.
- **A repeated key term.** Elegant variation ("the model", "the system", "the
  framework" for one thing) reads worse than repetition, because it leaves the
  reader wondering whether you mean three different things.
- **Semicolons.** Some people just write like that.
- **Clear, well-organised prose.** Judged clarity was already good at baseline;
  it was never the problem. Keep writing clearly.
