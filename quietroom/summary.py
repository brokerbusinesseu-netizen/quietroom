"""Post-session draft of agreed and open points.

Stage I: rule-based extraction from the mediator's own summarising turns
(transparent, editable). Stage II: the same interface backed by a small
instruct model on UGen300. The mediator always edits and approves.
"""
import re
from .metrics import Turn

SUMMARY = re.compile(r"\b(so we agree|we agree|agreed)\b\s*:?\s*(.*)", re.I)
OPEN = re.compile(r"\b(still need|not yet|need to check|come back to|remains open|later)\b", re.I)
ACCEPT = re.compile(r"\b(i can accept|that works|agreed|we agree)\b", re.I)


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def draft(turns: list[Turn]) -> dict[str, list[str]]:
    agreed, open_ = [], []
    for t in turns:
        if t.speaker != "M":
            continue
        for s in _sentences(t.text):
            m = SUMMARY.search(s)
            if m and m.group(2):
                agreed.append(m.group(2).rstrip("."))
            elif OPEN.search(s):
                open_.append(s.rstrip("."))
    confirmed = sorted({t.speaker for t in turns if t.speaker != "M" and ACCEPT.search(t.text)})
    return {"agreed": agreed, "open": open_, "confirmed_by": confirmed}
