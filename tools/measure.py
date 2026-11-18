#!/usr/bin/env python3
"""
Capstone test driver — runs the five criteria in criteria.md, three trials.

    python tools/measure.py --label before
    python tools/measure.py --label after

Each trial is one *session*, exactly as criteria.md defines it:

  1. start the service fresh, the way RUNNING.md does (gunicorn, one sync
     worker, AI201_CACHE=0 so every answer is a real model call)
  2. one warm-up question — logged, timed and reported as the cold start,
     but not counted toward any criterion
  3. 20 requests: 10 in-scope questions, 5 out-of-scope, 5 malformed
  4. stop the service, read back the records it wrote to logs/requests.jsonl

Everything a criterion is scored on comes from the log records — the same
file a reader of the README sees — not from timers in this script. That is
the point of the extension: if the log can't answer the question, the
instrumentation isn't done.

Writes results/capstone_<stamp>_<label>.md.
"""

import argparse
import datetime as dt
import json
import os
import signal
import statistics
import subprocess
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import questions  # noqa: E402  (unit 1's test questions)

LOG = ROOT / "logs" / "requests.jsonl"
PORT = int(os.getenv("MEASURE_PORT", "8000"))
URL = f"http://127.0.0.1:{PORT}"

WARMUP = "Where can I print on campus?"

# The 5 unit-1 questions first (criterion 5 scores those), then 5 more that the
# corpus covers, so latency and cost have 10 answered questions to work with.
IN_SCOPE = [q["question"] for q in questions.QUESTIONS] + [
    "How long is the wait at Kestrel Commons at lunchtime?",
    "What time does Halden Hall close?",
    "How do I request a transcript?",
    "Is there a quiet place to study in a group?",
    "How does the campus shuttle work?",
]
EXPECTS = {q["question"]: q["expects"] for q in questions.QUESTIONS}
OUT_OF_SCOPE = list(questions.OUT_OF_SCOPE)

# (label, how to send it)
MALFORMED = [
    ("no body", dict(data=None)),
    ("empty question", dict(json={"question": ""})),
    ("whitespace question", dict(json={"question": "   "})),
    ("question is a number", dict(json={"question": 42})),
    ("body is a JSON list", dict(json=["is the housing lottery random?"])),
]

REQUIRED = ["timestamp", "request_id", "status", "outcome", "duration_ms"]


def start_service() -> subprocess.Popen:
    env = {**os.environ, "AI201_CACHE": "0"}
    proc = subprocess.Popen(
        [str(ROOT / ".venv" / "bin" / "gunicorn"), "serve:app",
         "--bind", f"127.0.0.1:{PORT}", "--workers", "1", "--threads", "1",
         "--timeout", "60"],
        cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    for _ in range(60):
        try:
            if requests.get(f"{URL}/health", timeout=2).ok:
                return proc
        except requests.RequestException:
            pass
        time.sleep(0.5)
    proc.kill()
    sys.exit(f"service didn't come up on {URL}")


def stop_service(proc: subprocess.Popen) -> None:
    proc.send_signal(signal.SIGTERM)
    try:
        proc.wait(timeout=15)
    except subprocess.TimeoutExpired:
        proc.kill()


def ask(kind: str, label: str, **kwargs) -> dict:
    t0 = time.perf_counter()
    try:
        r = requests.post(f"{URL}/ask", timeout=90, **kwargs)
        try:
            body = r.json()
        except ValueError:
            body = {"_not_json": r.text[:200]}
        status = r.status_code
    except requests.RequestException as exc:
        body, status = {"_exception": str(exc)}, None
    return {"kind": kind, "sent": label, "status": status, "body": body,
            "client_ms": round((time.perf_counter() - t0) * 1000, 1),
            "request_id": body.get("request_id") if isinstance(body, dict) else None}


def run_trial(n: int) -> dict:
    LOG.parent.mkdir(exist_ok=True)
    offset = len(LOG.read_text(encoding="utf-8").splitlines()) if LOG.exists() else 0

    proc = start_service()
    try:
        warm = ask("warmup", WARMUP, json={"question": WARMUP})
        sent = []
        for q in IN_SCOPE:
            sent.append(ask("in_scope", q, json={"question": q}))
        for q in OUT_OF_SCOPE:
            sent.append(ask("out_of_scope", q, json={"question": q}))
        for label, kwargs in MALFORMED:
            sent.append(ask("malformed", label, **kwargs))
    finally:
        stop_service(proc)

    lines = LOG.read_text(encoding="utf-8").splitlines()[offset:] if LOG.exists() else []
    records = [json.loads(line) for line in lines if line.strip()]
    by_id = {}
    for rec in records:
        by_id.setdefault(rec.get("request_id"), []).append(rec)
    warm_rec = (by_id.get(warm["request_id"]) or [None])[0]

    for s in sent:
        matches = by_id.get(s["request_id"], []) if s["request_id"] else []
        s["records"] = len(matches)
        s["record"] = matches[0] if matches else None

    # C1 — exactly one complete record per request
    c1 = sum(1 for s in sent if s["records"] == 1
             and all(s["record"].get(k) is not None for k in REQUIRED))

    # C2 — malformed: 4xx JSON with error, logged as rejected
    bad = [s for s in sent if s["kind"] == "malformed"]
    c2 = sum(1 for s in bad if s["status"] and 400 <= s["status"] < 500
             and isinstance(s["body"], dict) and s["body"].get("error")
             and s["record"] and s["record"].get("outcome") == "rejected")
    c2_500s = sum(1 for s in bad if s["status"] and s["status"] >= 500)

    # C3 — warm latency of in-scope questions, from the log
    ins = [s for s in sent if s["kind"] == "in_scope"]
    durations = [s["record"]["duration_ms"] for s in ins if s["record"]]
    c3 = sum(1 for d in durations if d <= 3000)

    # C4 — tokens per answered question; refused cost nothing
    answered = [s["record"] for s in ins if s["record"] and s["record"].get("outcome") == "answered"]
    tokens = [r["total_tokens"] for r in answered]
    oos = [s for s in sent if s["kind"] == "out_of_scope"]
    refused_free = sum(1 for s in oos if s["record"] and s["record"].get("outcome") == "refused"
                       and s["record"].get("model_calls") == 0 and s["record"].get("total_tokens") == 0)

    # C5 — regression on unit 1's questions
    c5 = 0
    c5_detail = []
    for s in ins[:5]:
        answer = (s["body"].get("answer") or "") if isinstance(s["body"], dict) else ""
        ok = EXPECTS[s["sent"]].lower() in answer.lower() and ".txt" in answer
        c5 += ok
        c5_detail.append({"q": s["sent"], "expects": EXPECTS[s["sent"]], "ok": ok})
    for s in oos:
        ok = isinstance(s["body"], dict) and s["body"].get("refused") is True
        c5 += ok
        c5_detail.append({"q": s["sent"], "expects": "refused", "ok": ok})

    return {
        "trial": n,
        "cold_start_ms": warm_rec["duration_ms"] if warm_rec else None,
        "cold_start_record": warm_rec,
        "c1": c1, "c1_of": len(sent), "records_written": len(records),
        "c2": c2, "c2_of": len(bad), "c2_500s": c2_500s,
        "c3": c3, "c3_of": len(ins), "durations_ms": durations,
        "c4_mean_tokens": round(statistics.mean(tokens), 1) if tokens else None,
        "c4_max_tokens": max(tokens) if tokens else None,
        "c4_answered": len(answered),
        "c4_refused_free": refused_free, "c4_refused_of": len(oos),
        "c5": c5, "c5_of": 10, "c5_detail": c5_detail,
        "retrieval_ms": [r["retrieval_ms"] for r in answered],
        "generation_ms": [r["generation_ms"] for r in answered],
        "sent": sent,
    }


def verdict(trials, check) -> str:
    return "MET" if all(check(t) for t in trials) else "MISSED"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="")
    parser.add_argument("--trials", type=int, default=3)
    args = parser.parse_args()

    trials = []
    for n in range(1, args.trials + 1):
        print(f"trial {n}…", flush=True)
        trials.append(run_trial(n))
        t = trials[-1]
        print(f"  C1 {t['c1']}/{t['c1_of']}  C2 {t['c2']}/{t['c2_of']} ({t['c2_500s']}×500)  "
              f"C3 {t['c3']}/{t['c3_of']}  C4 mean {t['c4_mean_tokens']} max {t['c4_max_tokens']} "
              f"refused-free {t['c4_refused_free']}/5  C5 {t['c5']}/10  cold {t['cold_start_ms']} ms",
              flush=True)

    def runs(fmt):
        return " | ".join(fmt(t) for t in trials)

    rows = [
        ("C1. One complete record per request", "20 of 20",
         runs(lambda t: f"{t['c1']}/{t['c1_of']}"),
         verdict(trials, lambda t: t["c1"] == t["c1_of"])),
        ("C2. Malformed → 4xx JSON + rejected record", "5 of 5",
         runs(lambda t: f"{t['c2']}/5"),
         verdict(trials, lambda t: t["c2"] == 5)),
        ("C3. Warm answered ≤ 3000 ms", "≥ 9 of 10",
         runs(lambda t: f"{t['c3']}/10"),
         verdict(trials, lambda t: t["c3"] >= 9)),
        ("C4. Tokens: mean ≤ 750, max ≤ 1000, refused = 0", "all three",
         runs(lambda t: f"{t['c4_mean_tokens']} / {t['c4_max_tokens']} / {t['c4_refused_free']}of5"),
         verdict(trials, lambda t: t["c4_mean_tokens"] is not None and t["c4_mean_tokens"] <= 750
                 and t["c4_max_tokens"] <= 1000 and t["c4_refused_free"] == 5)),
        ("C5. Answers unchanged (unit 1 questions)", "≥ 9 of 10",
         runs(lambda t: f"{t['c5']}/10"),
         verdict(trials, lambda t: t["c5"] >= 9)),
    ]

    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
    out = ROOT / "results" / f"capstone_{stamp}{'_' + args.label if args.label else ''}.md"
    lines = [f"# Capstone run log{' — ' + args.label if args.label else ''}", "",
             "- Produced by: `tools/measure.py::main` (scores read from `logs/requests.jsonl`, "
             "written by `serve.py::_log_request`)",
             f"- {args.trials} trials, each a fresh gunicorn start · "
             f"{dt.datetime.now().strftime('%Y-%m-%d %H:%M')}", "",
             "| Criterion | Target | " + " | ".join(f"Run {t['trial']}" for t in trials) + " | Verdict |",
             "|---|---|" + "---|" * len(trials) + "---|"]
    for name, target, cells, v in rows:
        lines.append(f"| {name} | {target} | {cells} | {v} |")
    lines += ["", "## Per-trial detail", ""]
    for t in trials:
        lines += [f"### Trial {t['trial']}", "",
                  f"- cold start (warm-up request): {t['cold_start_ms']} ms",
                  f"- records written: {t['records_written']} (21 requests incl. warm-up)",
                  f"- in-scope durations ms: {t['durations_ms']}",
                  f"- retrieval ms: {t['retrieval_ms']}",
                  f"- generation ms: {t['generation_ms']}",
                  f"- malformed: " + ", ".join(f"{s['sent']}→{s['status']}"
                                                for s in t["sent"] if s["kind"] == "malformed"),
                  f"- C5: " + ", ".join(f"{'✓' if d['ok'] else '✗'} {d['q'][:40]}" for d in t["c5_detail"]),
                  "", "```json",
                  json.dumps([s["record"] for s in t["sent"]], indent=1, ensure_ascii=False),
                  "```", ""]
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print("\n" + "\n".join(lines[5:12]))
    print(f"\nWrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
