import json
from quietroom.metrics import SessionState, Turn
from quietroom.summary import draft

def load():
    return [Turn(**t) for t in json.load(open("demo/session_en.json"))]

def test_interruption_alert_names_reason():
    st = SessionState()
    for t in load():
        st.add(t)
    kinds = [a.kind for a in st.alerts]
    assert "interruptions" in kinds
    assert any("speaker B" in a.reason for a in st.alerts if a.kind == "interruptions")

def test_no_emotion_labels():
    st = SessionState()
    for t in load():
        st.add(t)
    banned = ("angry", "anger", "fear", "sad", "emotion", "lying", "credib")
    assert not any(b in a.reason.lower() for a in st.alerts for b in banned)

def test_draft():
    d = draft(load())
    assert d["agreed"] and d["open"]
    assert d["confirmed_by"] == ["A", "B"]
