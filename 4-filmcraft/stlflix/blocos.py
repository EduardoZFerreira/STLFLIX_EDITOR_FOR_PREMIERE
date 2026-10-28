"""Divide a transcrição de uma sequência pelos blocos do roteiro e escreve o documento em Markdown.

Roteiro (teleprompter .txt) no formato:
    --- BLOCO 5 · LUAN ---            (também "--- LEAD A · A objeção ---" e "--- BLOCO 28 CURTO · OFERTA ---")
    → instrução de gravação (ignorada)
    texto falado...
Cada bloco é localizado pela sua primeira frase, em ordem. Versões curtas (CURTO) e inserções são procuradas no
corpo inteiro; num empate com a versão completa, vence a curta quando blocos.versao_curta = true no config.
Quando a gravação abre diferente do texto, use blocos.ancoras no config: {"7": "olha o leonardo de criciuma"}.
"""
import json
import re

from .audio import origem
from .tempo import mmss, hms
from .texto import achar, aplicar_grafias, norm, tokens_da_transcricao

CAB = re.compile(r"--- (BLOCO|LEAD) ([0-9A-Z]+)( CURTO)? · (.+?) ---$")
TITULO_SOLTO = re.compile(r"[A-ZÁÉÍÓÚÂÊÔÃÕÇ0-9 ·:,—–\-]{5,}")


def ler_roteiro(caminho):
    """[{tipo, n, curto, titulo, texto}] na ordem do arquivo."""
    blocos, atual = [], None
    for bruto in open(caminho, encoding="utf-8"):
        linha = bruto.strip()
        m = CAB.match(linha)
        if m:
            atual = dict(tipo=m.group(1), n=m.group(2), curto=bool(m.group(3)), titulo=m.group(4), texto="")
            blocos.append(atual)
            continue
        if atual is None or not linha or linha.startswith(("→", "=", "---", "PARTE")) or TITULO_SOLTO.fullmatch(linha):
            continue
        if len(atual["texto"]) < 400:
            atual["texto"] += " " + linha
    return blocos


def localizar(blocos, tokens, ancoras=None, versao_curta=False, so_bloco=True, sinonimos=None):
    """Início de cada bloco na fala → [{n, titulo, t, nota}] ordenado pelo tempo; e os não encontrados."""
    ancoras = {str(k): v for k, v in (ancoras or {}).items()}
    achados, faltando, cursor = [], [], 0
    for b in blocos:
        if so_bloco and b["tipo"] != "BLOCO":
            continue
        frase = ancoras.get(b["n"]) if (b["n"] in ancoras and not b["curto"]) else b["texto"]
        alvo = " ".join(norm(frase, sinonimos)[:9])
        if not alvo:
            continue
        i, nota = achar(tokens, alvo, 0 if b["curto"] else cursor, sinonimos=sinonimos)
        if i is None or nota < 0.72:
            faltando.append((b["n"], b["titulo"] + (" (curto)" if b["curto"] else ""), round(nota, 2)))
            continue
        ant = next((a for a in achados if a["n"] == b["n"]), None)
        if ant and (ant["nota"] > nota + 0.02 or (ant["nota"] >= nota and not (versao_curta and b["curto"]))):
            continue
        if ant:
            achados.remove(ant)
        achados.append(dict(n=b["n"], titulo=b["titulo"] + (" (versão curta)" if b["curto"] else ""),
                            t=tokens[i][1], nota=round(nota, 2)))
        if not b["curto"]:
            cursor = i + 1
    achados.sort(key=lambda a: a["t"])
    if achados:
        achados[0]["t"] = 0.0
    nomes_achados = {a["n"] for a in achados}
    faltando = [f for f in faltando if f[0] not in nomes_achados]
    return achados, faltando


def escrever_md(caminho_md, tr, mapa, achados, grafias=None, titulo=None):
    linhas = [f"# Transcrição — {titulo or mapa['sequencia']}", "",
              f"Sequência \"{mapa['sequencia']}\" ({mmss(mapa['duracao'])}, {len(mapa['cortes'])} cortes). Tempos = posição "
              "na sequência (mm:ss.d); entre parênteses, o take e o tempo no bruto. Blocos conforme o roteiro, "
              "localizados pela fala. Fonte: Whisper.", ""]
    secoes = achados or [dict(n="", titulo=mapa["sequencia"], t=0.0)]
    for k, a in enumerate(secoes):
        fim = secoes[k + 1]["t"] if k + 1 < len(secoes) else 1e9
        cab = f"BLOCO {a['n']} · {a['titulo']}" if a["n"] else a["titulo"].upper()
        linhas += [f"## {cab}  ·  {mmss(a['t'])}", ""]
        for s in tr["segments"]:
            if a["t"] - 0.3 <= s["start"] + 0.05 < fim - 0.3:
                take, t_bruto = origem(mapa, s["start"])
                linhas.append(f"- **{mmss(s['start'])}** {aplicar_grafias(s['text'].strip(), grafias)}  _({take} {hms(t_bruto)})_")
        linhas.append("")
    open(caminho_md, "w", encoding="utf-8").write("\n".join(linhas))
    return sum(1 for l in linhas if l.startswith("- **"))


def gerar(proj, chave, tr, mapa):
    """Gera <transcricoes>/<chave>.md e <chave>.blocos.json; devolve (achados, faltando, falas)."""
    cfg_t, cfg_b = proj["transcricao"], proj["blocos"]
    tokens = tokens_da_transcricao(tr, cfg_t.get("sinonimos"))
    achados, faltando = [], []
    roteiro = proj.caminho(proj["roteiro"])
    try:
        blocos = ler_roteiro(roteiro)
    except FileNotFoundError:
        blocos = []
    curta = cfg_b.get("versao_curta")              # true/false, ou a lista das sequências que usam as versões curtas
    curta = chave in curta if isinstance(curta, list) else bool(curta)
    if blocos and any(b["tipo"] == "BLOCO" for b in blocos):
        achados, faltando = localizar(blocos, tokens, cfg_b.get("ancoras"), curta, sinonimos=cfg_t.get("sinonimos"))
    md = proj.arquivo_transcricao(chave, "md")
    falas = escrever_md(md, tr, mapa, achados if len(achados) > 1 else [], cfg_t.get("grafias"))
    json.dump(dict(achados=achados, faltando=faltando), open(proj.arquivo_transcricao(chave, "blocos.json"), "w",
              encoding="utf-8"), ensure_ascii=False, indent=1)
    return achados, faltando, falas
