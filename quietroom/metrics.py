"""Conversation-dynamics metrics for QuietRoom.

Metrics describe the conversation, never a person's state.
No emotion inference of any kind.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import re

ESCALATION_PATTERNS = [
    r"\balways\b", r"\bnever\b", r"\bor else\b", r"\blast chance\b",
    r"\bsee you in court\b", r"\bnon-negotiable\b", r"\bfinal offer\b",
    r"\bi'?m done\b", r"\bwalk out\b", r"\bnothing to talk about\b",
]


@dataclass
class Turn:
    speaker: str
    start: float
    end: float
    text: str

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)

    @property
    def words(self) -> int:
        return len(self.text.split())


@dataclass
class Alert:
    t: float
    kind: str
    reason: str


@dataclass
class Config:
    interruption_window_s: float = 60.0
    interruption_streak: int = 3
    talk_share_floor: float = 0.20
    talk_share_window_s: float = 120.0
    wpm_rise_ratio: float = 1.35
    wpm_turns: int = 3


@dataclass
class SessionState:
    cfg: Config = field(default_factory=Config)
    turns: list[Turn] = field(default_factory=list)
    interruptions: list[tuple[float, str]] = field(default_factory=list)
    alerts: list[Alert] = field(default_factory=list)

    def add(self, turn: Turn) -> list[Alert]:
        new: list[Alert] = []
        prev = self.turns[-1] if self.turns else None
        self.turns.append(turn)
        if prev and prev.speaker != turn.speaker and turn.start < prev.end:
            self.interruptions.append((turn.start, turn.speaker))
            recent = [s for t, s in self.interruptions
                      if t >= turn.start - self.cfg.interruption_window_s and s == turn.speaker]
            if len(recent) >= self.cfg.interruption_streak:
                new.append(Alert(turn.start, "interruptions",
                                 f"{len(recent)} interruptions by speaker {turn.speaker} "
                                 f"in {int(self.cfg.interruption_window_s)} s"))
        new += self._talk_share(turn.end)
        new += self._wpm(turn)
        for pat in ESCALATION_PATTERNS:
            m = re.search(pat, turn.text, re.IGNORECASE)
            if m:
                new.append(Alert(turn.start, "phrase",
                                 f"escalation phrase \"{m.group(0)}\" (speaker {turn.speaker})"))
                break
        self.alerts += new
        return new

    def talk_time(self, since: float = 0.0) -> dict[str, float]:
        out: dict[str, float] = {}
        for t in self.turns:
            if t.end >= since:
                out[t.speaker] = out.get(t.speaker, 0.0) + t.duration
        return out

    def _talk_share(self, now: float) -> list[Alert]:
        if now < self.cfg.talk_share_window_s:
            return []
        tt = self.talk_time(now - self.cfg.talk_share_window_s)
        parties = {s: v for s, v in tt.items() if s != "M"}  # M = mediator
        total = sum(parties.values())
        if total <= 0 or len(parties) < 2:
            return []
        out = []
        for s, v in parties.items():
            share = v / total
            already = any(a.kind == "talk_share" and s in a.reason and now - a.t < 60
                          for a in self.alerts)
            if share < self.cfg.talk_share_floor and not already:
                out.append(Alert(now, "talk_share",
                                 f"speaker {s} share of party talk time {share:.0%} "
                                 f"in last {int(self.cfg.talk_share_window_s)} s"))
        return out

    def _wpm(self, turn: Turn) -> list[Alert]:
        own = [t for t in self.turns if t.speaker == turn.speaker and t.duration > 1]
        n = self.cfg.wpm_turns
        if len(own) < 2 * n:
            return []
        rate = lambda ts: sum(t.words for t in ts) / (sum(t.duration for t in ts) / 60)
        early, late = rate(own[:n]), rate(own[-n:])
        if late >= early * self.cfg.wpm_rise_ratio:
            if not any(a.kind == "wpm" and turn.speaker in a.reason for a in self.alerts):
                return [Alert(turn.start, "wpm",
                              f"speaker {turn.speaker} speech rate {early:.0f} -> {late:.0f} wpm")]
        return []
