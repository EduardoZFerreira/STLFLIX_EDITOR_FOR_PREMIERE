"""Print transcript segments, marking stretched words (possible hidden repetitions) with ⚠.
Usage: python ler.py <transcript.json> [max_word_seconds=0.8]"""
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
lim = float(sys.argv[2]) if len(sys.argv) > 2 else 0.8
words = d["words"]
for s in d["segments"]:
    ws = [w for w in words if s["start"] - 0.01 <= w["start"] < s["end"] - 0.01]
    txt = " ".join(f"{w['text']}⚠{w['end'] - w['start']:.1f}s" if w["end"] - w["start"] > lim else w["text"] for w in ws)
    print(f"[{s['start']:7.2f}-{s['end']:7.2f}] {txt or s['text']}")
