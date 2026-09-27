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

**3.** After hybrid search came back with byte-for-byte identical results to the "before" run, I asked Claude why it might have had zero effect rather than assuming it was broken. Claude walked through the actual BM25 math with me: hybrid reranking can only help when the *question itself* contains a term that discriminates between candidates, and my question never mentioned the specific fact I was testing for ("9:00am") — it just said "hours" and "weekends," which every wrongly-retrieved document also contained. That reasoning changed my diagnosis from "semantic search misses exact terms" to the real mechanism: two dining halls each having a main post plus a followup structurally crowd out a single-post dining hall regardless of ranking method. I wrote the corrected diagnosis myself once I understood the actual mechanism.

<!-- ── Stretch features ─────────────────────────────────────────────────────
     Doing one? Say so here BEFORE you start. A feature this README never
     claims earns nothing.
     ───────────────────────────────────────────────────────────────────────── -->

---

# Unit 2

## Run Log — Before

`python run_eval.py --label before` — 3 runs per question, caching off. Full
output in `results/run_2026-09-23_1901_before.md`.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 | 4/5 | 4/5 | 4/5 | MET |
| 2. Every answer names a source | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 4. No chunk exceeds 800 characters | true | true | true | true | MET |
| 5. Answer returned in under 1 minute | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |

**Note on Criterion 1's real evidence:** `judge()` scores the *generated
answer* text for the `expects` phrase, but Criterion 1 is actually about
whether the *retrieved chunk* contains the answer — a different layer.
`run_eval.py`'s raw pass/fail (fail, pass, fail on the dorms question) was
catching Gemini's wording changing between "kitchen and bathroom" (singular)
and "kitchens and bathrooms" (plural) — not a retrieval problem. I checked
the actual retrieved chunk text directly for all 5 questions instead:

| Question | Expects | In retrieved chunk text? |
|---|---|---|
| Which on-campus dorms offer private rooms or restrooms? | `kitchen and bathroom` | Yes — `housing_tamsin_court.txt` |
| Do students get chosen randomly for housing? | `credit hours` | Yes — `admin_housing_lottery.txt` |
| What's the deadline for starting a grade appeal? | `fifteen days` | Yes — `admin_grade_appeals.txt` |
| Do dining halls have different hours on weekends? | `9:00am` | **No** — correct source (`dining_kestrel_commons.txt`) never retrieved |
| Can I add a course after week 1? | `second week` | Yes — `admin_add_drop_deadline.txt` |

4 of 5, identical across all 3 runs since retrieval is deterministic — MET
against my 4-of-5 target.

**Note on Criterion 5's real evidence:** the first timing pass showed cached
responses ("0 model calls, 1 served from cache"), which isn't a real
measurement of pipeline latency. I cleared `.cache` and re-ran all 5 with
`time`, confirming real model calls each time:

| Question | Real time (uncached) |
|---|---|
| Which on-campus dorms offer private rooms or restrooms? | 5.14s |
| Do students get chosen randomly for housing? | 3.79s |
| What's the deadline for starting a grade appeal? | 3.22s |
| Do dining halls have different hours on weekends? | 3.74s |
| Can I add a course after week 1? | 3.73s |

All 5 comfortably under the 1-minute target — MET, 5 of 5.

### Real output — Criterion 1 & 2 evidence (Question 4, all 3 runs)

The one genuine miss at the chunk level. Answer text pasted from
`results/run_2026-09-23_1901_before.md`:

```
### Do dining halls have different hours on weekends? — run 1
Best distance: 0.4325 (passed the gate)
Sources retrieved: dining_halden_hall.txt, dining_halden_hall_followup.txt, dining_pellew_dining_hall.txt, dining_pellew_dining_hall_followup.txt, money_jobs.txt

Yes, dining halls have different hours. Halden Hall is closed on Sundays (and its weekday hours are 7:30am to 7:00pm) (dining_halden_hall.txt), while Pellew Dining Hall is open daily from 7:00am to 8:00pm (dining_pellew_dining_hall.txt).

### Do dining halls have different hours on weekends? — run 2
Best distance: 0.4325 (passed the gate)
Sources retrieved: dining_halden_hall.txt, dining_halden_hall_followup.txt, dining_pellew_dining_hall.txt, dining_pellew_dining_hall_followup.txt, money_jobs.txt

Yes, dining halls have different hours. Halden Hall is closed on Sundays (and its hours are listed for weekdays), while Pellew Dining Hall is open daily from 7:00am to 8:00pm.

### Do dining halls have different hours on weekends? — run 3
Best distance: 0.4325 (passed the gate)
Sources retrieved: dining_halden_hall.txt, dining_halden_hall_followup.txt, dining_pellew_dining_hall.txt, dining_pellew_dining_hall_followup.txt, money_jobs.txt

Yes, dining halls have different hours on the weekend. Halden Hall is closed on Sundays (dining_halden_hall.txt), while Pellew Dining Hall is open daily (dining_pellew_dining_hall.txt).
```

### Real output — the relevance gate (all 5 out-of-scope questions)

```
Refused 5 of 5, cutoff 0.6:
  refused  (best distance 0.825)  What is the capital of Mongolia?
  refused  (best distance 0.934)  How do I change the oil in a diesel engine?
  refused  (best distance 0.886)  Who won the 1994 World Cup?
  refused  (best distance 0.844)  What is the recommended dosage of ibuprofen for a headache?
  refused  (best distance 0.896)  How do I write a for loop in Rust?
```

## Verdicts

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 | Retrieved chunk contains the answer | MET | My scorer's raw pass/fail (fail, pass, fail on the dorms question) was actually catching Gemini's wording changing between "kitchen and bathroom" and "kitchens and bathrooms," not a retrieval problem — so I checked the retrieved chunk text directly for all 5 questions instead of trusting judge()'s output. 4 of 5 questions had the answer literally present in a retrieved chunk, identically across all 3 runs since retrieval is deterministic, meeting my 4-of-5 target. |
| 2 | Every answer names a source | MET | All 15 answers across the 3 runs (5 questions × 3 runs) named at least one source file, with zero exceptions — this held even on the question that failed Criterion 1, since the system still cited real (if not fully sufficient) sources. |
| 3 | Gate stops out-of-corpus questions | MET | All 5 out-of-scope questions were refused in every run, exceeding my 4-of-5 target. Since retrieval is deterministic and the gate is a fixed comparison, this is a single measurement rather than something that could vary across 3 runs. |
| 4 | No chunk exceeds 800 characters | MET | Confirmed directly from the index summary at indexing time: 88 chunks, longest 549 characters, well under the 800-character ceiling. This is a structural property of the chunker, not something that varies per question, so a single check across the whole corpus is sufficient evidence. |
| 5 | Answer returned in under 1 minute | MET | My first timing pass showed 0 model calls (cached results), which isn't a real latency measurement. After clearing `.cache` and re-running all 5 questions with real model calls, times ranged from 3.22s to 5.14s — comfortably under the 1-minute target, 5 of 5. |

## Diagnoses

All 5 criteria came out MET at the target level, so nothing here required
loosening a target to pass. But diagnosing at the individual-question level
inside Criterion 1 surfaced one real, reproducible failure worth tracing
properly, since the aggregate 4-of-5 target was loose enough to absorb it
without registering as a miss.

**Question 4 ("Do dining halls have different hours on weekends?") — Retrieval failure.**

The correct source, `dining_kestrel_commons.txt`, is never retrieved across
all 3 runs — the same 5 sources come back every time: `dining_halden_hall.txt`,
`dining_halden_hall_followup.txt`, `dining_pellew_dining_hall.txt`,
`dining_pellew_dining_hall_followup.txt`, `money_jobs.txt`. Since retrieval
is deterministic, this isn't noise — it's a structural miss.

The mechanism: my corpus has two documents each for Halden Hall and Pellew
Dining Hall (a main post plus a "followup" reply), so those two dining halls
occupy 4 of the 5 retrieval slots for any generic "dining hall hours"
question, crowding out other dining halls that only have a single document —
like Kestrel Commons — even when that single document is the one that
actually answers the question. On top of that, the Kestrel Commons chunk
itself mixes two topics (wait-time/food tips, and separately, hours/cost),
the exact "one chunk, two ideas" pattern I flagged as a risk in Unit 1's
Chunking Strategy section but chose not to split at the time. A chunk
covering two topics likely produces a more diluted embedding — less
precisely matched to an hours-specific query than a chunk about hours alone
would be — which may be compounding the crowding effect from the duplicate
Halden/Pellew documents.

**Pattern check:** this is currently my only real miss, so there's no
cross-question pattern to report yet — but the mechanism (a mixed-topic
chunk, plus asymmetric document duplication across dining halls) is worth
watching for on other questions if I ran a wider test set.

**Honest note on target-setting:** because my Criterion 1 target was "at
least 4 of 5," this exact known failure sits inside the passing margin
without ever registering as a MISS. A tighter target (5 of 5) would have
caught it. I'm not revising the target after the fact — the current target
stands, and this is exactly the kind of target-safety observation the
assignment asks me to be honest about rather than pretend didn't happen.

## The Improvement

**What I changed:** Added hybrid search — BM25 keyword scoring blended with
existing semantic distance (60% semantic, 40% keyword) — to `store.py`'s
`search()` function, toggled via `config.HYBRID_SEARCH`.

**Why I picked it:** My Milestone 3 diagnosis showed Question 4 ("Do dining
halls have different hours on weekends?") never retrieves its correct
source, `dining_kestrel_commons.txt`, across any of 3 runs. This looked like
a textbook case for hybrid search, per the slides: "names, numbers, or exact
terms that semantic search glides past."

### Run Log — After

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 | 4/5 | 4/5 | 4/5 | MET |
| 2. Every answer names a source | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 4. No chunk exceeds 800 characters | true | true | true | true | MET |
| 5. Answer returned in under 1 minute | 5 of 5 | — | — | — | MET (not re-timed; hybrid reranking is local Python with no extra model calls, so latency is unaffected — confirmed by the identical 15 model calls in this session vs. the before run) |

### Real output — Question 4 after hybrid search (all 3 runs)

```
### Do dining halls have different hours on weekends? — run 1
Best distance: 0.4325 (passed the gate)
Sources retrieved: dining_halden_hall.txt, dining_halden_hall_followup.txt, dining_pellew_dining_hall.txt, dining_pellew_dining_hall_followup.txt, money_jobs.txt

### Do dining halls have different hours on weekends? — run 2
Best distance: 0.4325 (passed the gate)
Sources retrieved: dining_halden_hall.txt, dining_halden_hall_followup.txt, dining_pellew_dining_hall.txt, dining_pellew_dining_hall_followup.txt, money_jobs.txt

### Do dining halls have different hours on weekends? — run 3
Best distance: 0.4325 (passed the gate)
Sources retrieved: dining_halden_hall.txt, dining_halden_hall_followup.txt, dining_pellew_dining_hall.txt, dining_pellew_dining_hall_followup.txt, money_jobs.txt
```

**Did it help? No — and figuring out why changed my diagnosis.**

The retrieved sources for Question 4 are byte-for-byte identical before and
after: `dining_halden_hall.txt`, `dining_halden_hall_followup.txt`,
`dining_pellew_dining_hall.txt`, `dining_pellew_dining_hall_followup.txt`,
`money_jobs.txt` — same distances too (0.4325 both times). Hybrid search only
helps when the *question* contains an exact term that discriminates between
candidates. My question never mentions "9:00am" — it just says "hours" and
"weekends," and every wrongly-retrieved dining hall document *also* says
"hours" and "weekends," since they're all posts about dining hall hours.
BM25 had nothing to discriminate on, so the semantic ranking (which was
already the problem) won every tie.

This means my original diagnosis was half right and half wrong: the
retrieval failure is real, but the mechanism isn't "semantic search glides
past an exact term" — it's that Halden Hall and Pellew Dining Hall each have
2 documents in my corpus (a main post plus a "followup" reply), so they
structurally occupy 4 of 5 retrieval slots for any generic dining-hours
question, regardless of ranking method. Hybrid search targeted the wrong
layer of the problem.

## What's Still Broken

**Question 4 (dining hours) retrieval failure — still unresolved.** My one
allowed improvement (hybrid search) didn't fix it, and the assignment's rule
is one change per unit, so I'm not attempting a second fix now. What I'd try
next, based on the corrected diagnosis: either (1) increase `top_k` from 5 to
7-8 so Kestrel Commons has room to surface even with Halden and Pellew each
occupying 2 slots, tested carefully against the "Lost in the Middle" risk
from lecture — more chunks isn't automatically better; or (2) deduplicate
near-identical "followup" documents at index time, so a single dining hall
doesn't structurally crowd out others just by having more posts written
about it. I stopped here because the unit's own rule is one measured change,
not four — this is the next thing to try, not something I ran out of time
on.

## What I'd Do Differently

I'd rewrite Criterion 1's target. "At least 4 of 5" was loose enough that a
real, reproducible retrieval failure (Question 4) sat inside the passing
margin the entire time — I only found it by manually checking chunk text
against `expects`, not from the verdict itself. A tighter target, or a
sixth criterion specifically about retrieval diversity (e.g. "no single
source document occupies more than 2 of the top-5 slots for any question"),
would have surfaced this exact problem directly from the run log instead of
requiring a separate manual check.

I'd also build `judge()` differently from the start: it currently checks
the *generated answer* text against `expects`, but Criterion 1 is actually
about the *retrieved chunk* — a different layer entirely. Writing a second
scorer function that checks `results` directly (which `judge()` already
receives but doesn't use) would have caught the Question 4 failure
automatically in Milestone 1, rather than needing me to notice the
scorer/criterion mismatch by hand afterward.