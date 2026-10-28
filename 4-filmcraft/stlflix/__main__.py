"""python -m stlflix --projeto projetos/<VSL> <comando>

Comandos que só leem: status, plano, checar, motions (sem --aplicar), enquadrar (sem --aplicar).
Comandos que mudam o projeto no FilmCraft pedem --aplicar (ou são a própria ação: reconectar, exportar-xml).
"""
import argparse
import json
import os
import sys

from . import blocos, checar, enquadrar, exportar, midia, motions, plano
from .audio import exportar_mix, mapa_de_cortes, trechos_mudos
from .fc import FC, FilmCraftError, abrir, porta_aberta
from .projeto import Projeto
from .tempo import mmss


def _seqs(proj, nomes):
    return [proj.sequencia(n) for n in nomes] if nomes else list(proj["sequencias"].values())


def cmd_nova(a):
    """Copia projetos/_MODELO-VSL para a pasta pedida e põe o nome no config.json."""
    import shutil
    destino = os.path.abspath(a.projeto)
    modelo = os.path.join(os.path.dirname(destino), "_MODELO-VSL")
    if not os.path.isdir(modelo):
        modelo = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "projetos", "_MODELO-VSL")
    if os.path.exists(destino):
        print(f"✗ já existe: {destino}", file=sys.stderr)
        sys.exit(2)
    shutil.copytree(modelo, destino, ignore=shutil.ignore_patterns(".gitkeep"))
    arq = os.path.join(destino, "config.json")
    cfg = json.load(open(arq, encoding="utf-8"))
    cfg["nome"] = a.nome or os.path.basename(destino)
    cfg["filmcraft"]["projeto"] = ""
    json.dump(cfg, open(arq, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    exemplo = os.path.join(destino, "04-plano-de-cenas", "plano-de-cenas.md")
    os.replace(exemplo, os.path.join(destino, "04-plano-de-cenas", "EXEMPLO-plano-de-cenas.md"))
    print(f"✓ projeto criado: {destino}")
    print("  falta preencher: config.json (projeto do FilmCraft, sequências, takes), 01-roteiro/teleprompter.txt,")
    print("  02-brutos e 03-b-rolls (ou atalhos para o Drive). O exemplo do plano ficou em 04-plano-de-cenas/EXEMPLO-plano-de-cenas.md")


def cmd_abrir(proj, a):
    fcproj = proj["filmcraft"]["projeto"]
    ok = abrir(proj.caminho(fcproj) if fcproj else None)
    print("FilmCraft aberto com o controle ligado" if ok else "o controle não respondeu: veja se há alguma janela pedindo resposta no FilmCraft")


def cmd_status(proj, a):
    print(f"Projeto: {proj['nome'] or os.path.basename(proj.pasta)}  ({proj.pasta})")
    p = proj.caminho(proj["roteiro"])
    print(f"  {'✓' if os.path.exists(p) else '✗'} roteiro: {proj['roteiro']}")
    for p in proj.plano():
        print(f"  {'✓' if os.path.exists(p) else '✗'} plano de cenas: {os.path.relpath(p, proj.pasta)}")
    movs = motions.arquivos_motion(proj.pasta_de("motions"))
    print(f"  {'✓' if movs else '✗'} motions: {len(movs)} .mov em {proj['pastas']['motions']}")
    for chave, nome in proj["sequencias"].items():
        tem = os.path.exists(proj.arquivo_transcricao(chave))
        print(f"  {'✓' if tem else '·'} transcrição {chave} ({nome})")
    if porta_aberta():
        existentes = FC().sequencias()
        for nome in proj["sequencias"].values():
            print(f"  {'✓' if nome in existentes else '✗'} sequência no FilmCraft: {nome}")
    else:
        print("  · FilmCraft fechado (rode `abrir`)")


def cmd_transcrever(proj, a):
    from .transcrever import suspeitas, transcrever       # só aqui: precisa do faster-whisper
    fc = FC()
    nome = proj.sequencia(a.sequencia)
    seq = fc.seq(nome)
    wav = proj.arquivo_transcricao(a.sequencia, "wav")
    print(f"exportando o áudio de '{nome}'…")
    exportar_mix(fc, seq["id"], wav)
    for i, f in trechos_mudos(wav):
        print(f"  ⚠ trecho MUDO de {mmss(i)} a {mmss(f)} — confira se o áudio veio na importação")
    mapa = mapa_de_cortes(seq)
    json.dump(mapa, open(proj.arquivo_transcricao(a.sequencia, "cortes.json"), "w", encoding="utf-8"), ensure_ascii=False)
    cfg = proj["transcricao"]
    print("transcrevendo (Whisper)…")
    r = transcrever(wav, proj.arquivo_transcricao(a.sequencia), cfg["modelo"], cfg["idioma"], cfg["nomes"])
    print(f"  {r['palavras']} palavras em {r['segundos']}s ({r['device']})")
    tr = json.load(open(proj.arquivo_transcricao(a.sequencia), encoding="utf-8"))
    for t, w in suspeitas(tr)[:15]:
        print(f"  ⚠ palavra esticada em {mmss(t)}: '{w}' (possível tropeço repetido)")
    _blocos(proj, a.sequencia, tr, mapa)


def _blocos(proj, chave, tr, mapa):
    achados, faltando, falas = blocos.gerar(proj, chave, tr, mapa)
    if len(achados) <= 1:                          # lead ou trecho avulso: não é o corpo dividido em blocos
        print("  · nenhum bloco do corpo nesta sequência: documento sem divisão por blocos")
    else:
        for a in achados:
            print(f"  {mmss(a['t'])}  Bloco {a['n']:>3} · {a['titulo'][:50]}  ({a['nota']:.2f})")
        for n, t, nota in faltando:
            print(f"  ·  Bloco {n:>3} · {t[:50]}: não está nesta sequência ({nota:.2f})")
    print(f"documento: {proj.arquivo_transcricao(chave, 'md')} ({falas} falas)")


def cmd_blocos(proj, a):
    tr = json.load(open(proj.arquivo_transcricao(a.sequencia), encoding="utf-8"))
    mapa = json.load(open(proj.arquivo_transcricao(a.sequencia, "cortes.json"), encoding="utf-8"))
    _blocos(proj, a.sequencia, tr, mapa)


def cmd_plano(proj, a):
    movs = motions.arquivos_motion(proj.pasta_de("motions"))
    for p in proj.plano():
        if not os.path.exists(p):
            print(f"✗ não existe: {p}")
            continue
        cenas = plano.ler(p)
        erros = plano.validar(cenas)
        sem_mov = [c["id"] for c in cenas if c["id"] not in movs]
        print(f"{len(cenas)} cenas em {p}")
        for e in erros:
            print("  ✗", e)
        if sem_mov:
            print(f"  · sem .mov renderizado ainda: {', '.join(sem_mov[:20])}{' …' if len(sem_mov) > 20 else ''}")
        if not erros:
            print("  ✓ formato ok")


def cmd_motions(proj, a):
    P, fora = motions.planejar(proj, a.sequencia, a.plano)
    print(motions.tabela(P, fora))
    if a.aplicar:
        n = motions.aplicar(FC(), proj, a.sequencia, P)
        print(f"✓ {n} clipes de motion colocados em '{proj.sequencia(a.sequencia)}' ({proj['motions']['trilha']}, "
              f"escala {proj['motions']['escala']:.0f}). Revise e salve com Ctrl+S.")
    else:
        print("(nada foi alterado; rode de novo com --aplicar para colocar na timeline)")


def cmd_enquadrar(proj, a):
    t = proj["takes"]
    alvo = _seqs(proj, a.sequencias)
    fc = FC()
    if not a.aplicar:
        for nome, (ok, falta) in enquadrar.avaliar(fc, alvo, t["prefixo"], t["escala"], t["ancora"]).items():
            print(f"  {nome}: {ok} certos, {falta} a ajustar")
        print(f"(escala {t['escala']} · âncora {t['ancora']} · rode com --aplicar)")
        return
    for nome, n in enquadrar.aplicar(fc, alvo, t["prefixo"], t["escala"], t["ancora"]).items():
        print(f"  ✓ {nome}: {n} takes ajustados")


def cmd_checar(proj, a):
    res = checar.checar(FC(), _seqs(proj, a.sequencias), testar_render=not a.rapido)
    for grav, seq, msg in res:
        print(f"  {'✗' if grav == 'ERRO' else '⚠'} [{seq}] {msg}")
    print("✓ nenhum problema encontrado" if not res else f"{sum(g == 'ERRO' for g, _, _ in res)} erro(s), "
          f"{sum(g == 'AVISO' for g, _, _ in res)} aviso(s)")
    sys.exit(1 if any(g == "ERRO" for g, _, _ in res) else 0)


def cmd_reconectar(proj, a):
    feitos, erros = midia.reconectar(FC(), a.prefixo)
    print(f"✓ {len(feitos)} itens reconectados")
    for n, e in erros:
        print(f"  ✗ {n}: {e}")


def cmd_exportar_xml(proj, a):
    destino = a.destino or proj["drive"]["entrega_xml"] or proj.pasta_de("exports")
    for f in exportar.xmls(FC(), _seqs(proj, a.sequencias), destino):
        print("  ✓", f)


def main(argv=None):
    for s in (sys.stdout, sys.stderr):              # saída redirecionada no Windows cai em cp1252 e não imprime ✓/✗
        s.reconfigure(encoding="utf-8", errors="replace")
    ap =argparse.ArgumentParser(prog="python -m stlflix", description="Ferramentas de edição de VSL STLFLIX no FilmCraft")
    ap.add_argument("--projeto", help="pasta do projeto (com config.json), ex.: projetos/VSL-Shark")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("painel", help="página com as ferramentas instaladas e o que falta em cada VSL (não precisa de --projeto)")
    p.add_argument("--sem-abrir", action="store_true", help="só gera painel/index.html")
    p = sub.add_parser("nova", help="cria a pasta da VSL a partir de projetos/_MODELO-VSL")
    p.add_argument("--nome", help="nome da VSL (padrão: o nome da pasta)")
    sub.add_parser("abrir", help="abre o FilmCraft com o controle ligado e o projeto do config")
    sub.add_parser("status", help="o que já está preenchido / gerado no projeto")
    p = sub.add_parser("transcrever", help="exporta o áudio da sequência, transcreve com Whisper e divide por blocos")
    p.add_argument("sequencia")
    p = sub.add_parser("blocos", help="refaz só o documento por blocos a partir da transcrição existente")
    p.add_argument("sequencia")
    sub.add_parser("plano", help="valida o plano-de-cenas.md e mostra quais motions faltam renderizar")
    p = sub.add_parser("motions", help="encaixa os motions nas frases-gatilho (mostra o plano; --aplicar coloca)")
    p.add_argument("sequencia")
    p.add_argument("--plano", help="outro plano de cenas (padrão: o do config)")
    p.add_argument("--aplicar", action="store_true")
    p = sub.add_parser("enquadrar", help="escala e âncora padrão nos takes da câmera (--aplicar para mudar)")
    p.add_argument("sequencias", nargs="*")
    p.add_argument("--aplicar", action="store_true")
    p = sub.add_parser("checar", help="checagens antes de exportar (mídia preta, trilhas, pan, áudio faltando)")
    p.add_argument("sequencias", nargs="*")
    p.add_argument("--rapido", action="store_true", help="pula o teste de render (quadros pretos)")
    p = sub.add_parser("reconectar", help="reconecta a mídia do Drive no mesmo caminho (resolve MEDIA UNREADABLE)")
    p.add_argument("--prefixo", default="G:")
    p = sub.add_parser("exportar-xml", help="exporta XML (FCP7) das sequências; versões anteriores vão para backup")
    p.add_argument("sequencias", nargs="*")
    p.add_argument("--destino")
    a = ap.parse_args(argv)
    if a.cmd == "painel":
        from . import painel
        saida, dados = painel.gerar(abrir=not a.sem_abrir)
        print(f"✓ painel: {saida} ({len(dados['projetos'])} VSLs)")
        return
    if not a.projeto:
        ap.error("informe --projeto projetos/<VSL>")
    if a.cmd == "nova":
        return cmd_nova(a)
    try:
        proj = Projeto(a.projeto)
        globals()["cmd_" + a.cmd.replace("-", "_")](proj, a)
    except (FileNotFoundError, KeyError, FilmCraftError) as e:
        print(f"✗ {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
