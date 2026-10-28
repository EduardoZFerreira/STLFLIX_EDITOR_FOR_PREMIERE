"""Normalização de texto em português e busca aproximada de frases na transcrição."""
import difflib
import re
import unicodedata

NUM = {"um": "1", "uma": "1", "dois": "2", "duas": "2", "tres": "3", "quatro": "4", "cinco": "5", "seis": "6",
       "sete": "7", "oito": "8", "nove": "9", "dez": "10", "vinte": "20", "trinta": "30", "cem": "100",
       "pra": "para", "pro": "para", "pros": "para", "pras": "para"}


def norm(texto, sinonimos=None):
    """Minúsculas, sem acento, só palavras e números; números por extenso viram dígitos."""
    t = unicodedata.normalize("NFKD", texto.lower().replace("**", ""))
    t = "".join(c for c in t if not unicodedata.combining(c)).replace("r$", " ")
    rep = dict(NUM, **(sinonimos or {}))
    return [rep.get(x, x) for x in re.findall(r"[a-z0-9]+", t)]


def tokens_da_transcricao(tr, sinonimos=None):
    """[(token, início em s)] de uma transcrição {words:[{text,start,end}]}."""
    return [(tok, w["start"]) for w in tr["words"] for tok in norm(w["text"], sinonimos)]


def achar(tokens, frase, inicio=0, fim=None, sinonimos=None):
    """Melhor posição de `frase` em tokens[inicio:fim] → (índice, nota 0..1). Em empate, a mais cedo."""
    q = norm(frase, sinonimos)
    if not q:
        return None, 0.0
    alvo = " ".join(q)
    fim = len(tokens) if fim is None else min(fim, len(tokens))
    sm = difflib.SequenceMatcher(None)
    sm.set_seq2(alvo)                              # o alvo fica fixo: o difflib guarda o índice dele
    melhor = (0.0, None)
    for i in range(inicio, max(inicio, fim - len(q) + 1)):
        sm.set_seq1(" ".join(t for t, _ in tokens[i:i + len(q)]))
        if sm.real_quick_ratio() <= melhor[0] + 1e-9 or sm.quick_ratio() <= melhor[0] + 1e-9:
            continue
        r = sm.ratio()
        if r > melhor[0] + 1e-9:
            melhor = (r, i)
    return melhor[1], melhor[0]


def aplicar_grafias(texto, grafias):
    """grafias: [[regex, substituto], ...] do config.json (ex.: Steliflix → STLflix)."""
    for padrao, novo in grafias or []:
        texto = re.sub(padrao, novo, texto)
    return texto
