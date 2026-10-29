"""Painel do editor: página local com as ferramentas instaladas e o que já está preenchido em cada VSL.

stlflix painel gera painel/index.html a partir de painel/modelo.html (dados embutidos em JSON) e abre no navegador.
Só lê: não cria pastas nem conecta no FilmCraft. As ferramentas vêm do próprio instalador (-Verificar -Json);
as VSLs, da lista deste computador (vsls.py).
"""
import datetime
import json
import os
import pathlib
import subprocess
import tempfile

from . import plano, vsls
from .blocos import ler_roteiro
from .motions import arquivos_motion
from .projeto import Projeto
from .vsls import KIT


def ferramentas():
    """Resultado do instalador em modo de conferência: [{ok, item, detalhe, essencial}]."""
    saida = os.path.join(tempfile.gettempdir(), "stlflix-ferramentas.json")
    script = os.path.join(KIT, "1-instalacao", "instalar.ps1")
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script, "-Verificar", "-Json", saida],
                   capture_output=True, timeout=300)
    try:
        return json.load(open(saida, encoding="utf-8-sig"))
    except (OSError, ValueError):
        return [dict(ok=False, item="Instalador", detalhe="não consegui rodar 1-instalacao/instalar.ps1", essencial=True)]


def atualizacao():
    """Quantas mudanças do kit estão no GitHub e ainda não neste computador (None se não deu para saber, ex.: sem internet)."""
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never")   # nunca abrir janela de login
    try:
        subprocess.run(["git", "-C", KIT, "fetch", "--quiet", "origin"], capture_output=True, timeout=20, env=env, check=True)
        r = subprocess.run(["git", "-C", KIT, "rev-list", "--count", "HEAD..@{u}"], capture_output=True, text=True,
                           timeout=10, env=env, check=True)
        return int(r.stdout.strip())
    except (OSError, subprocess.SubprocessError, ValueError):
        return None


def _uri(p):
    return pathlib.Path(p).as_uri() if os.path.exists(p) else None


def _conteudo(pasta):
    """Arquivos e atalhos na pasta (sem entrar nas subpastas), ignorando .gitkeep."""
    if not os.path.isdir(pasta):
        return []
    return [n for n in os.listdir(pasta) if n != ".gitkeep" and not n.startswith("~")]


def _exemplo():
    return json.load(open(os.path.join(KIT, "projetos", "_MODELO-VSL", "config.json"), encoding="utf-8"))


def _item(titulo, estado, detalhe, quem="voce", pedido=None, pasta=None):
    return dict(titulo=titulo, estado=estado, detalhe=detalhe, quem=quem, pedido=pedido, pasta=pasta)


def projeto(pasta):
    proj = Projeto(pasta)
    vid = os.path.basename(proj.pasta)          # nome da pasta: é como o editor chama a VSL nos pedidos
    nome = proj["nome"] or vid
    itens = {}

    fc = proj["filmcraft"]["projeto"]
    if fc and os.path.exists(proj.caminho(fc)):
        itens["filmcraft"] = _item("Projeto do FilmCraft", "ok", os.path.basename(fc))
    else:
        itens["filmcraft"] = _item("Projeto do FilmCraft", "falta",
                                   "caminho do .fcproj não encontrado" if fc else "falta o caminho do .fcproj no config.json",
                                   "claude", f"Configura o projeto do FilmCraft da {vid}")

    seqs = proj["sequencias"]
    lista = ", ".join(f"{k} → {v}" for k, v in seqs.items())
    if not seqs:
        itens["sequencias"] = _item("Sequências", "falta", "nenhuma sequência no config.json", "claude",
                                    f"Configura as sequências da {vid}")
    elif seqs == _exemplo()["sequencias"]:
        itens["sequencias"] = _item("Sequências", "aviso", f"ainda são as do exemplo ({lista}): confira os nomes no FilmCraft",
                                    "claude", f"Configura as sequências da {vid}")
    else:
        itens["sequencias"] = _item("Sequências", "ok", lista)

    rot = proj.caminho(proj["roteiro"])
    if not os.path.exists(rot):
        itens["roteiro"] = _item("Roteiro (teleprompter)", "falta", f"salve o roteiro em {proj['roteiro']}",
                                 pasta=_uri(os.path.dirname(rot)))
    else:
        n = len(ler_roteiro(rot))
        itens["roteiro"] = (_item("Roteiro (teleprompter)", "ok", f"{n} blocos marcados", pasta=_uri(os.path.dirname(rot))) if n else
                            _item("Roteiro (teleprompter)", "aviso", "sem marcações --- BLOCO 5 · Título ---: a transcrição não vai dividir por blocos",
                                  pasta=_uri(os.path.dirname(rot))))

    for chave, pasta_mod, titulo in (("brutos", "02-brutos", "Brutos da câmera"), ("brolls", "03-b-rolls", "B-rolls")):
        p = os.path.join(proj.pasta, pasta_mod)
        n = len(_conteudo(p))
        itens[chave] = (_item(titulo, "ok", f"{n} itens", pasta=_uri(p)) if n else
                        _item(titulo, "aviso", "vazia (tudo bem se estão só no Drive)", pasta=_uri(p)))

    feitas = [k for k in seqs if os.path.exists(proj.arquivo_transcricao(k))] if seqs else []
    falta_tr = [k for k in seqs if k not in feitas]
    pasta_tr = proj.caminho(proj["pastas"]["transcricoes"])
    if seqs and not falta_tr:
        itens["transcricao"] = _item("Transcrições", "ok", ", ".join(feitas), pasta=_uri(pasta_tr))
    else:
        itens["transcricao"] = _item("Transcrições", "aviso" if feitas else "falta",
                                     ("feitas: " + ", ".join(feitas) + " · " if feitas else "") + "faltam: " + (", ".join(falta_tr) or "configure as sequências"),
                                     "claude", f"Abre o FilmCraft e transcreve {falta_tr[0] if falta_tr else 'o corpo'} da {vid}", _uri(pasta_tr))

    ids, erros, faltam_planos = [], [], []
    for p in proj.plano():
        if not os.path.exists(p):
            faltam_planos.append(os.path.relpath(p, proj.pasta).replace("\\", "/"))
            continue
        cenas = plano.ler(p)
        ids += [c["id"] for c in cenas]
        erros += plano.validar(cenas)
    pasta_pl = os.path.dirname(proj.plano()[0])
    if faltam_planos and not ids:
        itens["plano"] = _item("Plano de cenas", "falta", f"escreva {faltam_planos[0]} (tem um exemplo na pasta)",
                               pasta=_uri(pasta_pl))
    elif erros or faltam_planos:
        itens["plano"] = _item("Plano de cenas", "aviso",
                               f"{len(ids)} cenas · " + "; ".join(erros[:2] + [f"falta {f}" for f in faltam_planos]),
                               "claude", f"Confere o plano de cenas da {vid}", _uri(pasta_pl))
    else:
        itens["plano"] = _item("Plano de cenas", "ok", f"{len(ids)} cenas", pasta=_uri(pasta_pl))

    ref = proj["motions"]["referencia"]
    itens["referencia"] = (_item("Quadro de referência", "ok", os.path.basename(ref)) if ref and os.path.exists(proj.caminho(ref)) else
                           _item("Quadro de referência", "aviso", "sem quadro do apresentador: a prévia dos motions sai em fundo cinza",
                                 "claude", f"Exporta um quadro do apresentador para a referência da {vid}"))

    pasta_mov = proj.caminho(proj["pastas"]["motions"])
    movs = arquivos_motion(pasta_mov) if os.path.isdir(pasta_mov) else {}
    sem = [i for i in ids if i not in movs]
    if not ids:
        itens["motions"] = _item("Motions criados", "falta", "depois do plano de cenas", pasta=_uri(pasta_mov))
    elif not sem:
        itens["motions"] = _item("Motions criados", "ok", f"todos os {len(ids)} prontos", pasta=_uri(pasta_mov))
    else:
        feitos = len(ids) - len(sem)
        itens["motions"] = _item("Motions criados", "aviso" if feitos else "falta",
                                 f"{feitos} de {len(ids)} prontos · faltam {', '.join(sem[:6])}{' …' if len(sem) > 6 else ''}",
                                 "claude", f"Cria os motions {' e '.join(sem[:2])} da {vid} para eu ver" if not feitos else f"Cria os motions que faltam da {vid}",
                                 _uri(pasta_mov))

    pasta_exp = proj.caminho(proj["pastas"]["exports"])
    n = len(_conteudo(pasta_exp))
    itens["exports"] = _item("Exports", "ok" if n else "info", f"{n} arquivos" if n else "nada exportado ainda", pasta=_uri(pasta_exp))

    proximo = None
    for k in ("filmcraft", "sequencias", "roteiro", "transcricao", "plano", "motions"):
        if itens[k]["estado"] in ("falta", "aviso"):
            proximo = itens[k]
            break
    if proximo is None:
        proximo = _item("Encaixar e entregar", "info", "motions prontos: coloque na timeline, revise e cheque antes de exportar",
                        "claude", f"Coloca os motions no {next(iter(seqs))} da {vid} e checa antes de exportar" if seqs else None)
    return dict(id=vid, nome=nome, pasta=proj.pasta, uri=_uri(proj.pasta), itens=list(itens.values()), proximo=proximo)


def gerar(abrir=True):
    projetos, erros = [], []
    for n, p, existe in vsls.todas():
        if not existe:
            erros.append(f"{n}: pasta não encontrada ({p}). Se mudou de lugar, peça ao Claude para anotar o novo caminho")
            continue
        try:
            projetos.append(projeto(p))
        except (OSError, ValueError, KeyError) as e:
            erros.append(f"{n}: {e}")
    projetos.sort(key=lambda p: p["nome"].lower())
    dados = dict(gerado=datetime.datetime.now().strftime("%d/%m/%Y %H:%M"), kit=KIT, atualizacao=atualizacao(),
                 ferramentas=ferramentas(), projetos=projetos, erros=erros)
    modelo = open(os.path.join(KIT, "painel", "modelo.html"), encoding="utf-8").read()
    js = json.dumps(dados, ensure_ascii=False).replace("</", "<\\/")
    saida = os.path.join(KIT, "painel", "index.html")
    open(saida, "w", encoding="utf-8").write(modelo.replace("__DADOS__", js))
    if abrir:
        os.startfile(saida)
    return saida, dados
