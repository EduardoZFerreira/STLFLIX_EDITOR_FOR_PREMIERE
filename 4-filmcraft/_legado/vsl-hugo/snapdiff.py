"""Diff two sequence snapshots from snapshot.py. Clips are matched by (media, overlapping source range),
transitions by the source time of the cut, markers by name. Usage: python snapdiff.py old.json new.json"""
import json, sys
T, FPS, FRAME = 254_016_000_000, 24000 / 1001, 10_594_584_000
fmt = lambda s: f"{int(s // 60)}:{s % 60:05.2f}"
old, new = (json.load(open(p, encoding="utf-8")) for p in sys.argv[1:3])
TR = {}
for name in ("C2345", "C2346", "C2347", "C2348", "C2349", "C2350", "C2351"):
    try:
        TR[name] = json.load(open(f"{name}.transcript.json", encoding="utf-8"))["words"]
    except OSError:
        pass

def text(media, a, b):
    W = TR.get(media.split(".")[0], [])
    return " ".join(w["text"] for w in W if a - .05 <= w["start"] and w["end"] <= b + .05) or "[pausa]"

def clips(snap, track):
    return [(i["name"], i["sourceIn"] / T, i["sourceOut"] / T, i["start"] / T, i) for i in snap["tracks"].get(track, {}).get("items", [])]

print(f"duração: {old['durationFrames']} -> {new['durationFrames']} frames ({(new['durationFrames'] - old['durationFrames']) / FPS:+.1f}s)")
for track in sorted(set(old["tracks"]) | set(new["tracks"])):
    o, n = clips(old, track), clips(new, track)
    if not o and not n:
        continue
    lines = []
    # source coverage per media: what was removed / added
    for media in sorted({c[0] for c in o + n}):
        def cover(cs): return sorted((a, b) for m, a, b, *_ in cs if m == media)
        co, cn = cover(o), cover(n)
        def minus(A, B):
            out = []
            for a, b in A:
                segs = [(a, b)]
                for c, d in B:
                    segs = [s for x, y in segs for s in ((x, min(y, c)), (max(x, d), y)) if s[1] - s[0] > 0.02]
                out += segs
            return out
        for a, b in minus(co, cn):
            lines.append(f"  - {media} {fmt(a)}-{fmt(b)} ({b - a:.2f}s) saiu: {text(media, a, b)}")
        for a, b in minus(cn, co):
            lines.append(f"  + {media} {fmt(a)}-{fmt(b)} ({b - a:.2f}s) entrou: {text(media, a, b)}")
    # other per-clip changes (effects / gain) for clips with identical source range
    oi = {(m, round(a, 2), round(b, 2)): c for m, a, b, _, c in o}
    for m, a, b, st, c in n:
        prev = oi.get((m, round(a, 2), round(b, 2)))
        if prev:
            for k in ("gainDb", "speed", "enabled"):
                if prev.get(k) != c.get(k):
                    lines.append(f"  * {m} @ {fmt(st)}: {k} {prev.get(k)} -> {c.get(k)}")
            for e in set(prev["effects"]) | set(c["effects"]):
                pe, ce = prev["effects"].get(e), c["effects"].get(e)
                if pe != ce:
                    ch = [f"{k}: {pe.get(k) if pe else None} -> {ce.get(k) if ce else None}"
                          for k in sorted(set(pe or {}) | set(ce or {})) if (pe or {}).get(k) != (ce or {}).get(k)]
                    lines.append(f"  * {m} @ {fmt(st)} efeito {e}: " + ("; ".join(ch[:4]) or ("adicionado" if ce else "removido")))
    # transitions keyed by (media of outgoing clip, its source out)
    def trans(snap, track):
        items = {i["clip"]: i for i in snap["tracks"][track]["items"]} if track in snap["tracks"] else {}
        out = {}
        for t in snap["tracks"].get(track, {}).get("transitions", []):
            f = items.get(t["from"])
            key = (f["name"], round(f["sourceOut"] / T, 1)) if f else ("?", t["start"])
            out[key] = (round(t["duration"] / FRAME), t["effect"], t["align"], t["start"] / T)
        return out
    to, tn = trans(old, track), trans(new, track)
    for k in sorted(set(to) | set(tn), key=lambda k: (tn.get(k) or to.get(k))[3]):
        if to.get(k, (None,))[:3] != tn.get(k, (None,))[:3]:
            a, b = to.get(k), tn.get(k)
            where = fmt((b or a)[3])
            desc = (f"{a[0]}q {a[1]}" if a else "—") + " -> " + (f"{b[0]}q {b[1]} ({b[2]})" if b else "removida")
            lines.append(f"  ~ transição @ {where} (corte em {k[0]} {fmt(k[1])}): {desc}")
    if lines:
        print(f"== {track}: {len(o)} -> {len(n)} clipes")
        print("\n".join(lines))
mo, mn = {m["name"]: m for m in old["markers"]}, {m["name"]: m for m in new["markers"]}
for name in sorted(set(mo) | set(mn)):
    a, b = mo.get(name), mn.get(name)
    if not b: print(f"marcador removido: {name}")
    elif not a: print(f"marcador novo: {name} @ {fmt(b['start'] / T)}")
    elif a["start"] != b["start"] or a.get("comment") != b.get("comment") or a.get("color") != b.get("color"):
        print(f"marcador alterado: {name} @ {fmt(a['start'] / T)} -> {fmt(b['start'] / T)}")
