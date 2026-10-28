"""VSL-Shark: sync the lead motions (HyperFrames ProRes 4444, 1080x1920) to the 'Lead A'..'Lead G' sequences and
reframe the camera takes there.

Each motion starts LEAD_IN s before the first word of its anchor line (word times from the Whisper transcript
of that sequence, shark/Lead_X.json). When it would run into the next motion it is shortened like the VSL-Hugo
letterings: the head is kept and the last FADE s (fade-out) are appended. Motions go on V2 at scale 200.
Camera clips (V1) get the user's Lead A framing: scale 114, anchor y 1900.

Usage: python motions_leads.py plan                 -> table per lead (no app needed)
       python motions_leads.py apply [Lead A ...]   -> live app (filmcraft --control 9876)
"""
import difflib, json, os, re, sys, unicodedata
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

T, FRAME, FPS = 254_016_000_000, 10_594_584_000, 24000 / 1001
HERE = os.path.dirname(os.path.abspath(__file__))
MOTION_DIR = r"G:\Drives compartilhados\GROWTH 2026\1. Campanhas\[BRA] Brasil\[BRA] Black Friday 2026\VSLs\682_[BLACK26]\Assets\Motion"
LEAD_IN, FADE, GAP = 0.2, 0.5, 0.1
TAKE_SCALE, TAKE_ANCHOR_Y = 114.0, 1900.0
# motion code -> first words of the line that triggers it
ANCHORS = {
    "A1": "4 em cada 10 pessoas", "A2": "porque nao sabem o que vender", "A3": "nao e falta de impressora",
    "A4": "entao a gente fez 1 teste", "A5": "1 delas nunca tinha vendido", "A6": "2 meses depois os 3",
    "A7": "e nesse video voce vai ver",
    "B1": "esse e o arena 3d", "B2": "3 pessoas sem impressora", "B3": "1 delas ja vivia de impressao",
    "B4": "2 meses e meio depois", "B5": "e nao e so no arena",
    "C1": "o emerson era motorista", "C2": "a camila e a jennifer trabalhavam", "C3": "o rafael e tecnico",
    "C4": "o ph e gerente", "C5": "nenhum deles largou tudo", "C6": "e hoje o emerson faz",
    "C7": "a camila e a jennifer fazem", "C8": "essa black friday nao e sobre desconto",
    "C9": "e sobre estar mais perto da sua familia",
    "D1": "a gente colocou tudo em jogo", "D2": "a gente botou 3 pessoas", "D3": "se eles nao conseguissem vender",
    "D4": "o arena ta no youtube", "D5": "empresa que todo dia mostra", "D6": "e nao foi facil",
    "D7": "2 meses e meio depois os 3", "D8": "e nesse video voce vai ver tudo",
    "E1": "quantos negocios que voce conhece", "E2": "em 6 8 10 meses", "E3": "o caio comecou",
    "E4": "o giovanni fatura", "E5": "michelle e o adriano comecaram", "E6": "o leonardo comecou por hobby",
    "E7": "1 negocio que comeca em casa", "E8": "e na arena 3d a gente foi mais longe",
    "E9": "essa black friday e sobre isso",
    "F1": "quanto custa montar 1 empresa", "F2": "compara com 1 micro franquia", "F3": "com a impressao 3d o investimento",
    "F4": "para mim nao existe", "F5": "e 1 franquia que nao e micro", "F6": "o leonardo comprou na nossa",
    "F7": "essa black friday e sobre isso",
    "G1": "fracasso total", "G2": "foi isso que escreveram", "G3": "o cotrim estava na arena",
    "G4": "a gente grava e 2 semanas", "G5": "no comeco deu errado", "G6": "eu mesmo respondi",
    "G7": "2 meses e meio depois", "G8": "e nesse video voce vai ver",
}
NUM = {"um": "1", "uma": "1", "dois": "2", "duas": "2", "tres": "3", "quatro": "4", "seis": "6", "oito": "8",
       "dez": "10", "pra": "para", "pro": "para"}


def norm(text):
    t = unicodedata.normalize("NFKD", text.lower())
    t = "".join(c for c in t if not unicodedata.combining(c)).replace("r$", " ")
    return [NUM.get(x, x) for x in re.findall(r"[a-z0-9]+", t)]


def words_of(lead):
    tr = json.load(open(os.path.join(HERE, lead.replace(" ", "_") + ".json"), encoding="utf-8"))
    return [(tok, w["start"]) for w in tr["words"] for tok in norm(w["text"])]


def find(tokens, anchor, cursor):
    a = " ".join(anchor)
    best = [(difflib.SequenceMatcher(None, a, " ".join(t for t, _ in tokens[i:i + len(anchor)])).ratio(), i)
            for i in range(cursor, len(tokens))]
    if not best:
        return None, 0.0
    top = max(r for r, _ in best)
    return min(i for r, i in best if r >= top - 0.03), top


def motions():
    out = {}
    for line in open(os.path.join(HERE, "motions_dur.txt"), encoding="utf-8"):
        name, dur = line.strip().split("|")
        out[name.split("-")[0]] = (name, float(dur))
    return out


def plan(lead):
    letter = lead.split()[-1]
    mv = motions()
    codes = sorted((c for c in mv if c[0] == letter and c[1:].isdigit()), key=lambda c: int(c[1:]))
    tokens, cursor, P = words_of(lead), 0, []
    for code in codes:
        anchor = norm(ANCHORS[code])
        i, score = find(tokens, anchor, cursor)
        name, dur = mv[code]
        if i is None:
            P.append(dict(code=code, name=name, missing=True)); continue
        P.append(dict(code=code, name=name, dur=dur, start=max(0.0, tokens[i][1] - LEAD_IN), score=score,
                      heard=" ".join(t for t, _ in tokens[i:i + len(anchor)])))
        cursor = i + 1
    end = json.load(open(os.path.join(HERE, "leads.json"), encoding="utf-8"))[lead]["duration"]
    for k, p in enumerate(P):
        if p.get("missing"):
            continue
        nxt = next((q for q in P[k + 1:] if not q.get("missing")), None)
        room = (nxt["start"] - GAP - p["start"]) if nxt else (end - p["start"])   # the last one ends with the lead
        p["len"] = min(p["dur"], room)
        p["trim"] = p["len"] < p["dur"] - 1e-6
    return P


LEADS = [f"Lead {c}" for c in "ABCDEFG"]

if __name__ == "__main__":
    if sys.argv[1] == "plan":
        for lead in LEADS:
            dur = json.load(open(os.path.join(HERE, "leads.json"), encoding="utf-8"))[lead]["duration"]
            print(f"== {lead} ({dur:.1f}s)")
            for p in plan(lead):
                if p.get("missing"):
                    print(f"  {p['code']:3s} ✗ não encontrada"); continue
                fit = f"encurtado {p['dur']:.0f}s→{p['len']:.1f}s" if p["trim"] else f"inteiro {p['dur']:.0f}s"
                over = " ⚠ passa do fim" if p["start"] + p["len"] > dur + 0.5 else ""
                flag = "⚠" if p["score"] < 0.75 else " "
                print(f" {flag}{p['code']:3s} {p['start']:5.1f}s  {fit:22s} conf {p['score']:.2f} | {p['heard']}{over}")
        sys.exit()
    from fc import FC
    fc = FC()
    todo = [a for a in LEADS if not sys.argv[2:] or a in " ".join(sys.argv[2:])]
    tree = fc.run("project.inspect")["root"]

    def walk(n):
        for c in n.get("children", []):
            yield c
            yield from walk(c)
    seqs = {c["name"]: c["item"] for c in walk(tree) if c.get("type") == "Sequence"}
    have = {c["name"]: c["item"] for c in walk(tree) if str(c.get("name", "")).lower().endswith(".mov")}
    need = [os.path.join(MOTION_DIR, d, f) for d in os.listdir(MOTION_DIR) if d[:6] in [f"Lead {l[-1]}" for l in todo]
            and os.path.isdir(os.path.join(MOTION_DIR, d)) for f in os.listdir(os.path.join(MOTION_DIR, d))
            if f.endswith(".mov") and f not in have]
    if need:
        fc.run("file.import", paths=need)
        have = {c["name"]: c["item"] for c in walk(fc.run("project.inspect")["root"]) if str(c.get("name", "")).lower().endswith(".mov")}
        print(f"{len(need)} motions importados")
    for lead in todo:
        fc.run("sequence.open", item=seqs[lead])
        seq = fc.run("sequence.inspect")
        v2 = next((t for t in seq["video"] if t["name"] == "Video 2"), None)
        old = [c["clip"] for c in (v2["items"] if v2 else []) if c["name"].endswith(".mov")]
        if old:
            fc.run("edit.clear", clips=old)
        n_cl = 0
        for c in (c for t in seq["video"] if t["name"] == "Video 1" for c in t["items"] if c["name"].startswith("C23")):
            mi = [e["effect"] for e in c["effects"]].index("motion")
            fc.run("effects.setParam", clip=c["clip"], effect=mi, param="scale", value=TAKE_SCALE)
            fc.run("effects.setParam", clip=c["clip"], effect=mi, param="anchor", value=[1080.0, TAKE_ANCHOR_Y])
            n_cl += 1
        placed = []
        for p in plan(lead):
            if p.get("missing") or p["len"] < 1.0:
                continue
            pos = round(p["start"] * FPS)
            segs = [(0.0, p["len"])] if not p["trim"] else [(0.0, p["len"] - FADE), (p["dur"] - FADE, p["dur"])]
            for a, b in segs:
                n = max(1, round((b - a) * FPS))
                r = fc.run("timeline.place", item=have[p["name"]], track="V2", time=pos * FRAME, sourceIn=round(a * T),
                           duration=n * FRAME, insert=False, audio=False)
                placed += r["clips"]
                pos += n
        for c in (c for t in fc.run("sequence.inspect")["video"] for c in t["items"] if c["clip"] in placed):
            mi = [e["effect"] for e in c["effects"]].index("motion")
            fc.run("effects.setParam", clip=c["clip"], effect=mi, param="scale", value=200)
        print(f"{lead}: {n_cl} takes em escala {TAKE_SCALE:.0f} / âncora y {TAKE_ANCHOR_Y:.0f} · {len(placed)} clipes de motion na V2")
