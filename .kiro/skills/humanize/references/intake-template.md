# GENERATE intake brief

The source research found its single most effective anti-slop intervention was
not the training algorithm — it was **forcing structured input**. The demo
requires a prompt, an outline including stats and quotes, a style, and a use
case, and the author is explicit that these fields are not needed by the
algorithm at all. They exist to make the writer think.

The reasoning, in his words paraphrased: LLMs are not the cause of slop, lack of
effort is. Spend days researching, put everything into a detailed outline, hand
that to a model, and the output is worth reading — even with a lot of em-dashes
in it.

So: collect these six fields before drafting. Paste this block to LO.

---

```markdown
## 1. Prompt
What am I writing, and for whom?
- Subject:
- Audience (be specific — "senior backend engineers evaluating a migration",
  not "developers"):
- What should the reader do or believe afterwards:
- What they already know (so I don't explain it back to them):

## 2. Outline  ← the field that decides whether this works
Section by section. Include the ACTUAL specifics that will appear:
numbers, names, dates, quotes, product versions, benchmark results,
anecdotes. An outline of abstract topic labels produces slop.

- Section 1 —
  - fact / stat / quote:
  - fact / stat / quote:
- Section 2 —
  - fact / stat / quote:
- Section 3 —
  - fact / stat / quote:

Sources for the above (link or "mine / from memory / needs research"):

## 3. Style
- Voice reference (a writer, publication, or a link to my own past piece):
- Sample paragraph of the target voice (paste 100+ words if available — this
  is worth more than any adjective):
- Person: first / second / third
- Register: formal / neutral / conversational / blunt
- Contractions: yes / no
- Humour: none / dry / heavy

## 4. Use case
blog post / newsletter / cold email / internal memo / README / API docs /
landing page / conference talk / video script / social post / report / other:

## 5. Target length
- Words:
- Hard ceiling? yes / no

## 6. Constraints
- Em-dashes: allowed / banned
- Terms I must use (product names, defined terms):
- Terms I must avoid:
- Headings: required / optional / none
- Formatting: markdown / plain text / HTML
- Anything legally or factually load-bearing that must survive untouched:
```

---

## Handling a thin brief

**If the outline has no specifics, stop.** Say which sections lack facts and
offer three options:

1. LO supplies them.
2. You research them (if tools allow) and he approves before drafting.
3. You draft with `[VERIFY]` markers at every unsupported claim.

Do not silently pick option 3 and hand over prose full of plausible-sounding
invented detail. That converts a style problem into a factual one, which is
strictly worse.

**If there is no style sample**, ask for any 100 words LO has written on any
subject. A real sample beats every adjective in field 3 combined. Absent that,
propose a specific named voice and get confirmation — "closer to Patrick
McKenzie than to a McKinsey deck?" — rather than guessing.

**If LO says "just write it, don't interrogate me"**, then write it. Use option
3, keep it short, mark the gaps, and say in one line what you would have asked
for. Do not litigate the brief.

---

## Minimum viable brief

When a full brief is genuinely disproportionate — a three-line email, a commit
message — collapse to three questions:

1. Who reads this and what do they do next?
2. What are the two or three concrete facts that must appear?
3. Whose voice, and how long?

That is enough to avoid the worst of it. Anything longer than a couple of
hundred words deserves the full six fields.
