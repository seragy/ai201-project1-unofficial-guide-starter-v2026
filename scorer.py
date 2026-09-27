"""
Milestone-2 scorer for run_eval.py.

run_eval.py imports this module and calls exactly one function:
    judge(question, expects, answer, results) -> bool

Get the name or the arguments wrong and run_eval.py runs unscored —
no error, just blank Run columns.
"""


def judge(question: str, expects: str, answer: str, results) -> bool:
    """
    Crude substring check: does `expects` appear anywhere in the answer?

    This catches a MISSING fact (the phrase isn't there -> False, correctly).
    It cannot catch an ADDED, invented fact sitting next to a correct phrase
    -> that would still score True. Known limitation, not a bug to fix here.
    """
    return expects.strip().lower() in answer.strip().lower()