#!/usr/bin/env python3
"""
The Unofficial Guide — the same pipeline, over HTTP.

    python serve.py                          run it locally on port 5000
    gunicorn serve:app                       run it the way a host runs it

Nothing new happens in this file. It is a wrapper: a request comes in, it
hands the question to `app.py::ask_pipeline` — the exact function the command
line uses — and hands the answer back as JSON. Retrieval, the relevance gate
and the grounded prompt all still live where they lived. If you change how
your system answers, you change it in those files and this one follows.

Two routes:

    POST /ask       {"question": "..."} in, the answer and its sources out
    GET  /health    is the service up, and is there an index to search

Why this exists: `app.py` runs once and exits, which is fine on your laptop
and impossible to deploy. A hosted service has to stay up and wait for
requests. This is the smallest thing that does that.

Unit 9 (capstone): every request to /ask now writes one structured record
to logs/requests.jsonl — what came in, what went out, how long it took and
where the time went, and the tokens the model reported. Failures write a
record too. See `_log_request` for the fields; README "Instrumentation".
"""

import json
import os
import threading
import time
import uuid
from datetime import datetime, timezone

from flask import Flask, g, jsonify, request

import config

app = Flask(__name__)

REQUEST_LOG = config.ROOT / "logs" / "requests.jsonl"
_log_lock = threading.Lock()
QUESTION_LOG_CHARS = 500   # a 1 MB question shouldn't make a 1 MB log line


def _log_request(record: dict) -> None:
    """Append one request record as a JSON line. Never breaks the request."""
    try:
        REQUEST_LOG.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(record, ensure_ascii=False)
        with _log_lock:
            with REQUEST_LOG.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
    except Exception:  # noqa: BLE001 — logging never takes the service down
        pass


def _base_record(status: int, outcome: str) -> dict:
    """The fields every record has, whatever happened."""
    question = getattr(g, "question", None)
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "request_id": getattr(g, "request_id", None),
        "route": request.path,
        "status": status,
        "outcome": outcome,              # answered | refused | rejected | error
        "question": question[:QUESTION_LOG_CHARS] if isinstance(question, str) else None,
        "question_chars": len(question) if isinstance(question, str) else None,
        "duration_ms": round((time.perf_counter() - g.t0) * 1000, 1) if hasattr(g, "t0") else None,
        "corpus": config.CORPUS,
        "model": config.MODEL,
    }


@app.before_request
def _start_clock():
    g.t0 = time.perf_counter()
    g.request_id = uuid.uuid4().hex[:12]


@app.errorhandler(Exception)
def _unhandled(exc):
    """
    Anything the route didn't catch. Without this, Flask answers with an HTML
    error page and nothing is written anywhere — a failure that shows up only
    as an absence.
    """
    from werkzeug.exceptions import HTTPException

    status = exc.code if isinstance(exc, HTTPException) else 500
    record = _base_record(status, "error")
    record.update({"error_type": type(exc).__name__, "error": str(exc)[:500]})
    if request.path == "/ask":
        _log_request(record)
    return jsonify({"error": f"{type(exc).__name__}: {exc}",
                    "request_id": record["request_id"]}), status


@app.get("/health")
def health():
    """Is the service up, and is there an index to search?

    Two different questions, and the second one is the one that bites. A
    freshly deployed service answers this route happily while every /ask
    returns "no index" — hosts give you no disk that survives a restart, so
    the index has to be built as part of getting the service up. Checking
    here means you find that out in one request instead of five.
    """
    from store import index_exists

    ready = index_exists(config.CORPUS)
    return jsonify(
        {
            "status": "ok",
            "corpus": config.CORPUS,
            "index_ready": ready,
            "detail": (
                "ready"
                if ready
                else "no index for this corpus — run `python app.py index`"
            ),
        }
    )


@app.post("/ask")
def ask():
    """One question in, one grounded answer out.

    A refused question is a 200, not an error. The gate refusing is your
    system working — it is an answer, and the JSON says so with
    `"refused": true` so whatever calls this can tell the two apart.
    """
    from app import ask_pipeline
    import generate

    # Capstone improvement: check the SHAPE of the input before touching it.
    # Before this, a JSON list (`.get` on a list) or a non-string question
    # (`.strip()` on an int) raised AttributeError here and came back as a 500.
    payload = request.get_json(silent=True)
    if payload is None:
        payload = {}
    problem = None
    if not isinstance(payload, dict):
        problem = ("body_not_object", "the request body must be a JSON object")
        question = ""
    else:
        raw = payload.get("question")
        if raw is not None and not isinstance(raw, str):
            problem = ("question_not_string", "'question' must be a string")
            question = ""
        else:
            question = (raw or "").strip()
            if not question:
                problem = ("empty_question", "no question in the request body")
    g.question = question

    if problem:
        record = _base_record(400, "rejected")
        record.update({"error_type": problem[0], "error": problem[1]})
        _log_request(record)
        return (
            jsonify(
                {
                    "error": "Send JSON with a question in it, like "
                    '{"question": "is the housing lottery random?"}',
                    "request_id": g.request_id,
                }
            ),
            400,
        )

    # Per-request numbers come from differences in generate.py's session
    # counters. Safe because gunicorn runs one sync worker with one thread
    # (RUNNING.md); with threads these deltas would bleed between requests.
    tokens_before = generate.token_counts()
    calls_before = generate.call_count()
    cache_before = generate._cache_hits
    marks = {}

    def on_gate(decision):
        marks["gate"] = time.perf_counter()   # retrieval + gate are done here

    try:
        outcome = ask_pipeline(question, corpus=config.CORPUS, on_gate=on_gate)
    except Exception as exc:  # noqa: BLE001 — a reader gets this, not a traceback
        record = _base_record(500, "error")
        record.update({
            "error_type": type(exc).__name__,
            "error": str(exc)[:500],
            "retrieval_ms": round((marks["gate"] - g.t0) * 1000, 1) if "gate" in marks else None,
            "model_calls": generate.call_count() - calls_before,
        })
        _log_request(record)
        return jsonify({"error": f"{type(exc).__name__}: {exc}", "request_id": g.request_id}), 500

    end = time.perf_counter()
    tokens_after = generate.token_counts()
    gate_at = marks.get("gate", end)

    record = _base_record(200, "refused" if outcome["refused"] else "answered")
    record.update({
        "answer": outcome["answer"],
        "answer_chars": len(outcome["answer"] or ""),
        "refused": outcome["refused"],
        "best_distance": round(outcome["best_distance"], 4),
        "threshold": outcome["threshold"],
        "sources": outcome["sources"],
        "retrieval_ms": round((gate_at - g.t0) * 1000, 1),
        "generation_ms": round((end - gate_at) * 1000, 1),
        "model_calls": generate.call_count() - calls_before,
        "cache_hit": generate._cache_hits > cache_before,
        "prompt_tokens": tokens_after["prompt"] - tokens_before["prompt"],
        "output_tokens": tokens_after["output"] - tokens_before["output"],
        "total_tokens": tokens_after["total"] - tokens_before["total"],
    })
    _log_request(record)

    return jsonify(
        {
            "question": question,
            "answer": outcome["answer"],
            "refused": outcome["refused"],
            "sources": outcome["sources"],
            "best_distance": round(outcome["best_distance"], 4),
            "threshold": outcome["threshold"],
            "corpus": config.CORPUS,
            "request_id": g.request_id,
            "duration_ms": record["duration_ms"],
        }
    )


def main():
    # Hosts tell you which port to listen on through PORT, and they expect you
    # on 0.0.0.0. Binding 127.0.0.1 instead works perfectly on your laptop and
    # then answers nothing at all once deployed, because the host's router
    # can't reach a socket that only accepts connections from inside the
    # container. It is the single most common way a first deploy "succeeds"
    # and is unreachable.
    port = int(os.getenv("PORT", "5000"))

    # Debug mode reloads on save, which is handy, and prints a console that
    # runs arbitrary code, which is not something to leave switched on where
    # strangers can reach it. Off unless you ask for it.
    debug = os.getenv("AI201_DEBUG", "0") == "1"

    print(f"Serving The Unofficial Guide on http://localhost:{port}")
    print(f"Corpus: {config.CORPUS}    (Ctrl-C to stop)\n")
    print("Try it from another terminal:\n")
    print(f"  curl http://localhost:{port}/health")
    print(
        f"  curl -X POST http://localhost:{port}/ask \\\n"
        f"    -H 'Content-Type: application/json' \\\n"
        f"    -d '{{\"question\": \"is the housing lottery random?\"}}'\n"
    )

    app.run(host="0.0.0.0", port=port, debug=debug)


if __name__ == "__main__":
    main()
