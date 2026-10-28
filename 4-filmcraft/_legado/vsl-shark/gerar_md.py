"""Write the VSL-Shark leads transcript (Lead A..G) as Markdown, in the same layout as Transcricao_Hugo_VSL.md.
Times are positions inside each 'Lead X' sequence; each line also carries the source take and its time in the raw.
Usage: python gerar_md.py <out.md>
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TITLES = {"Lead A": "Objeção", "Lead B": "Arena", "Lead C": "Sem largar o emprego", "Lead D": "Arriscamos tudo",
          "Lead E": "Negócio de casa", "Lead F": "Franquia × impressão 3D", "Lead G": "Viramos chacota"}
FIX = [(r"\bvendou\b", "vendeu")]                         # Whisper slips checked against the audio
info = json.load(open(os.path.join(HERE, "leads.json"), encoding="utf-8"))


def mmss(s, dec=True):
    return f"{int(s // 60):02d}:{s % 60:04.1f}" if dec else f"{int(s // 3600):02d}:{int(s // 60) % 60:02d}:{int(s % 60):02d}"


def src_of(clips, t):
    c = next((c for c in clips if c["start"] - 0.05 <= t < c["start"] + c["dur"]), clips[-1])
    return c["take"].split(".")[0], c["src_in"] + max(0.0, t - c["start"])


out = ["# Transcrição — Leads A a G (VSL-Shark)", "",
       "Tempos = posição dentro de cada sequência \"Lead X\" do projeto VSL-Shark (mm:ss.d). Entre parênteses, o take "
       "e o tempo no bruto. Fonte: Whisper large-v3-turbo sobre o áudio montado de cada sequência (A1).", ""]
for name in sorted(info):
    d = info[name]
    tr = json.load(open(os.path.join(HERE, name.replace(" ", "_") + ".json"), encoding="utf-8"))
    out += [f"## {name.upper()} · {TITLES.get(name, '')}  ·  duração {mmss(d['duration'])}", ""]
    for s in tr["segments"]:
        txt = s["text"].strip()
        for a, b in FIX:
            txt = re.sub(a, b, txt)
        take, st = src_of(d["clips"], s["start"])
        out.append(f"- **{mmss(s['start'])}** {txt}  _({take} {mmss(st, dec=False)})_")
    notes = [m for m in d["markers"] if not m["name"].startswith("EMENDA") and m["name"].split(" ")[0] in ("R-LA4", "ALT-06", "R-LF1", "R-LF2", "ALT-05", "R-LD1", "R-LG1")]
    if notes:
        out += ["", "Marcadores de revisão nesta sequência:"]
        for m in notes:
            c = re.sub(r"\s*\[timecode no bruto:.*$", "", m["comment"].replace("\n", " ")).strip()
            out.append(f"- {mmss(m['t'])} · {m['name']}: {c}")
    out.append("")
open(sys.argv[1], "w", encoding="utf-8").write("\n".join(out))
print(sys.argv[1], sum(1 for l in out if l.startswith("- **")), "falas")
