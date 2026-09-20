# The Unofficial Guide

**Youssef Serag — campus_life**

> **This file is your submission.** Fill it in as you go — most sections get
> written during the milestone that produces them, not at the end.
>
> How the starter works, and every command you'll need, is in `RUNNING.md`.
> Leave that file alone.
>
> **Paste everything as text.** No screenshots, no video. A typed table gets
> full credit; a picture of the same table gets none.
>
> Delete these instruction blocks as you replace them. The `<!-- -->` comments
> are notes to you and don't show up when the page renders — you can leave them
> or remove them.

---

# Unit 1

## What This Does

The Unofficial Guide is a RAG system built over the campus_life corpus — 88 short, informal posts covering the kind of practical information students share with each other but rarely find in official university documentation. Topics include housing lottery mechanics, dining dollar rollover rules, grade appeal deadlines, add/drop timing, and similar day-to-day logistics. Users ask plain-language questions (e.g. "is the housing lottery random?") and the system retrieves the most relevant post(s), then generates an answer grounded in that retrieved text, always naming its source document. If a question falls outside what the corpus covers, the system says so rather than guessing.

## Chunking Strategy

**Chunk size:** 800 (unchanged from starter default)
**Overlap:** 120 (unchanged from starter default)

I kept fallback_split's fixed-size window logic rather than writing a new
splitting strategy. My longest post is 549 characters, well under my
800-character chunk_size, so every post already stays as exactly one chunk —
character-window and paragraph-aware splitting would produce identical
results here. This matches the corpus's own description that "useful
information usually sits in a single sentence," which I confirmed by reading
6 documents directly in Milestone 1. A random sample of 5 chunks (below) all
read as complete, self-contained thoughts, with no sentence cut in half.

split_documents now explicitly calls fallback_split with my chosen config
values, rather than silently using the untouched default — this was a
deliberate decision, not an oversight.

I also checked generate.py and confirmed the starter already implements a
grounding instruction (GROUNDING_INSTRUCTION) as a second layer on top of the
relevance gate — it tells the model to answer only from the provided
documents, refuse rather than guess, and name its source file. I verified
this against my own test runs rather than assuming it worked.

## Sample Chunks

**Chunk 1** — source: `admin_add_drop_deadline.txt#0` — produced by: `chunker.py::fallback_split`

```
On the add/drop deadline

You can add a course through the end of the second week. Dropping is a longer window — through the end of week six — but a drop after week two shows as a W on your transcript. Nothing anywhere on the registrar's site says this plainly, and students find out from each other.
```

**Chunk 2** — source: `course_biol_160.txt#0` — produced by: `chunker.py::fallback_split`

```
BIOL 160 Cell Biology

I lived here my sophomore year. Format is lecture three times a week with a weekly lab. Assessment: four unit tests and a cumulative final. Not curved.

Expect 9 to 11 hours a week, the heaviest first-year course by reputation.

The one piece of advice: the unit tests come fast, roughly every three weeks; falling behind once is very hard to recover from.
```

**Chunk 3** — source: `course_hist_118_workload.txt#0` — produced by: `chunker.py::fallback_split`

```
Workload for HIST 118 Modern World History

People keep asking so: a lot of reading, about 120 pages a week, but no problem sets. That's real time, not optimistic time.

It's front-loaded — the first month is heavier than the rest, partly because you're learning the format.
```

**Chunk 4** — source: `dining_pellew_dining_hall_followup.txt#0` — produced by: `chunker.py::fallback_split`

```
Re: Pellew Dining Hall

Adding to what people have said about Pellew Dining Hall. The wait figure of 12 to 18 minutes at peak matches what I've seen. If you're trying to eat between classes, go before 11:45 and it's a different building entirely.

Also worth saying: the furthest hall from anywhere, next to the athletics centre. Nobody tells you this at orientation.
```

**Chunk 5** — source: `housing_innisfree_hall.txt#0` — produced by: `chunker.py::fallback_split`

```
Innisfree Hall — what it's actually like

Transferred in last year, so take this with a grain of salt. Built 1991, renovated 2022. Rooms are doubles arranged as pairs sharing one bathroom between two rooms.

The good: the shared-bathroom-between-two-rooms arrangement is the best compromise on campus.

The bad: no air conditioning, which matters for the first three weeks of September.

Laundry costs $1.75 wash, $1.75 dry, app-based. On noise: moderate; the building is L-shaped and the short wing is much quieter.
```

## Sample Answer

**Question:** Do students get chosen randomly for housing?

**Answer:**

```
No, the housing lottery is not entirely random; rising sophomores get a
number drawn at random, but juniors and seniors are ordered by accumulated
credit hours first, with random tie-breaks.

Source: admin_housing_lottery.txt
```

**My relevance cutoff:** 0.6 (kept the starter's default)

I ran all 5 in-corpus test questions and all 5 OUT_OF_SCOPE questions and found
a wide, clean gap: my in-corpus questions topped out at 0.433, while my
out-of-scope questions bottomed out at 0.825 — no overlap between the two
groups. 0.6 sits comfortably in that gap, and at this cutoff all 5 in-corpus
questions were answered correctly with sources, and all 5 out-of-scope
questions were correctly refused. I kept the default because the evidence
showed it was already well-placed, not because I didn't check.

| Question | In corpus? | Best distance |
|---|---|---|
| Which on-campus dorms offer private rooms or restrooms? | Yes | 0.404 |
| Do students get chosen randomly for housing? | Yes | 0.305 |
| What's the deadline for starting a grade appeal? | Yes | 0.218 |
| Do dining halls have different hours on weekends? | Yes | 0.433 |
| Can I add a course after week 1? | Yes | 0.401 |
| What is the capital of Mongolia? | No | 0.825 |
| How do I change the oil in a diesel engine? | No | 0.934 |
| Who won the 1994 World Cup? | No | 0.886 |
| What is the recommended dosage of ibuprofen for a headache? | No | 0.844 |
| How do I write a for loop in Rust? | No | 0.896 |

## How I Used AI

**1.** I drafted my Criterion 5 target (answers return in under 1 minute) and wrote "I picked 1 minute to keep a track of a fixed wait time" as my reasoning. Claude pointed out this was circular — it explained what the number was, not why that number specifically. I tried two more times, and Claude kept rejecting each one until I landed on something honest: 1 minute is my subjective ceiling for what still feels like a responsive tool, and I don't have a measured baseline yet, so it's a sanity check rather than a data-backed number. I wrote the final version myself once I understood what was actually missing.

**2.** For Milestone 3, Claude initially suggested I write a custom paragraph-splitting chunker to handle posts that mix two topics (like the housing lottery post). I asked if I could just keep the chunk size at 800 instead. Claude checked that against my actual data — my longest post is 549 characters, well under 800 — and agreed that a fixed-size window and paragraph splitting would produce identical results for my corpus, so keeping the simpler starter logic was a legitimate, evidence-based choice rather than a shortcut. I ended up documenting *why* I kept it instead of writing new splitting code.

<!-- ── Stretch features ─────────────────────────────────────────────────────
     Doing one? Say so here BEFORE you start. A feature this README never
     claims earns nothing.
     ───────────────────────────────────────────────────────────────────────── -->

---

# Unit 2

<!-- These sections get ADDED to what's already above. Don't delete or rewrite
     unit 1 — the point is that someone can see what you said before you knew
     how it went. -->

## Run Log — Before

<!-- Your five criteria, three runs each. `python run_eval.py --label before`
     runs the questions, puts the OUT_OF_SCOPE ones through the gate, and
     writes it all into results/ for you. Targets come from criteria.md; the
     verdict column is your call.

     Criterion 3 is measured in one deterministic pass rather than three, so
     the same number goes in all three run columns. That's correct, not lazy.

     Milestone 1. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

<!-- Underneath, paste the REAL output for each criterion from one of your
     runs — the actual text your system produced, not a description of it.
     Name the file and function that produced it. -->

## Verdicts

<!-- MET or MISSED for each of the five, against the target you wrote last
     unit — not a new one. Plus a sentence on how you decided. That sentence
     matters most where it was close.

     If your target said 4 of 5 and your runs came out 4, 3, 4, that's a MISS.
     The target has to hold, not show up occasionally.

     Milestone 2. -->

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 |  |  |  |
| 2 |  |  |  |
| 3 |  |  |  |
| 4 |  |  |  |
| 5 |  |  |  |

## Diagnoses

<!-- For each miss: which stage caused it, and how. The stage alone isn't
     enough — you need the mechanism.

     Not a diagnosis: "Question 3 didn't work."
     A diagnosis:     "Question 3 asks about laundry costs. The answer is in
                       one sentence that got split across two chunks, so
                       neither chunk on its own contains it."

     The five stages: loading → chunking → embedding → retrieval → generation.

     Look for a pattern. If three misses all ask about numbers, that's one
     problem, not three.

     Missed nothing? Say so, then say honestly whether your targets were set
     low, and which one you'd tighten and to what.

     Milestone 3. -->

## The Improvement

**What I changed:**

**Why I picked it:**

<!-- Connect it to a specific diagnosis above in one sentence. If you can't,
     you picked a fix because it sounded impressive. -->

### Run Log — After

<!-- Same format, same five criteria, three runs each.
     `python run_eval.py --label after` -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

**Did it help?**

<!-- Say plainly whether it did, and how you know. If it made things worse,
     say that — a change that backfired, honestly reported, earns full credit
     and is more interesting than one that worked. What matters is that you can
     tell.

     Milestone 4. -->

## What's Still Broken

<!-- For each criterion still missed after your fix: what you'd do about it,
     and why you stopped where you did.

     "I ran out of time" is fine if it's true. Pretending nothing is left is
     not.

     Milestone 5. -->

## What I'd Do Differently

<!-- Knowing what you know now — which of your five criteria would you write
     differently, and why?

     Milestone 5. -->
     