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

---

## Capstone

**What This Extends**

The Unofficial Guide (units 1–2): a RAG system over 88 campus_life posts. It
retrieves with hybrid search, refuses past a 0.6 distance cutoff, and asks
Gemini (gemini-3.5-flash-lite) for a grounded answer that names its source.
Until now it only ran as `python app.py ask "..."` on my laptop, plus a bare
`serve.py` that, in its own words, had "no logging, no timing and no
metrics." What's new this unit is the operational layer around that HTTP
service:

1. A single documented command that starts it the way a host would (gunicorn).
2. A structured JSONL log (`logs/requests.jsonl`) with one record for every
   request, failures included. Each record holds timestamp, request id, what
   came in, what went out, total duration, a per-stage time split (retrieval vs
   generation), and the tokens the model actually reported.
3. A measurement script (`tools/measure.py`) that reads cost per request from
   those records rather than from a pricing page.

**The Shape**

**A — Deploy and instrument**, on **Path B (local with logs)**. The extension is
the run path, the instrumentation, and the numbers that come out of it. Retrieval,
the gate and the prompt don't change; the service just becomes observable.

Out of scope, decided before building:
- **No hosting.** The free tier's 512 MB is tight for Chroma + an ONNX
  embedder in memory, and a signup with a card isn't something I'm going to
  sign the user up for. Path B is worth the same.
- **No changes to retrieval, chunking, the relevance gate or the prompt.**
  Those were unit 1–2's work. If the test turns up a problem there, it goes
  in What's Still Broken, not into this unit's build.
- **No dashboard or UI.** The log is a file. Reading it is `tools/measure.py`
  or `jq`, not a web page.
- **No rate limiting or auth** on `/ask`. Both are real gaps for a hosted
  service, and both are a second extension.

Size check: one file changed (`serve.py`), one new tool, one RUNNING.md
section. That's under the ~90-minute build budget.

**Running It**

Path B, local with logs. Hosting is out of scope (see The Shape). The single
start command is `./run.sh`, and [RUNNING.md](RUNNING.md) ("Capstone (unit 9)")
has the environment, the clean-checkout steps and the measuring command.

I tested those instructions on myself: a fresh `git clone` of this repo into
an empty folder, a new venv, `pip install -r requirements.txt`, `cp .env.example
.env` plus a key, then `./run.sh`. The run built the index (`stored 88 chunks in
44.6s`), gunicorn came up, `/health` returned `"index_ready": true`, the
housing-lottery question was answered in 7.4 s cold, and the record landed in
that clone's own `logs/requests.jsonl`. What a fresh clone would otherwise have
hit: `chroma_db/` is gitignored, so there's no index, which is why `run.sh`
builds one when it's missing instead of serving a service that refuses
everything.

**Instrumentation**

Every `POST /ask` writes one JSON line to `logs/requests.jsonl`
(`serve.py::_log_request`). That includes requests the route rejects and
requests that crash: an `@app.errorhandler(Exception)` logs those and returns
JSON instead of Flask's HTML error page.

| field | on | what it is |
|---|---|---|
| `timestamp` | all | UTC, milliseconds |
| `request_id` | all | 12 hex chars, also returned in the response, so a user's complaint can be matched to its line |
| `route`, `status` | all | path and HTTP status sent back |
| `outcome` | all | `answered` · `refused` (gate) · `rejected` (bad input, 4xx) · `error` (crash, 5xx) |
| `question`, `question_chars` | all | what came in (first 500 chars) and its real length |
| `duration_ms` | all | server time for the whole request |
| `corpus`, `model` | all | which index and which model answered |
| `answer`, `answer_chars`, `refused`, `sources` | 200s | what went out |
| `best_distance`, `threshold` | 200s | why the gate decided what it did |
| `retrieval_ms`, `generation_ms` | 200s | where the time went: search + gate, then the model call (0 when refused) |
| `model_calls`, `prompt_tokens`, `output_tokens`, `total_tokens`, `cache_hit` | 200s | what it cost, as reported by the model on the response itself |
| `error_type`, `error` | 4xx / 5xx | which check rejected it, or the exception |

Ten entries from the after run (trial 1; long answers cut at 160 characters
here, in full in the file). The first is the warm-up: a cold start, where
retrieval is 1.7 s because the embedder is loading.

```json
{"timestamp": "2026-11-18T19:47:26.837+00:00", "request_id": "2546474d4882", "route": "/ask", "status": 200, "outcome": "answered", "question": "Where can I print on campus?", "question_chars": 28, "duration_ms": 3831.7, "corpus": "campus_life", "model": "gemini-3.5-flash-lite", "answer": "Based on the provided documents, printing is mentioned in relation to a student printing quota and student accounts, but the documents do not state specific loc…", "answer_chars": 322, "refused": false, "best_distance": 0.4991, "threshold": 0.6, "sources": ["admin_printing_quota.txt", "admin_wifi_and_accounts.txt", "dining_verrill_street_grill.txt", "money_jobs.txt", "money_textbooks.txt"], "retrieval_ms": 1717.9, "generation_ms": 2113.7, "model_calls": 1, "cache_hit": false, "prompt_tokens": 568, "output_tokens": 70, "total_tokens": 638}
{"timestamp": "2026-11-18T19:47:28.096+00:00", "request_id": "f390366debbd", "route": "/ask", "status": 200, "outcome": "answered", "question": "Which on-campus dorms offer private rooms or restrooms?", "question_chars": 55, "duration_ms": 1255.7, "corpus": "campus_life", "model": "gemini-3.5-flash-lite", "answer": "Based on the provided documents:\n- **Tamsin Court** offers rooms that are studio apartments with private kitchens and bathrooms (housing_tamsin_court.txt).\n- **…", "answer_chars": 241, "refused": false, "best_distance": 0.4038, "threshold": 0.6, "sources": ["housing_aldridge_hall.txt", "housing_fenwick_court.txt", "housing_innisfree_hall.txt", "housing_old_brewhouse.txt", "housing_tamsin_court.txt"], "retrieval_ms": 107.0, "generation_ms": 1148.6, "model_calls": 1, "cache_hit": false, "prompt_tokens": 791, "output_tokens": 60, "total_tokens": 851}
{"timestamp": "2026-11-18T19:47:31.172+00:00", "request_id": "12f4c7dfcc43", "route": "/ask", "status": 200, "outcome": "answered", "question": "Do students get chosen randomly for housing?", "question_chars": 44, "duration_ms": 3069.5, "corpus": "campus_life", "model": "gemini-3.5-flash-lite", "answer": "Rising sophomores get a number drawn at random in the housing lottery, but juniors and seniors are ordered by accumulated credit hours first, with random tie-br…", "answer_chars": 203, "refused": false, "best_distance": 0.3053, "threshold": 0.6, "sources": ["admin_housing_lottery.txt", "advising_registration.txt", "housing_aldridge_hall.txt", "housing_aldridge_hall_noise.txt", "housing_tamsin_court.txt"], "retrieval_ms": 86.5, "generation_ms": 2983.0, "model_calls": 1, "cache_hit": false, "prompt_tokens": 598, "output_tokens": 46, "total_tokens": 644}
{"timestamp": "2026-11-18T19:47:32.118+00:00", "request_id": "536cf4cdd8a9", "route": "/ask", "status": 200, "outcome": "answered", "question": "What's the deadline for starting a grade appeal?", "question_chars": 48, "duration_ms": 943.5, "corpus": "campus_life", "model": "gemini-3.5-flash-lite", "answer": "A grade appeal has to be raised within fifteen days of the grade posting. \n\nSource: admin_grade_appeals.txt", "answer_chars": 107, "refused": false, "best_distance": 0.2177, "threshold": 0.6, "sources": ["admin_add_drop_deadline.txt", "admin_grade_appeals.txt", "admin_pass_fail_option.txt", "admin_withdrawal_deadline.txt", "course_stat_150.txt"], "retrieval_ms": 138.9, "generation_ms": 804.6, "model_calls": 1, "cache_hit": false, "prompt_tokens": 542, "output_tokens": 27, "total_tokens": 569}
{"timestamp": "2026-11-18T19:47:34.010+00:00", "request_id": "c1d00e008eaa", "route": "/ask", "status": 200, "outcome": "answered", "question": "Do dining halls have different hours on weekends?", "question_chars": 49, "duration_ms": 1887.6, "corpus": "campus_life", "model": "gemini-3.5-flash-lite", "answer": "Yes. Halden Hall is closed on Sundays (dining_halden_hall.txt), while Pellew Dining Hall is open daily (dining_pellew_dining_hall.txt).", "answer_chars": 135, "refused": false, "best_distance": 0.4325, "threshold": 0.6, "sources": ["dining_halden_hall.txt", "dining_halden_hall_followup.txt", "dining_pellew_dining_hall.txt", "dining_pellew_dining_hall_followup.txt", "money_jobs.txt"], "retrieval_ms": 111.9, "generation_ms": 1775.7, "model_calls": 1, "cache_hit": false, "prompt_tokens": 667, "output_tokens": 40, "total_tokens": 707}
{"timestamp": "2026-11-18T19:47:53.205+00:00", "request_id": "8bc589ac1f6a", "route": "/ask", "status": 200, "outcome": "answered", "question": "Can I add a course after week 1?", "question_chars": 32, "duration_ms": 976.5, "corpus": "campus_life", "model": "gemini-3.5-flash-lite", "answer": "Yes, you can add a course through the end of the second week. \n\nSource: `admin_add_drop_deadline.txt`", "answer_chars": 101, "refused": false, "best_distance": 0.4012, "threshold": 0.6, "sources": ["admin_add_drop_deadline.txt", "admin_pass_fail_option.txt", "advising_registration.txt", "course_biol_160_workload.txt", "course_cs_340.txt"], "retrieval_ms": 103.5, "generation_ms": 872.9, "model_calls": 1, "cache_hit": false, "prompt_tokens": 560, "output_tokens": 30, "total_tokens": 590}
{"timestamp": "2026-11-18T19:47:41.943+00:00", "request_id": "fba9d56b4033", "route": "/ask", "status": 200, "outcome": "refused", "question": "What is the capital of Mongolia?", "question_chars": 32, "duration_ms": 100.3, "corpus": "campus_life", "model": "gemini-3.5-flash-lite", "answer": "I don't have enough information about that.", "answer_chars": 43, "refused": true, "best_distance": 0.8246, "threshold": 0.6, "sources": [], "retrieval_ms": 100.3, "generation_ms": 0.0, "model_calls": 0, "cache_hit": false, "prompt_tokens": 0, "output_tokens": 0, "total_tokens": 0}
{"timestamp": "2026-11-18T19:47:42.037+00:00", "request_id": "550b48095907", "route": "/ask", "status": 200, "outcome": "refused", "question": "How do I change the oil in a diesel engine?", "question_chars": 43, "duration_ms": 91.9, "corpus": "campus_life", "model": "gemini-3.5-flash-lite", "answer": "I don't have enough information about that.", "answer_chars": 43, "refused": true, "best_distance": 0.934, "threshold": 0.6, "sources": [], "retrieval_ms": 91.9, "generation_ms": 0.0, "model_calls": 0, "cache_hit": false, "prompt_tokens": 0, "output_tokens": 0, "total_tokens": 0}
{"timestamp": "2026-11-18T19:47:42.313+00:00", "request_id": "1fa711ba3455", "route": "/ask", "status": 400, "outcome": "rejected", "question": "", "question_chars": 0, "duration_ms": 0.1, "corpus": "campus_life", "model": "gemini-3.5-flash-lite", "error_type": "question_not_string", "error": "'question' must be a string"}
{"timestamp": "2026-11-18T19:47:42.315+00:00", "request_id": "82534a7df505", "route": "/ask", "status": 400, "outcome": "rejected", "question": "", "question_chars": 0, "duration_ms": 0.1, "corpus": "campus_life", "model": "gemini-3.5-flash-lite", "error_type": "body_not_object", "error": "the request body must be a JSON object"}
```

Two failed runs from the before run: the crash path, logged rather than lost.
These are the C2 misses.

```json
{"timestamp": "2026-11-18T19:45:12.226+00:00", "request_id": "ba840881e0a1", "route": "/ask", "status": 500, "outcome": "error", "question": null, "question_chars": null, "duration_ms": 0.1, "corpus": "campus_life", "model": "gemini-3.5-flash-lite", "error_type": "AttributeError", "error": "'int' object has no attribute 'strip'"}
{"timestamp": "2026-11-18T19:45:12.229+00:00", "request_id": "668e9986ca4d", "route": "/ask", "status": 500, "outcome": "error", "question": null, "question_chars": null, "duration_ms": 0.1, "corpus": "campus_life", "model": "gemini-3.5-flash-lite", "error_type": "AttributeError", "error": "'list' object has no attribute 'get'"}
```

The whole log (126 records across the smoke test and six trials) is committed
at `logs/requests.jsonl`.

**What It Costs**

Measured from `prompt_tokens` / `output_tokens` on the log records, which
`generate.py::_record_tokens` reads off each response's `usage_metadata`. The
counts are what the model reported, not what I estimated.

- **The 10-run measurement** (after run, trial 1, the 10 in-scope questions):
  mean **624.6 input + 42.6 output = 667.2 tokens** per answered question,
  mean **1.50 s** server time.
- **All 60 answered questions across six trials:** 624.6 input + 47.9 output =
  672.5 tokens. Server time: mean 2.0 s, median 1.3 s, max 12.6 s. Retrieval is
  ~0.1 s of that (median 103 ms warm); the rest is the model call.
- **Refused questions:** 0 tokens and 0 model calls (30 of 30), ~0.18 s.
  **Rejected requests:** 0 tokens, ~0.1 ms.

In money, at Gemini 3.5 Flash-Lite's list price of $0.30 per 1M input and $2.50
per 1M output tokens: 624.6 × 0.30/1M + 47.9 × 2.50/1M = $0.000187 + $0.000120
= **$0.00031 per answered question**. My actual spend was **$0**, because the
key is on the free tier. The price comes from pricing trackers that cite
Google's page (e.g. pricepertoken.com, eesel.ai); I didn't open Google's page
itself.

**A hundred people a day:** say each asks 5 questions, all answered (an upper
bound, since refusals cost nothing). That's 500 × $0.00031 = **$0.15 a day,
about $4.60 a month**, and 500 × 2.0 s = 1,000 s of server time a day, about
17 minutes for one worker. The money isn't the constraint. The 12.6 s tail is:
one sync worker serves one request at a time, so a slow model call holds up
everyone queued behind it.

**Run Log and Verdicts**

Before, three trials, each a fresh `gunicorn` start
(`results/capstone_2026-11-18_1446_before.md`, produced by
`tools/measure.py::main`, which scores everything from the log records):

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| C1. One complete record per request | 20 of 20 | 20/20 | 20/20 | 20/20 | MET |
| C2. Malformed → 4xx JSON + rejected record | 5 of 5 | 3/5 | 3/5 | 3/5 | MISSED |
| C3. Warm answered ≤ 3000 ms | ≥ 9 of 10 | 8/10 | 4/10 | 8/10 | MISSED |
| C4. Tokens: mean ≤ 750, max ≤ 1000, refused = 0 | all three | 672 / 848 / 5 of 5 | 673 / 850 / 5 of 5 | 676 / 853 / 5 of 5 | MET |
| C5. Answers unchanged (unit-1 questions) | ≥ 9 of 10 | 8/10 | 8/10 | 8/10 | MISSED |

The trials differ (C3: 8, 4, 8) because the answers come from a hosted model
called fresh each time with the cache off. Same code, different afternoon.

Real output underneath each, from `logs/requests.jsonl` via
`results/capstone_2026-11-18_1446_before.md`:

- **C1, MET:** each trial wrote 21 records (20 + the warm-up), and every
  request_id in a response matched exactly one record. Example matched pair:
  trial 1's first question returned `"request_id": "04eae9e09c74"`, and the log
  holds exactly one line for it:
  `{"request_id": "04eae9e09c74", "status": 200, "outcome": "answered", "duration_ms": 2283.1, …}`.
- **C2, MISSED:** `malformed: no body→400, empty question→400, whitespace
  question→400, question is a number→500, body is a JSON list→500`, the same in
  all three trials. The two 500 records are pasted under Instrumentation.
- **C3, MISSED:** trial 2 in-scope `duration_ms`: `[3309.4, 1136.9, 2489.8,
  3072.2, 12580.0, 3065.5, 3425.8, 914.3, 8130.1, 2076.1]`, with retrieval
  `[97.8, 109.7, 115.9, 142.4, 617.1, 98.9, 92.3, 93.4, 95.9, 93.2]` and
  generation `[3211.5, 1027.1, 2373.8, 2929.6, 11962.8, 2966.6, 3333.5, 820.9,
  8034.2, 1982.8]`.
- **C4, MET:** trial 1 per-question `total_tokens`: `848, 648, 569, 711, 588,
  785, 705, 564, 597, 707`; every refused record has `"model_calls": 0,
  "total_tokens": 0`.
- **C5, MISSED:** `✗ Which on-campus dorms offer private room…, ✓ …housing,
  ✓ …grade appeal, ✗ Do dining halls have different hours…, ✓ …add a course`,
  plus 5 of 5 out-of-scope refused. The dorms answer was `"Tamsin Court offers
  studio apartments with private kitchens and bathrooms
  (housing_tamsin_court.txt)"`.

**Diagnoses**

- **C2, stage: the route's input handling (`serve.py::ask`). Mechanism:** it
  assumed the body was a JSON object and the question a string.
  `payload.get(...)` on a list, and `(42 or "").strip()` on an int, both raise
  `AttributeError` before any check runs, so a caller's mistake became a 500.
  The logging itself worked: both crashes left `outcome: "error"` records,
  which is how I can name the exception. I saw the list case in my build smoke
  test before writing the criteria, and left it unfixed so the fix would be
  measured.
- **C3, stage: generation, the hosted Gemini call. Mechanism:** the time
  sits in the model's response time, not in my pipeline, and not in prompt size.
  Across all 30 before-run questions, retrieval was 90 ms–1.0 s; every request
  over 3 s had `generation_ms` over 2.9 s. The slow ones weren't the big ones:
  the 12.6 s request had 585 tokens and the 853-token dorms question took 0.9 s in
  trial 3. Trial 2 was slow across the board (4/10), the other two at 8/10, with
  identical code. That's free-tier latency variance. My target assumed the
  model's tail was rarer than 1 in 10, and on this afternoon it wasn't.
- **C5, stage: my scoring rule, plus one real retrieval miss. Two mechanisms.**
  (1) The dorms answer is correct, but the model writes "private kitchen**s**
  and bathroom**s**" and my criterion's exact-substring rule wants "kitchen and
  bathroom". Unit 2's README documented this exact wording flip, and in the
  after run the model happened to use the singular once (trial 2: 9/10). The
  system didn't regress; the scorer can't tell rewording from regression.
  (2) The weekend-hours question misses "9:00am", which is the retrieval
  failure unit 2 diagnosed and left out of scope. The target-setting mistake is
  mine: I wrote "9 of 10 is no worse than before" from memory of unit 2's
  verdicts. By this scorer, unit 2's own after-run already had the dorms
  question failing all three times (`results/run_2026-09-27_1358_after.md`),
  so the honest baseline was 8 of 10.

**Pattern:** the three misses have three different stages: the route, the
hosted model, and my scorer. Only one, C2, is code I own that was wrong. The
instrumentation is what made each one nameable: the per-stage timings put C3 on
the model, and the `error_type` records put C2 on the route.

**The Improvement**

**What I changed:** one thing. `serve.py::ask` now checks the request's shape
before using it. A body that isn't a JSON object returns 400 `body_not_object`,
and a `question` that isn't a string returns 400 `question_not_string`. Both
are logged as `outcome: "rejected"`. Nothing in retrieval, the gate, the prompt
or generation changed. Commit: "capstone improvement: validate request shape…".

**Why:** the C2 diagnosis named this stage and this mechanism exactly, and it's
the only miss caused by my code. C3's cause is upstream, and C5's is in the
scorer.

After, same three fresh-start trials (`results/capstone_2026-11-18_1448_after.md`):

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| C1. One complete record per request | 20 of 20 | 20/20 | 20/20 | 20/20 | MET |
| C2. Malformed → 4xx JSON + rejected record | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| C3. Warm answered ≤ 3000 ms | ≥ 9 of 10 | 9/10 | 10/10 | 9/10 | MET |
| C4. Tokens: mean ≤ 750, max ≤ 1000, refused = 0 | all three | 667 / 851 / 5 of 5 | 676 / 859 / 5 of 5 | 671 / 848 / 5 of 5 | MET |
| C5. Answers unchanged (unit-1 questions) | ≥ 9 of 10 | 8/10 | 9/10 | 8/10 | MISSED |

Real C2 output after: `malformed: no body→400, empty question→400, whitespace
question→400, question is a number→400, body is a JSON list→400`, in all three
trials. The two rejected records are the last two of the ten under
Instrumentation.

**Did it help?** For C2, yes: 3/5 became 5/5 in every trial, with zero 500s
left. **C3 also flipped to MET, and my change did not cause that.** Validation
runs before retrieval and never touches the model call. The after run's model
calls were simply faster: generation stayed under 3.8 s, against 12 s and 8 s
spikes before. If I counted C3 as fixed I'd be crediting the change with
Google's afternoon, so I'm calling C3 **MET by these runs, with no fix behind
it**. Pooled over both runs it's 48 of 60 under 3 s (20 of 30 before, 28 of 30 after); a second slow afternoon
would miss it again. C1 and C4 held, so the change cost nothing, and C5 didn't
move, as expected.

**What's Still Broken**

- **C5 (missed both runs).** I'd fix the scorer before touching the system:
  normalise singular and plural, or check the retrieved chunk text the way unit
  2 ended up doing by hand. Then the weekend-hours retrieval failure would
  be the only miss left, and I'd decide whether that one is worth a unit. I
  stopped because changing the scorer and calling it a pass is close to moving
  the goalposts, and that fix would have been a second change in a unit that
  allows one.
- **C3 (met this time, not fixed).** The tail is the hosted model. What would
  actually help is a per-call timeout plus one retry on generation (the genai
  client accepts an HTTP timeout), or streaming, so the first words arrive
  under a second. I stopped because a retry doubles the tokens on exactly the
  slow calls, which moves cost (C4) the wrong way, and I'd want a criterion
  for that trade before making it.
- **A target set too low:** C4. All six trials sat at 667–676 mean against a
  750 ceiling, and refusals cost exactly zero. I'd tighten it to **mean ≤ 700
  tokens and max ≤ 900**. That's still above what I measured, but close enough
  that one extra chunk or a longer system prompt would show up as a miss.
  C1 was also never in danger. 20/20 six times says the target was fine, but
  the test never stressed it: no concurrency, no disk errors.

**The one thing I'd do next:** add the generation timeout-and-retry *with* a
criterion on its cost, e.g. "≥ 9 of 10 warm answers under 3 s, and mean
tokens per answered question rises by no more than 10%". Latency is the one
thing a real user of this service would notice, and the log now shows exactly
which stage to aim at.

**How I Used AI**

**Moment 1: checking my criteria before any results existed.**
- *What I asked:* the unit's self-check prompt, run against my committed C1–C5:
  "how exactly would you test it using only the sentence itself, would two
  people score it the same way, and what would have to happen for it to fail?
  Don't rewrite them."
- *What came back:* real ambiguities. Was `duration_ms` the whole request or
  one stage? Did the warm-up count toward C1's 20 (it would make 21 lines)?
  What would C4 average over if an in-scope question got refused? Was C5's
  "contains" case-sensitive, and did ".txt" have to be in the answer text or
  just the `sources` field?
- *What I changed:* I added a "How each is scored" block under the criteria,
  pinning each of those down without changing any target, and committed it
  *before* the first test run. That order is in the history (`d7562d2`
  before `c2c14b0`).

**Moment 2: diagnosing C3, and not taking credit for it.**
- *What I asked:* for the slow requests to be explained from the log, with
  retrieval and generation time and token counts side by side.
- *What came back:* every slow request was slow in `generation_ms`, retrieval
  stayed near 0.1 s, and size didn't predict it (585 tokens took 12.6 s). Then,
  after the fix, the first draft of the results said the improvement had
  helped C2 *and* C3.
- *What I changed:* I cut that claim. The validation fix runs before the model
  call, so it can't have sped generation up. The write-up now says C3 was met
  by a faster API afternoon, with no fix behind it, and keeps the timeout idea
  in What's Still Broken.
