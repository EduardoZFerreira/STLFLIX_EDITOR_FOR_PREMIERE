"""Write the two transcripts the user asked for, from the live timeline:
  Transcricoes/Transcricao_Hugo_VSL.md   - Hugo's VSL (Sequence 01, camera clips), sentence lines with timeline time, by block
  Transcricoes/Transcricao_Brolls.md      - each B-roll: lines with source time + timeline time (or 'fora da timeline')
Also imports the B-roll transcripts into FilmCraft (transcript.set) so they can be searched in the app.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fc import FC

T = 254_016_000_000
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = r"C:\Users\joaop\OneDrive\Desktop\Filmcraft\Transcricoes"
CAM = {1: "C2351", 2: "C2345", 3: "C2346", 4: "C2347", 5: "C2348", 6: "C2349"}


def tc(s):
    d = int(round(max(0.0, s) * 10))          # tenths, rounded once (no 'mm:60.0')
    return f"{d // 600:02d}:{(d % 600) // 10:02d}.{d % 10}"


def clean(txt):
    import re
    txt = re.sub(r'R\s*\$\s*', 'R$ ', txt)
    txt = re.sub(r'(\d)\s+([.,]\d)', lambda m: m.group(1) + m.group(2), txt)
    txt = re.sub(r'\s+%', '%', txt)
    return re.sub(r'\s{2,}', ' ', txt).strip()


def lines_from(words, gap=0.7, max_words=22):
    """Group (text, t_start, t_end) words into readable lines (sentence end, pause, or length)."""
    out, cur = [], []
    for w in words:
        if cur and (w[1] - cur[-1][2] > gap or len(cur) >= max_words or
                    (cur[-1][0].endswith((".", "?", "!")) and len(cur) >= 4)):
            out.append(cur); cur = []
        cur.append(w)
    if cur:
        out.append(cur)
    return [(l[0][1], l[-1][2], clean(" ".join(x[0] for x in l))) for l in out]


fc = FC()
seq = fc.run("sequence.inspect")
v1 = [c for t in seq["video"] if t["name"] == "Video 1" for c in t["items"]]
os.makedirs(OUT, exist_ok=True)

# ---------------- Hugo (camera clips on V1)
cache = {}
words = []
for c in v1:
    if c["item"] not in CAM:
        continue
    name = CAM[c["item"]]
    if name not in cache:
        cache[name] = json.load(open(os.path.join(HERE, f"{name}.transcript.json"), encoding="utf-8"))["words"]
    a, b = c["sourceIn"] / T, c["sourceOut"] / T
    for w in cache[name]:
        if w["end"] > a + 0.1 and w["start"] < b - 0.1:   # at least 0.1 s of the word is inside the clip
            t0 = c["start"] / T + (w["start"] - a)
            words.append((w["text"], max(t0, c["start"] / T), c["start"] / T + (min(w["end"], b) - a)))
words.sort(key=lambda w: w[1])
hugo_end = max(c["end"] for c in v1 if c["item"] in CAM) / T
blocks = sorted([(m["start"] / T, m["name"]) for m in seq["markers"] if m.get("color") == "Blue"])
md = ["# Transcrição — Hugo (VSL montado na Sequence 01)", "",
      f"Tempos = posição na timeline (mm:ss.d). Duração do VSL: {tc(hugo_end)}. Fonte: Whisper large-v3-turbo sobre os takes usados (C2345–C2351).", ""]
bi = 0
for s, e, txt in lines_from(words):
    while bi < len(blocks) and blocks[bi][0] <= s + 0.3:
        md += ["", f"## {blocks[bi][1]}  ·  {tc(blocks[bi][0])}", ""]
        bi += 1
    md.append(f"- **{tc(s)}** {txt}")
open(os.path.join(OUT, "Transcricao_Hugo_VSL.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
print(f"Hugo: {len(words)} palavras, {len(blocks)} blocos")

# ---------------- B-rolls
status = {m["name"]: m["item"] for m in fc.run("media.status")}
paths = [l.split("|", 1)[1].strip() for l in open(os.path.join(HERE, "broll_paths.txt"), encoding="utf-8") if "|" in l]
order = ["Live TikTok Shop", "Higor - Chapada Diamantina", "Arena 3D EP 01 - Teaser", "Arena 3D - EP2",
         "Arena 3D - EP2 - STL Seller", "Arena 3D - EP3", "Arena 3D - EP5 - Kit Leão", "Arena 3D - EP7"]
md = ["# Transcrição — B-rolls", "",
      "Cada linha: **tempo no vídeo original** · (tempo na timeline, quando o trecho está nela). "
      "Trechos marcados *fora da timeline* foram cortados por você do bloco de B-roll.",
      "Fonte: Whisper large-v3-turbo. Os episódios têm várias vozes (Hugo, Cotrim, Luan, Tales, Lincoln…): a transcrição não separa quem fala.", ""]
for base in order:
    p = next(x for x in paths if os.path.basename(x)[:-4] == base)
    tr = json.load(open(os.path.join(HERE, "broll", "tr_" + base.replace(" ", "_") + ".json"), encoding="utf-8"))
    item = status[os.path.basename(p)]
    pieces = sorted([c for t in seq["video"] for c in t["items"] if c["item"] == item], key=lambda c: c["start"])
    def where(t):
        for c in pieces:
            a, b = c["sourceIn"] / T, c["sourceOut"] / T
            if a - 0.3 <= t < b:
                return c["start"] / T + (max(t, a) - a)
        return None
    md += ["", f"## {base}  ·  {tc(tr['duration'])}", ""]
    if pieces:
        md.append("Na timeline: " + "; ".join(f"{tc(c['sourceIn'] / T)}–{tc(c['sourceOut'] / T)} → {tc(c['start'] / T)}" for c in pieces))
    else:
        md.append("*Não está na timeline.*")
    md.append("")
    ws = [(w["text"], w["start"], w["end"]) for w in tr["words"] if w["text"]]
    if not ws:
        md.append("*(sem fala)*")
    for s, e, txt in lines_from(ws):
        tl = where(s)
        md.append(f"- **{tc(s)}** · " + (f"({tc(tl)})" if tl is not None else "*fora da timeline*") + f" {txt}")
    fc.run("transcript.set", item=item, transcript={"language": "pt", "speakers": [{"name": "Falante"}], "words": [
        {"text": w["text"], "start": round(w["start"] * T), "end": round(max(w["end"], w["start"]) * T), "speaker": 0}
        for w in tr["words"] if w["text"]]})
    print(f"{base}: {len(ws)} palavras, {len(pieces)} pedaço(s) na timeline")
open(os.path.join(OUT, "Transcricao_Brolls.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
print("arquivos em", OUT)
