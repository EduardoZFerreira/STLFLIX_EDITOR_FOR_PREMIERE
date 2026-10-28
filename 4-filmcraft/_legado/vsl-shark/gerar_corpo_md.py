"""Transcript of the VSL-Shark body sequence, split into the teleprompter's blocks (Bloco 2..30).
Each block is located by fuzzy-matching the first words of its text in the Whisper transcript, in order; for the
offer blocks the full and the short (Parte 3) versions are both tried. Lines carry the take and its raw time.
Usage: python gerar_corpo_md.py <out.md>   (env CORPO_TR / CORPO_CLIPS pick another sequence's transcript and clip map)
"""
import difflib, json, os, re, sys, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = r"G:\Drives compartilhados\GROWTH 2026\1. Campanhas\[BRA] Brasil\[BRA] Black Friday 2026\VSLs\682_[BLACK26]\Copy\VSL BLACK NOVEMBER 2026 · TELEPROMP.txt"
# where the recorded line opens differently from the teleprompter copy
ANCHOR = {7: "olha o leonardo de criciuma", 29: "agora quanto tenho que investir"}
# spellings as in the teleprompter (Whisper writes these names several ways)
FIX = [(r"\bSt[ea]l+i?e?\s?[Ff]li[xc]k?s?\b|\bSTL\s?[Ff]lix\b|\bSTLFLIX\b", "STLflix"), (r"\besse Netflix\b", "a STLflix"),
       (r"\bNetflix\b", "STLflix"), (r"\bSTLA\b|\bSTL IA\b", "STLIA"), (r"\bThales\b", "Tales"), (r"\bLuana\b", "Luan"),
       (r"\btria completa\b", "trilha completa"), (r"\bFusio 360\b", "Fusion 360"), (r"\bSTL [Ss]eller\b", "STL Seller"),
       (r"\bHigor\b", "Igor"), (r"\bPetare?\b", "Petar"), (r"\bUnique ?[Bb]ox\b", "UniqueBox")]
NUM = {"um": "1", "uma": "1", "dois": "2", "duas": "2", "tres": "3", "quatro": "4", "cinco": "5", "seis": "6",
       "sete": "7", "oito": "8", "nove": "9", "dez": "10", "pra": "para", "pro": "para", "stlflix": "stlflix"}


def norm(text):
    t = unicodedata.normalize("NFKD", text.lower())
    t = "".join(c for c in t if not unicodedata.combining(c)).replace("r$", " ").replace("stl flix", "stlflix")
    return [NUM.get(x, x) for x in re.findall(r"[a-z0-9]+", t)]


def blocks():
    """[(number, title, first spoken words, part)] from the teleprompter; skips '→' stage directions."""
    out, cur, part = [], None, ""
    for raw in open(SCRIPT, encoding="utf-8"):
        line = raw.strip()
        if line.startswith("PARTE"):
            part = line
        m = re.match(r"--- BLOCO (\d+)( CURTO)? · (.+?) ---$", line)
        if m:
            cur = dict(n=int(m.group(1)), short=bool(m.group(2)), title=m.group(3), text="", part=part)
            out.append(cur)
            continue
        if cur is not None and line and not line.startswith(("→", "=", "---", "PARTE", "INSERÇÃO")) and len(cur["text"]) < 400:
            if not re.fullmatch(r"[A-ZÁÉÍÓÚÂÊÔÃÕÇ0-9 ·:,—–\-]{5,}", line):
                cur["text"] += " " + line
    return [b for b in out if "PARTE 1" not in b["part"]]


def find(tokens, anchor, cursor):
    a = " ".join(anchor)
    best = (0.0, None)
    for i in range(cursor, len(tokens)):
        r = difflib.SequenceMatcher(None, a, " ".join(t for t, _ in tokens[i:i + len(anchor)])).ratio()
        if r > best[0] + 1e-9:
            best = (r, i)
    return best


def mmss(s, dec=True):
    if dec:
        d = round(s * 10)                                  # round first so 59.96 s never prints as ":60.0"
        return f"{d // 600:02d}:{d % 600 / 10:04.1f}"
    return f"{int(s // 3600):02d}:{int(s // 60) % 60:02d}:{int(s % 60):02d}"


tr = json.load(open(os.path.join(HERE, os.environ.get("CORPO_TR", "Corpo.json")), encoding="utf-8"))
cl = json.load(open(os.path.join(HERE, os.environ.get("CORPO_CLIPS", "corpo_clips.json")), encoding="utf-8"))
tokens = [(tok, w["start"]) for w in tr["words"] for tok in norm(w["text"])]
found, cursor = [], 0
for b in blocks():
    anchor = norm(ANCHOR.get(b["n"]) if not b["short"] and b["n"] in ANCHOR else b["text"])[:9]
    if not anchor:
        continue
    extra = b["short"] or b["part"] == "extra"          # alternates/inserts: search the whole body
    score, i = find(tokens, anchor, 0 if extra else cursor)
    if i is not None and score >= 0.72:
        prev = next((f for f in found if f["n"] == b["n"]), None)
        # short vs full version of the same block: keep the better match; on a tie (same opening line) the short
        # version wins when CORPO_CURTO=1 (the short cut uses the Parte 3 takes)
        prefer_short = os.environ.get("CORPO_CURTO") == "1" and b["short"]
        if prev and (prev["score"] > score + 0.02 or (prev["score"] >= score and not prefer_short)):
            continue
        if prev:
            found.remove(prev)
        found.append(dict(n=b["n"], title=b["title"] + (" (versão curta)" if b["short"] else ""), t=tokens[i][1], score=score))
        if not extra:
            cursor = i + 1
    else:
        print(f"Bloco {b['n']}{' curto' if b['short'] else ''} · {b['title']}: não encontrado no corpo (melhor {score:.2f})")
found.sort(key=lambda f: f["t"])
found[0]["t"] = 0.0


def src_of(t):
    c = next((c for c in cl["clips"] if c["start"] - 0.05 <= t < c["start"] + c["dur"]), cl["clips"][-1])
    return c["take"].split(".")[0], c["src_in"] + max(0.0, t - c["start"])


out = [f"# Transcrição — {cl['sequence']} (VSL-Shark)", "",
       f"Sequência \"{cl['sequence']}\" ({mmss(cl['duration'])}, {len(cl['clips'])} cortes). Tempos = posição na sequência "
       "(mm:ss.d); entre parênteses, o take e o tempo no bruto. Blocos conforme o teleprompter (Copy/VSL BLACK NOVEMBER 2026 · "
       "TELEPROMP.txt), localizados pela fala. Fonte: Whisper large-v3-turbo sobre o áudio da sequência (A1).", ""]
for k, f in enumerate(found):
    end = found[k + 1]["t"] if k + 1 < len(found) else 1e9
    head = f"BLOCO {f['n']} · {f['title']}" if f["n"] else f["title"]
    out += [f"## {head}  ·  {mmss(f['t'])}", ""]
    for s in tr["segments"]:
        mid = s["start"] + 0.05
        if f["t"] - 0.3 <= mid < end - 0.3:
            take, st = src_of(s["start"])
            txt = s["text"].strip()
            for a, b in FIX:
                txt = re.sub(a, b, txt)
            out.append(f"- **{mmss(s['start'])}** {txt}  _({take} {mmss(st, dec=False)})_")
    out.append("")
open(sys.argv[1], "w", encoding="utf-8").write("\n".join(out))
for f in found:
    print(f"{mmss(f['t'])}  Bloco {f['n']:2d} · {f['title'][:50]:50s} conf {f['score']:.2f}")
print(sum(1 for l in out if l.startswith("- **")), "falas")
