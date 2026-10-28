"""Sync the HyperFrames lettering .movs to Sequence 01 using plano-de-cenas.md trigger lines and the
timeline transcript (word times mapped through every V1 clip).

Usage: python letterings.py plan     -> table: scene, matched words, timeline in/out, fit/trim, confidence
       python letterings.py apply    -> clear the .movs from V1, place them on V2 at scale 200 (LA7 reused)
"""
import difflib, json, os, re, sys, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fc import FC

T, FRAME = 254_016_000_000, 10_594_584_000
FPS = 24000 / 1001
HERE = os.path.dirname(os.path.abspath(__file__))
PLAN = r"C:\Users\joaop\OneDrive\Desktop\Hyperframes\videos\vsl-black-november\plano-de-cenas.md"
MEDIA_TR = {1: "C2351", 2: "C2345", 3: "C2346", 4: "C2347", 5: "C2348", 6: "C2349"}
# anchors where the spoken line differs from the copy, or where the copy's first words are ambiguous
OVERRIDE = {
    "LB2": "tem gente vendendo impressao 3d para milhoes", "S01": "meu nome e hugo lopes",
    "S06": "o stl seller para saber o que vender", "S07": "o questionamento que mais chega ate a gente",
    "S10": "a primeira imagem que vem na cabeca", "S10B": "e isso que a pessoa comum compra",
    "S11": "ninguem procura vaso impresso", "S12": "o richard 1 dos nossos alunos",
    "S21": "no arena quem foi por esse caminho foi o luan", "S26": "o leonardo aluno do nosso curso de marketplace",
    "S30": "o lincoln 1 dos fundadores", "S31": "e o comeco foi dificil para ele", "S35": "o petare que vende",
    "S37": "esse caminho e o tiktok shop a loja", "S43": "a ana mentorada do elite 3d",
    "S46": "sao a michelle 1 das mentoras", "S48": "tem tambem o caso do emerson",
    "S49": "agora voce conhece os 4 caminhos", "S51": "lembra das 4 respostas que eu te falei",
    "S52": "nessa black november", "S53": "a primeira resposta o que vender", "S54": "a segunda resposta por quanto vender",
    "S55": "e as duas ultimas respostas onde vender", "S56": "e alem desses 4 cursos voce ainda leva",
    "S57": "normalmente todas essas plataformas funcionam", "S58": "ou seja voce paga 1 vez e o acesso e seu",
    "S59": "o sucesso de cada aluno alimenta", "S60": "se voce hoje comprar cada 1 dos servicos",
    "S61": "mas nessa black voce nao vai pagar", "S62": "ter 1 referencia do que esse valor representa",
    "S63": "e tem mais esses 4 997 reais voltam", "S64": "ao todo sao 334 cupons",
    "S65": "ou seja o filamento das suas proximas pecas", "S66": "que essa oferta ela tem 1 limite",
    "S67": "e quando eles acabarem a oferta", "S68": "entao vamos recapitular agora", "S69": "voce pode clicar no botao",
    "LB5": "no arena 3d o reality", "S39": "na primeira live ele passou 1 hora",
    "S42": "como frete gratis cupom de desconto",
}
LA7_ANCHOR = "os 4 caminhos que existem hoje para"
LEAD_IN = 0.2           # scene starts this long before the first matched word
FADE = 0.5              # last part of each .mov is the fade-out: kept when a scene must be shortened
GAP = 0.1               # breathing room between two scenes
NUM = {"um": "1", "uma": "1", "dois": "2", "duas": "2", "tres": "3", "quatro": "4", "cinco": "5", "seis": "6",
       "sete": "7", "oito": "8", "nove": "9", "dez": "10", "treze": "13", "setenta": "70", "cem": "100", "pra": "para",
       "pro": "para", "pros": "para", "pras": "para", "steliflix": "stlflix", "stelflix": "stlflix", "stereflix": "stlflix",
       "steleflix": "stlflix", "thales": "tales", "igor": "higor"}


def norm(text):
    t = unicodedata.normalize("NFKD", text.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.replace("stl flix", "stlflix").replace("r$", " ")
    toks = re.findall(r"[a-z0-9]+", t)
    return [NUM.get(x, x) for x in toks]


def timeline_words(seq):
    words = []
    v1 = [i for t in seq["video"] if t["name"] == "Video 1" for i in t["items"] if i["item"] in MEDIA_TR]
    cache = {}
    for c in v1:
        name = MEDIA_TR[c["item"]]
        if name not in cache:
            cache[name] = json.load(open(os.path.join(HERE, f"{name}.transcript.json"), encoding="utf-8"))["words"]
        a, b = c["sourceIn"] / T, c["sourceOut"] / T
        for w in cache[name]:
            if a - 0.05 <= w["start"] and w["end"] <= b + 0.1:
                t0 = c["start"] / T + (w["start"] - a)
                for tok in norm(w["text"]):
                    words.append((tok, max(t0, c["start"] / T)))
    words.sort(key=lambda x: x[1])
    return words


def scenes_from_plan():
    out = []
    for line in open(PLAN, encoding="utf-8"):
        m = re.match(r"\*\*([A-Z]{1,2}\d+B?) · [^*]*\*\* — \"(.+?)\"", line.strip())
        if m:
            code, quote = m.groups()
            out.append((code, quote))
    return out


def find(tokens, anchor, cursor, window=700):
    """Best fuzzy match of the anchor tokens in tokens[cursor:cursor+window]; earliest among near-best."""
    a = " ".join(anchor)
    best = []
    for i in range(cursor, min(len(tokens), cursor + window)):
        cand = " ".join(t for t, _ in tokens[i:i + len(anchor)])
        r = difflib.SequenceMatcher(None, a, cand).ratio()
        best.append((r, i))
    if not best:
        return None, 0.0
    top = max(r for r, _ in best)
    i = min(i for r, i in best if r >= max(top - 0.03, 0.0))
    return i, top


def build_plan(fc):
    seq = fc.run("sequence.inspect")
    tokens = timeline_words(seq)
    # the lettering .movs come from the Project panel (they may or may not still sit on the timeline)
    on_tl = {i["item"]: i["clip"] for t in seq["video"] for i in t["items"] if i["name"].lower().endswith(".mov")}
    proj = fc.run("project.inspect") if False else None
    import subprocess
    tree = json.loads(subprocess.run([r"C:\Program Files\FilmCraft\filmcraft-cli.exe", "--bridge", "127.0.0.1:9876",
                                      "--compact", "inspect", "project"], capture_output=True, text=True,
                                     encoding="utf-8").stdout)["root"]
    def walk(n):
        for c in n.get("children", []):
            yield c
            yield from walk(c)
    movs = {}
    for c in walk(tree):
        if str(c.get("name", "")).lower().endswith(".mov"):
            code = c["name"].split("-")[0]
            movs[code] = {"clip": on_tl.get(c["item"]), "item": c["item"], "dur": c["duration"] / T, "name": c["name"]}
    quotes = dict(scenes_from_plan())
    codes = sorted(movs, key=lambda c: ({"L": 0, "S": 1}[c[0]], c[:2] if c[0] == "L" else "",
                                         int(re.sub(r"[^0-9]", "", c)), c.endswith("B")))
    order = []
    for code in codes:
        order.append((code, quotes.get(code, ""), ""))
        if code in ("LB7", "LC7"):  # LA7 ('4 caminhos') closes all three leads
            order.append(("LA7", "", f"reuso no fim do Lead {code[1]}"))
    plan, cursor = [], 0
    for code, quote, note in order:
        first = OVERRIDE.get(code) or (LA7_ANCHOR if code == "LA7" else quote.replace("…", " "))
        anchor = norm(first)[:8]
        i, score = find(tokens, anchor, cursor)
        if i is None:
            plan.append({"code": code, "note": note, "missing": True}); continue
        start = max(0.0, tokens[i][1] - LEAD_IN)
        plan.append({"code": code, "quote": first, "heard": " ".join(t for t, _ in tokens[i:i + len(anchor)]),
                     "start": start, "score": score, "note": note, **movs[code]})
        cursor = i + 1
    for k, p in enumerate(plan):
        if p.get("missing"):
            continue
        nxt = next((q for q in plan[k + 1:] if not q.get("missing")), None)
        room = (nxt["start"] - GAP - p["start"]) if nxt else p["dur"]
        p["len"] = min(p["dur"], room)
        p["trim"] = p["len"] < p["dur"] - 1e-6
    return plan


def fmt(s):
    return f"{int(s // 60)}:{s % 60:05.2f}"


if __name__ == "__main__":
    fc = FC()
    P = build_plan(fc)
    if sys.argv[1] == "plan":
        for p in P:
            if p.get("missing"):
                print(f"{p['code']:5s} ✗ não encontrada"); continue
            flag = "⚠" if p["score"] < 0.7 else " "
            fit = f"encurtada {p['dur']:.0f}s→{p['len']:.1f}s" if p["trim"] else f"inteira {p['dur']:.0f}s"
            print(f"{flag}{p['code']:5s} {fmt(p['start'])}  {fit:24s} conf {p['score']:.2f} | copy: {p['quote'][:45]!r} | fala: {p['heard'][:45]!r} {p['note']}")
        print(f"{len(P)} cenas · encurtadas: {sum(1 for p in P if p.get('trim'))} · baixa confiança: {sum(1 for p in P if p.get('score', 1) < 0.7)}")
        sys.exit()

    # apply
    old = sorted({p["clip"] for p in P if not p.get("missing") and p.get("clip")})
    if old:
        fc.run("edit.clear", clips=old)
    placed = []
    for p in P:
        if p.get("missing") or p["len"] < 1.0:
            continue
        pos = round(p["start"] * FPS)
        segs = [(0.0, p["len"])] if not p["trim"] else [(0.0, p["len"] - FADE), (p["dur"] - FADE, p["dur"])]
        for a, b in segs:
            n = max(1, round((b - a) * FPS))
            r = fc.run("timeline.place", item=p["item"], track="V2", time=pos * FRAME, sourceIn=round(a * T),
                       duration=n * FRAME, insert=False, audio=False)
            placed += r["clips"]
            pos += n
    v2 = [i for t in fc.run("sequence.inspect")["video"] if t["name"] == "Video 2" for i in t["items"]]
    for c in v2:
        mi = [e["effect"] for e in c["effects"]].index("motion")
        fc.run("effects.setParam", clip=c["clip"], effect=mi, param="scale", value=200)
    print(f"V2: {len(v2)} clipes de lettering colocados em escala 200 ({len([p for p in P if not p.get('missing')])} cenas)")
