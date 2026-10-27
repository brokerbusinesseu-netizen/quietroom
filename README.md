# QuietRoom

An offline co-pilot for mediators. Built for the ASUS UGen300 (Hailo-10H) USB AI accelerator.
ASUS UGen AI League 2026, Battlefield Lightning, Global Online Track. Team Archaios (solo).

**What is said in mediation stays in the room.** QuietRoom never sends audio, transcripts or summaries off the device.

## What it does

1. **Local transcription** with speaker turns (who spoke when; no voice identification of any person).
2. **Conversation-dynamics alerts, shown only to the mediator**, each with its reason:
   - interruption streaks ("3 interruptions by speaker B in 60 s"),
   - a party's share of talk time collapsing,
   - speech rate rising across a speaker's turns,
   - escalation phrases in the transcript (absolutes, ultimatums).
3. **Post-session draft** of agreed and open points, which the mediator edits and approves.

## What it deliberately does not do

No emotion recognition, no credibility scoring, no decisions. It describes the conversation, not the people
(EU AI Act art. 5(1)(f) and Annex III emotion recognition do not apply by design). Written consent of all
parties before recording; transcripts are deleted once the mediator approves the summary.

## Stage I prototype (this repository)

Pure Python 3.10+, no dependencies, runs on any laptop CPU. It replays a role-played, fictional
session (`demo/session_en.json`, English, no real parties) through the full alert and summary loop:

```
python -m quietroom.cli demo/session_en.json
python -m pytest -q
```

## Architecture

```
microphone -> host laptop (Windows/Linux)
               audio capture, voice activity, speaker turns, metrics (CPU)   <- quietroom/metrics.py
          -> UGen300 over USB-C (HailoRT, INT4)
               speech-to-text model, then a 1-2B instruct model (loaded sequentially if needed)
          -> local alert panel + local encrypted session folder              <- quietroom/summary.py interface
```

In Stage I, speech-to-text input is the scripted transcript and the summary is rule-based.
In Stage II (06.11-04.12) both are moved to UGen300 via HailoRT, with models chosen from those supported on Hailo-10H.

## Stage II plan and what we will measure

| Week | Work |
|---|---|
| 1 | HailoRT setup, speech-to-text on device, latency measurement |
| 2 | small instruct model on device for the agreed-points draft |
| 3 | alert panel, encrypted local storage, single installer |
| 4 | measurements, 10-minute final video, documentation |

Reported, including shortfalls: end-to-end transcript latency, alert latency, host CPU load with and without the
accelerator, laptop battery drain over a 2-hour session.

## Configuration

Thresholds live in `quietroom.metrics.Config` and are adjustable per session by the mediator.

## License

Apache-2.0. Contact: brokerbusinesseu@gmail.com
