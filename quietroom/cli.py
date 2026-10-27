"""Replay a session transcript (JSON) through QuietRoom, offline.

Usage: python -m quietroom.cli demo/session_en.json
"""
import json, sys
from .metrics import SessionState, Turn
from .summary import draft


def bar(tt: dict[str, float]) -> str:
    total = sum(v for s, v in tt.items() if s != "M") or 1
    return "  ".join(f"{s}:{v/total:4.0%}" for s, v in sorted(tt.items()) if s != "M")


def main(path: str) -> None:
    turns = [Turn(**t) for t in json.load(open(path, encoding="utf-8"))]
    st = SessionState()
    for t in turns:
        alerts = st.add(t)
        print(f"[{t.start:6.1f}s] {t.speaker}: {t.text}")
        for a in alerts:
            print(f"          ALERT {a.kind}: {a.reason}")
    print("\nTalk-time balance (parties):", bar(st.talk_time()))
    print("Interruptions:", len(st.interruptions))
    d = draft(turns)
    print("\nDRAFT FOR MEDIATOR REVIEW (nothing is sent anywhere)")
    print("Agreed:"); [print("  -", x) for x in d["agreed"]]
    print("Open:"); [print("  -", x) for x in d["open"]]
    print("Acceptance heard from:", ", ".join(d["confirmed_by"]) or "none")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "demo/session_en.json")
