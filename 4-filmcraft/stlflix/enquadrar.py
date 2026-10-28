"""Enquadramento padrão dos takes da câmera (escala e ponto de ancoragem do efeito Movimento).

Vale para os clipes da V1 cujo nome começa com takes.prefixo (ex.: "C23"); sequências aninhadas na V1 são
ajustadas por dentro. Ex. VSL-Shark: escala 114 e âncora [1080, 1900].
"""
import collections


def _clipes_de_take(seq, prefixo):
    return [c for c in seq["video"][0]["items"] if c["name"].startswith(prefixo)] if seq["video"] else []


def avaliar(fc, nomes_seq, prefixo, escala, ancora):
    """{sequência: (clipes já certos, clipes a ajustar)} incluindo sequências aninhadas."""
    seqs = fc.sequencias()
    rel, fila, vistos = {}, list(nomes_seq), set()
    while fila:
        nome = fila.pop(0)
        if nome in vistos or nome not in seqs:
            continue
        vistos.add(nome)
        s = fc.run("sequence.inspect", item=seqs[nome])
        ok = falta = 0
        for c in _clipes_de_take(s, prefixo):
            m = next(e for e in c["effects"] if e["effect"] == "motion")["params"]
            certo = m["scale"]["value"] == f"Float({float(escala)})" and f"y: {float(ancora[1])}" in m["anchor"]["value"]
            ok, falta = ok + certo, falta + (not certo)
        rel[nome] = (ok, falta)
        fila += [c["name"] for c in (s["video"][0]["items"] if s["video"] else []) if c["item"] in seqs.values()]
    return rel


def aplicar(fc, nomes_seq, prefixo, escala, ancora):
    seqs = fc.sequencias()
    contagem, fila, vistos = collections.Counter(), list(nomes_seq), set()
    ativa = fc.run("sequence.inspect")["id"]
    while fila:
        nome = fila.pop(0)
        if nome in vistos or nome not in seqs:
            continue
        vistos.add(nome)
        fc.run("sequence.open", item=seqs[nome])         # só a sequência aberta aceita edição
        s = fc.run("sequence.inspect", item=seqs[nome])
        for c in _clipes_de_take(s, prefixo):
            mi = [e["effect"] for e in c["effects"]].index("motion")
            fc.run("effects.setParam", clip=c["clip"], effect=mi, param="scale", value=float(escala))
            fc.run("effects.setParam", clip=c["clip"], effect=mi, param="anchor", value=[float(ancora[0]), float(ancora[1])])
            contagem[nome] += 1
        fila += [c["name"] for c in (s["video"][0]["items"] if s["video"] else []) if c["item"] in seqs.values()]
    fc.run("sequence.open", item=ativa)
    return dict(contagem)
