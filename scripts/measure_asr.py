"""Stage I speech-to-text baseline on CPU.

Voices each turn of demo/session_en.json with synthetic voices (Kokoro, offline),
transcribes it with Whisper base.en int8 (sherpa-onnx) on the CPU, and reports
word error rate and real-time factor. Writes demo/session_en_asr.json, which the
alert loop then consumes instead of the reference script.

Usage:
  python scripts/measure_asr.py --kokoro k.onnx --voices voices-v1.0.bin --whisper sherpa-onnx-whisper-base.en
"""
import argparse, json, re, time
import numpy as np
import sherpa_onnx
from kokoro_onnx import Kokoro

VOICE = {"M": ("bm_george", "en-gb"), "A": ("af_heart", "en-us"), "B": ("am_michael", "en-us")}


def norm(s: str) -> list[str]:
    return re.sub(r"[^a-z0-9' ]", " ", s.lower()).split()


def wer(ref: list[str], hyp: list[str]) -> int:
    d = list(range(len(hyp) + 1))
    for i, r in enumerate(ref, 1):
        prev, d[0] = d[0], i
        for j, h in enumerate(hyp, 1):
            cur = min(d[j] + 1, d[j - 1] + 1, prev + (r != h))
            prev, d[j] = d[j], cur
    return d[-1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kokoro", required=True); ap.add_argument("--voices", required=True)
    ap.add_argument("--whisper", required=True); ap.add_argument("--session", default="demo/session_en.json")
    ap.add_argument("--out", default="demo/session_en_asr.json")
    a = ap.parse_args()
    tts = Kokoro(a.kokoro, a.voices)
    w = a.whisper.rstrip("/")
    rec = sherpa_onnx.OfflineRecognizer.from_whisper(
        encoder=f"{w}/base.en-encoder.int8.onnx", decoder=f"{w}/base.en-decoder.int8.onnx",
        tokens=f"{w}/base.en-tokens.txt", language="en", task="transcribe", num_threads=4)
    rows = json.load(open(a.session, encoding="utf-8"))
    errs = words = 0; audio_s = asr_s = 0.0
    for r in rows:
        v, lang = VOICE[r["speaker"]]
        samples, sr = tts.create(r["text"], voice=v, speed=1.0, lang=lang)
        t0 = time.perf_counter()
        st = rec.create_stream(); st.accept_waveform(sr, np.asarray(samples, dtype=np.float32))
        rec.decode_stream(st)
        asr_s += time.perf_counter() - t0; audio_s += len(samples) / sr
        r["text_asr"] = st.result.text.strip()
        ref, hyp = norm(r["text"]), norm(r["text_asr"])
        errs += wer(ref, hyp); words += len(ref)
    json.dump(rows, open(a.out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"WER {errs / words:.1%} ({errs}/{words} words), "
          f"RTF {asr_s / audio_s:.2f} ({audio_s:.1f} s audio in {asr_s:.1f} s)")


if __name__ == "__main__":
    main()
