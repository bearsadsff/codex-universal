# Metrics, target bands, and the judge rubric

Everything here is derived from Rosmine, *Fixing LLM writing with Distribution
Fine Tuning*, rosmine.ai, 18 May 2026. Figures are paraphrased. Each band is
tagged `[P]` (paper-derived) or `[E]` (calibrated estimate for general English
prose — adjust to your own corpus if you have one).

---

## 1. Why measure similarity instead of quality

"Quality" is not well defined, so the paper measures **similarity to human
writing samples** instead. That reframing is the whole design. It converts a
taste argument into a distance measurement, and it means every target is a
*band* rather than a direction.

Three primary metrics:

| Metric | What it captures | Optimum |
|---|---|---|
| **Token-distribution L2** | Word choice. Catches overuse of specific tokens or n-grams. | 0 |
| **MMD** (Maximum Mean Discrepancy) | Content. Catches genericness, missing detail, concept fixation. | 0 |
| **JMQ** (Judge Model Quality) | Preference. 2x the win rate vs human text. | **1.0, i.e. a 50% win rate** |

### The JMQ point is the one to internalise

JMQ is defined as twice the model's win rate against human completions, so the
scale runs 0–1.0 and **the optimum is a coin flip**. Winning more than half the
time is a failure condition, because being preferred means being
distinguishable.

This inverts the instinct to polish. When you find yourself making a sentence
more elegant than the surrounding human text, you are moving away from the
target, not toward it.

### MMD detail

MMD compares the average within-distribution distance against the average
cross-distribution distance, using an embedding model
(`nvidia/llama-embed-nemotron-8b`) and a Gaussian RBF kernel. It is zero if and
only if the two distributions are identical. It was chosen over other
embedding distances because it was designed as a two-sample test — "did these
come from the same source" — which is exactly the humanizing question.

Practically: MMD is the metric that catches **vagueness**. If output is
generic and never goes into detail, or fixates on one concept, MMD rises even
when token statistics look fine.

### Why not KL or JS divergence

Both behave badly here. Many tokens appear in the reference but not the output,
or vice versa, and those cases dominate the metric. L2 was chosen to avoid that.

---

## 2. Headline results

Trained on ~185K cleaned FineWeb samples, evaluated on 2,000 held-out samples
(JMQ on the first 400).

| Model | MMD ↓ | JMQ ↑ | Token L2 ↓ |
|---|---|---|---|
| 4B SFT super-baseline | 0.047 | 0.27 | 0.0040 |
| 4B DFT | **0.025** | **0.40** | 0.0042 |
| 8B SFT super-baseline | 0.041 | 0.37 | 0.0040 |
| 8B DFT | **0.023** | **0.56** | **0.0031** |
| 14B SFT super-baseline | 0.037 | 0.49 | 0.0039 |
| 14B DFT | **0.018** | **0.80** | **0.0036** |

The "super-baseline" is not a single model — it is the best score achieved
across a hyperparameter sweep over learning rates, LoRA vs full fine-tune, and
sampler settings, taking the max per metric. So it is better than any single
real configuration could be, and taking a max over noisy estimates biases it
upward further. DFT results, by contrast, come from one model at fixed
hyperparameters. The comparison is deliberately stacked against DFT.

**Why this matters for you:** the baseline was tuned to death and still lost.
Slop is not a sampler-settings problem. You cannot temperature your way out of
it, which is the next section.

---

## 3. The two-sided failure — why "add randomness" is not the fix

The optimum sampler setting differs per metric. Token L2 is best at
temperature 1.0; MMD and JMQ are best at lower temperatures. There is no
setting that satisfies all three.

**% of texts containing non-English characters**

| Source | Rate |
|---|---|
| Human training data | 0.1% |
| SFT T=0.7 | 1% |
| SFT T=0.8 | 3.2% |
| SFT T=0.9 | 9.1% |
| SFT T=1.0 | 36.45% |
| DFT | 8.1% |

**% of texts with 3+ consecutive sentences starting with the same word**

| Source | Rate |
|---|---|
| Human | 17.4% |
| SFT T=0.7 | 53.3% |
| SFT T=0.8 | 43.8% |
| SFT T=0.9 | 29.9% |
| SFT T=1.0 | 16.3% |
| DFT | 18.6% |

Read those two tables together. Turning temperature down suppresses gibberish
and produces relentless repetition. Turning it up fixes repetition — SFT at
T=1.0 actually beats the human repetition rate — and simultaneously puts stray
Chinese and Korean characters in 36% of documents. One documented sample
lurched from "a systematic way of thinking about synergy" to "The natural world
or organisms" to economic theory, and dropped `拭엥` in mid-sentence. (Those are
a Chinese character meaning roughly "to wipe" and Korean for "huh?".)

**The lesson for a humanizer:** variance is not humanity. Injecting
unpredictability — odd word choices, deliberate typos, abrupt tangents —
reproduces the high-temperature failure mode. Both ends of the dial are
detectable. Aim for the middle band on every axis.

Note also that the human 17.4% repetition rate was investigated and found
legitimate: lists of questions all starting "How", or consecutive sentences
running "The Lamu Archipelago…", "The islands lie between…", "The largest
island…". So do not treat all anaphora as a defect.

---

## 4. Target bands

### Paper-derived `[P]`

| Feature | Human reference | Target |
|---|---|---|
| Documents containing an em-dash | 18.6% | zero is normal; density is the tell |
| Em-dash relative overuse (GPT-5 vs human) | 5.1x | keep well below one per paragraph |
| Docs with a 3+ same-opener sentence run | 17.4% | 0–1 runs per document |
| Docs with non-English characters | 0.1% | 0 |
| self-BLEU across outputs | 0.061 | ~0.06, and see caveat below |

### Token frequencies — the non-obvious finding

For a 14B SFT model at T=0.8, ranked by relative overuse against human text
among the top 1000 tokens:

| Token | vs human |
|---|---|
| ` The` | **+90%** |
| ` was` | +49% |
| ` is` | +44% |
| ` are` | +31% |
| ` that` | +25% |
| ` the` | +19% |
| `.` | +19% |
| ` a` | +15% |
| ` to` | +11% |
| ` of` | +5% |

These are all *function words*, and the top 10 tokens account for **87.2% of
the squared L2 distance**. The dominant statistical signature of machine text
is not exotic vocabulary. It is ordinary words becoming more ordinary.

Translate each into a writing instruction:

- ` The` +90% and ` is`/` was`/` are` elevated → the model defaults to
  **"The X is Y"** declarative assertion. Fix: use concrete subjects and real
  verbs. Prefer "Rosmine trained a 14B model" over "The model that was trained
  is a 14B model".
- `.` +19% → **too many sentences per unit of text**, i.e. chronically short,
  uniform sentences. Fix: subordinate clauses, longer breath, varied length.
- ` that` +25% → over-explicit complementiser. "He argued that it failed" →
  "He argued it failed."

### n-gram filler `[P]`

Occurrence counts in SFT vs DFT output over the same evaluation set:

| 3-gram | SFT | DFT | Ratio |
|---|---|---|---|
| `it is a` | 520 | 42 | 12.4x |
| `be used to` | 621 | 55 | 11.3x |
| `can be used` | 509 | 71 | 7.2x |
| `the number of` | 501 | 134 | 3.7x |
| `one of the` | 430 | 408 | **1.05x — not a signal** |

Keep `one of the` in mind as a negative control. It is a phrase people love to
ban, and the data says it does not discriminate. Do not waste edits on it.

This also explains a counter-intuitive result: the SFT baseline scored *better*
than DFT on BLEU (0.062 vs 0.051 at 14B). BLEU rewards n-gram overlap with the
reference, so overusing common grammatical patterns inflates it. The
best-BLEU baseline configuration used `top_k=2`, which produces bland,
repetitive text. The paper concluded BLEU is the wrong metric here. Treat any
metric that rewards predictability with suspicion.

### Vocabulary overuse `[P]`

Tokens appearing in ≥2% of responses, ranked by relative frequency against
human writing, for GPT-5:

| Token | Relative diff | Appears in human docs |
|---|---|---|
| corridors | 45.2x | 0.1% |
| norms | 43.1x | 0.1% |
| align | 36.0x | 0.2% |
| metrics | 27.2x | 0.2% |
| engagement | 26.5x | 0.2% |
| — (em-dash) | 5.1x | 18.6% |
| targeted | 5.1x | 1.6% |
| identity | 5.0x | 1% |
| trust | 4.9x | 1.2% |

The em-dash sits *low* on this ranking. Abstract institutional nouns are the
far bigger offender, and nobody talks about them. If a reader cannot tell that
a model is overusing "targeted", "identity", and "trust", em-dash count is not
what is giving the text away.

For contrast, the same analysis on DFT output found its top "overused" tokens
(`file` 5.7x, `smoking` 3.4x, `routine` 2.8x) matched what you get comparing
one set of *human* documents against another (`file` 4.1x, `faith` 3.4x,
`items` 2.7x) — i.e. noise, not signature.

### Diversity `[E]` caveat

self-BLEU measures similarity between an author's own outputs across different
prompts; lower is more diverse. Human 0.061; SFT at T=0.9 0.079–0.081; DFT
0.063–0.066.

**But self-BLEU can be driven arbitrarily low by generating gibberish.** Never
optimise it directly. It is a diagnostic for "am I reusing my own template
across pieces", nothing more. Practically: if you write LO three blog posts
this month, they should not share a skeleton.

---

## 5. The five-dimension judge rubric

Use these for the self-judge gate. Definitions paraphrased from the paper's
judge prompts.

| Dimension | Definition | 14B baseline | 14B DFT |
|---|---|---|---|
| **Clarity** | Easy to follow, precise, readable, well organised; no muddled wording or needless ambiguity. | 70.5 | 82.0 |
| **Coherence** | A clear through-line, logical progression, consistent claims and details, no confusing jumps or contradictions. | 54.5 | 70.0 |
| **Creativity** | Fresh ideas, vivid detail, distinctive phrasing, non-generic development — while still fitting the assignment. | 32.5 | 86.0 |
| **Depth** | Goes past surface points, develops ideas with substance, gives meaningful detail, shows real insight. | 35.5 | 87.5 |
| **Prompt relevance** | Follows the assignment, respects stated constraints, addresses the actual topic, does not drift. | 44.0 | 75.0 |

**The ordering is the actionable part.** Clarity was already fine at 70.5 —
LLMs write clearly. The catastrophic scores were Creativity (32.5) and Depth
(35.5). That is where humanizing effort belongs, and it is why this skill's
priority order puts specificity above punctuation.

### Two critical caveats on self-judging

**1. Judge scores vary wildly by judge.** Same two texts, different graders:

| Judge | Baseline | DFT | Change |
|---|---|---|---|
| Claude Sonnet 4.6 | 37 | 51 | +37% |
| Claude Sonnet | 19 | 46 | +142% |
| Gemini 3.1 Flash | 48 | 62 | +29% |
| Gemini 3.1 Pro Preview | 62 | 72 | +16% |
| Grok 3 mini | 54 | 84 | +56% |
| Grok 4.3 | 35 | 65 | +86% |
| GPT 5.5 | 37 | 41 | +11% |

Absolute self-judge numbers are close to meaningless. Direction of change is
what survives across judges. So use the rubric to compare *your draft against
your revision*, not to certify a draft as good.

**2. LLM judges are biased toward LLM text.** Judges prefer machine-generated
communications in general, and their own generations specifically. You are an
LLM grading text for human-likeness, which means **your self-judge will
systematically under-penalise slop**. Compensate: when a dimension feels like a
7, treat it as a 5. When you cannot decide whether a paragraph is generic, it
is generic.

---

## 6. Honest limits

- The paper reports a sample of 100 outputs scoring as 100% human-written on
  the Pangram detector. Detector behaviour is not stable across tools or
  versions, and this skill makes no such promise.
- The paper's own stronger test — a statistical test for any difference between
  token distributions — **its outputs do not pass**. Even purpose-trained
  models remain distinguishable under a strict test.
- DFT still emits non-English characters in 8.1% of outputs versus 0.1% for
  humans, so it is not a solved problem even in the source work.
- The demo corpus was FineWeb, i.e. blogs and news. Its conclusions transfer to
  expository non-fiction most reliably; creative fiction is explicitly
  untested.
- Bands marked `[E]` in this file and in `slopcheck.py` are calibrated
  estimates, not measurements. Treat them as tripwires, not verdicts.

---

## 7. Measured limitation: the function-word findings do not transfer

§4's token table is the paper's most striking result, and testing it against
frontier chat prose **inverted it**.

The fixtures in `tests/` are one essay in three provenances — student-written,
chat-model-written, and a hybrid — on the same subject at the same length
(~560 words each). Run `python3 tests/compare.py` to reproduce.

The overall ranking holds, which is the good news: human 0.0, hybrid 8.6, AI
21.8 on the linter's rollup. But the per-check breakdown splits sharply.

**Signals that reproduced**, and now carry the most weight:

| Check | Human | AI |
|---|---|---|
| em-dash density | 0.0/1k | 7.14/1k, in 57% of paragraphs |
| negative parallelism | 0.0/1k | 1.79/1k |
| rule-of-three triads | 3.49/1k | 5.36/1k |
| sentence-length variation | CV 0.44 | **CV 0.35 — flat** |

**Signals that inverted**, where the human text scored *worse* than the AI:

| Check | Human | AI |
|---|---|---|
| sentences opening "The" | 6.06% | 2.78% |
| connective scaffolding openers | 3.03% | 0% |
| grammatical filler n-grams | 1.75/1k | 0/1k |
| copular verb rate | 3.49% | 1.96% |

The reason is provenance. §4 measured an SFT'd Qwen3 trained on FineWeb and
sampled at T=0.8 — a base model imitating scraped web documents. A modern
RLHF'd chat model writes nothing like that. It uses contractions, addresses the
reader, avoids "The X is Y" scaffolding, and reaches for em-dashes and
"not X, but Y" instead. The paper's own §3 tables hint at this: post-training
changes the failure mode, and these signals were never measured on a
post-trained model.

Consequences now encoded in `slopcheck.py`:

- Inverted checks are retagged `[P!]`, downweighted to 0.5–0.75, and their
  bands widened, because two of them were flagging genuine human prose.
- Em-dash density and negative parallelism are upweighted to 1.75 and 2.0.
- The vocabulary blocklists contributed **nothing** on this pair: the AI sample
  scored 0.0 on both measured and conventional vocabulary. It never said
  "delve" or "tapestry". A competent modern model does not use the words the
  blocklists hunt, so treat §4.2 of the inventory as a floor, not a detector.
- Specificity barely separated the three (3.32 / 2.90 / 3.21), because the AI
  sample invented plausible figures. The proxy counts specifics; it cannot
  check whether they are true. That is a reader's job, and it is why sourcing
  every specific is a guardrail rather than a linter rule.

The general lesson: a detector calibrated on one generation of models decays
against the next. Re-run `tests/compare.py` with fresh samples periodically,
and trust the checks that still separate.
