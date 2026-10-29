"""python -m stlflix --projeto <VSL> <comando>

--projeto aceita o caminho da pasta da VSL (em qualquer lugar do computador) ou só o nome dela, se já foi anotada (ver vsls.py).
Comandos que só leem: status, plano, checar, motions (sem --aplicar), enquadrar (sem --aplicar).
Comandos que mudam o projeto no FilmCraft pedem --aplicar (ou são a própria ação: reconectar, exportar-xml).
"""
import argparse
import json
import os
import sys

from . import blocos, checar, enquadrar, exportar, midia, motions, plano, vsls
from .audio import exportar_mix, mapa_de_cortes, trechos_mudos
from .fc import FC, FilmCraftError, abrir, porta_aberta
from .projeto import Projeto
from .tempo import mmss


def _seqs(proj, nomes):
    return [proj.sequencia(n) for n in nomes] if nomes else list(proj["sequencias"].values())


def cmd_nova(a):
    """Copia projetos/_MODELO-VSL para a pasta pedida (em qualquer lugar), põe nome e campanha no config.json e anota a VSL."""
    import shutil
    destino = os.path.abspath(a.projeto)
    if os.path.exists(destino):
        print(f"✗ já existe: {destino}", file=sys.stderr)
        sys.exit(2)
    campanhas = os.path.join(vsls.KIT, "2-design-system", "campanhas")
    if a.campanha and not os.path.isdir(os.path.join(campanhas, a.campanha)):
        print(f"✗ campanha '{a.campanha}' não existe (tem: {', '.join(sorted(os.listdir(campanhas)))})", file=sys.stderr)
        sys.exit(2)
    shutil.copytree(vsls.MODELO, destino, ignore=shutil.ignore_patterns(".gitkeep"))
    arq = os.path.join(destino, "config.json")
    cfg = json.load(open(arq, encoding="utf-8"))
    cfg["nome"] = a.nome or os.path.basename(destino)
    cfg["filmcraft"]["projeto"] = ""
    if a.campanha:
        cfg["motions"]["campanha"] = a.campanha
    json.dump(cfg, open(arq, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    exemplo = os.path.join(destino, "04-plano-de-cenas", "plano-de-cenas.md")
    os.replace(exemplo, os.path.join(destino, "04-plano-de-cenas", "EXEMPLO-plano-de-cenas.md"))
    vsls.anotar(destino)
    print(f"✓ projeto criado: {destino}")
    print(f"  campanha dos motions: {cfg['motions']['campanha']}")
    print("  falta preencher: config.json (projeto do FilmCraft, sequências, takes), 01-roteiro/teleprompter.txt,")
    print("  02-brutos e 03-b-rolls (ou atalhos para o Drive). O exemplo do plano ficou em 04-plano-de-cenas/EXEMPLO-plano-de-cenas.md")
    drive = midia.letra_drive()
    if drive and destino.upper().startswith(drive.upper()):
        print(f"  ⚠ a pasta está no Google Drive ({drive}): os renders dos motions ficam lentos e podem falhar. Prefira um disco do computador.")


def cmd_campanha(a):
    from . import campanha
    if a.acao == "listar":
        for c in campanha.listar():
            print(f"  {c['id']:10s} {c['nome']:28s} {len(c['icones'])} ícones{'' if c['logo'] else ' · SEM LOGO'}: {', '.join(c['icones'])}")
        return
    if not a.id:
        print("✗ informe o código da campanha, ex.: campanha conferir bf26", file=sys.stderr)
        sys.exit(2)
    if a.acao in ("nova", "importar"):
        if a.acao == "nova":
            cores = [c.strip() for c in a.cores.split(",")] if a.cores else None
            feitos = campanha.nova(a.id, a.nome or a.id, a.de, cores, a.barra, a.brilho)
            print(f"✓ campanha criada: {campanha.pasta(a.id)} (cores em campanha.json)")
        else:
            if not a.de:
                print("✗ informe --de <pasta com os arquivos do design>", file=sys.stderr)
                sys.exit(2)
            feitos = campanha.importar(a.id, a.de)
        for origem, nome, aviso in feitos:
            print(f"  {'✓' if nome else '✗'} {origem}" + (f" → {nome}.png" if nome else "") + (f"  ⚠ {aviso}" if aviso else ""))
    erros = campanha.conferir(a.id)
    for e in erros:
        print(f"  ✗ {e}")
    print(f"✓ campanha {a.id} pronta para usar" if not erros else f"{len(erros)} problema(s) na campanha {a.id}")
    if erros:
        sys.exit(1)


def cmd_vsls(a):
    if a.anotar:
        print(f"✓ anotada: {vsls.anotar(a.anotar)}")
    if a.tirar:
        print(f"✓ tirada da lista (a pasta continua no disco): {vsls.tirar(a.tirar)}")
    lista = vsls.todas()
    if not lista:
        print("nenhuma VSL neste computador ainda: crie com `nova`")
    for nome, pasta, existe in lista:
        print(f"  {'✓' if existe else '✗'} {nome:<28} {pasta}{'' if existe else '   (pasta não encontrada)'}")


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


def cmd_transcrever_brutos(proj, a):
    from . import decupagem
    prefixo = proj["takes"]["prefixo"]
    if a.pasta:
        takes, onde = decupagem.takes_da_pasta(a.pasta, prefixo), a.pasta
    elif porta_aberta():
        takes, onde = decupagem.takes_do_projeto(FC(), prefixo), "projeto do FilmCraft"
    else:
        onde = os.path.join(proj.pasta, "02-brutos")
        takes = decupagem.takes_da_pasta(onde, prefixo)
    if not takes:
        print(f"✗ nenhum vídeo começando com '{prefixo}' em {onde}: confira takes.prefixo no config, abra o FilmCraft "
              "com os brutos importados, ou use --pasta", file=sys.stderr)
        sys.exit(2)
    so = a.so.split(",") if a.so else None
    print(f"{len(takes)} takes ({onde}): {', '.join(sorted(takes))}")
    for take, r in decupagem.transcrever_brutos(proj, takes, so, a.refazer):
        print(f"  {take}: " + ("já transcrito" if r is None else f"{r['palavras']} palavras em {r['segundos']}s ({r['device']})"))
    caminho, feitos = decupagem.escrever_brutos_md(proj)
    print(f"documento: {caminho} ({len(feitos)} takes)")


def cmd_decupar(proj, a):
    from . import decupagem
    arquivo = _plano_pedido(proj, a)
    if not a.aplicar:
        clipes, trechos, erros = decupagem.planejar(proj, a.sequencia, arquivo)
        print(decupagem.tabela(clipes, trechos))
        for e in erros:
            print(f"  ✗ {e}")
        print("(nada foi alterado; rode de novo com --aplicar para montar a sequência)")
        sys.exit(1 if erros else 0)
    r = decupagem.aplicar(FC(), proj, a.sequencia, arquivo)
    print(f"✓ '{proj.sequencia(a.sequencia)}' montada: {r['clipes']} clipes de {mmss(r['inicio'])} a {mmss(r['fim'])}, "
          f"{r['crossfades']} crossfades, {r['marcadores']} marcadores. A sequência foi duplicada antes (backup) "
          f"e {r['tirados']} clipes dos brutos saíram dela. Revise e salve com Ctrl+S.")


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


def _plano_pedido(proj, a):
    """--plano aceita um caminho a partir da raiz do kit ou da pasta da VSL (ex.: 04-plano-de-cenas/rascunho-corpo.md)."""
    if not a.plano:
        return None
    return a.plano if os.path.exists(a.plano) else proj.caminho(a.plano)


def cmd_gatilhos(proj, a):
    P, fora = motions.planejar(proj, a.sequencia, _plano_pedido(proj, a), exigir_mov=False)
    for p in P:
        print(f"  ✓ {p['id']:6s} {mmss(p['inicio'])}  nota {p['nota']:.2f}  | ouvido: {p['ouvido'][:60]}")
    for c, motivo in fora:
        print(f"  ✗ {c['id']:6s} \"{c['gatilho']}\" | {motivo}")
    print(f"{len(P)} frases encontradas na transcrição · {len(fora)} com problema"
          + (": copie a frase de novo da transcrição, do jeito que foi dita" if fora else ""))


def cmd_motions(proj, a):
    P, fora = motions.planejar(proj, a.sequencia, _plano_pedido(proj, a))
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
    prefixo = a.prefixo or midia.letra_drive()
    if not prefixo:
        print("✗ não achei o Google Drive neste computador: informe --prefixo com a letra (ex.: H:)", file=sys.stderr)
        sys.exit(2)
    feitos, erros = midia.reconectar(FC(), prefixo)
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
    ap.add_argument("--projeto", help="pasta da VSL (com config.json) ou só o nome dela, ex.: VSL-Shark ou D:/Edicao/VSL-Shark")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("painel", help="página com as ferramentas instaladas e o que falta em cada VSL (não precisa de --projeto)")
    p.add_argument("--sem-abrir", action="store_true", help="só gera painel/index.html")
    p = sub.add_parser("vsls", help="lista as VSLs deste computador (não precisa de --projeto)")
    p.add_argument("--anotar", metavar="PASTA", help="põe na lista uma pasta de VSL que já existe (copiada de outro editor, por exemplo)")
    p.add_argument("--tirar", metavar="VSL", help="tira da lista (não apaga a pasta)")
    p = sub.add_parser("campanha", help="campanhas visuais dos motions: listar, nova, importar, conferir (não precisa de --projeto)")
    p.add_argument("acao", choices=["listar", "nova", "importar", "conferir"])
    p.add_argument("id", nargs="?", help="código da campanha, ex.: natal26 (pasta em 2-design-system/campanhas)")
    p.add_argument("--nome", help="nome legível, ex.: \"Natal 2026\"")
    p.add_argument("--de", help="pasta com os PNGs do design (ícones e logo)")
    p.add_argument("--cores", help="degradê dos títulos, da palavra-chave e do botão: \"#RRGGBB,#RRGGBB,...\" (padrão: o da BF26)")
    p.add_argument("--barra", help="cor da barrinha (padrão: a última do degradê)")
    p.add_argument("--brilho", help="cor do brilho embaixo dos ícones (padrão: a primeira do degradê)")
    sub.add_parser("escolher-pasta", help="abre a janela do Windows para o editor escolher uma pasta e mostra o caminho")
    p = sub.add_parser("nova", help="cria a pasta da VSL (no caminho de --projeto) a partir de projetos/_MODELO-VSL")
    p.add_argument("--nome", help="nome da VSL (padrão: o nome da pasta)")
    p.add_argument("--campanha", help="pasta em 2-design-system/campanhas (padrão: a do modelo)")
    sub.add_parser("abrir", help="abre o FilmCraft com o controle ligado e o projeto do config")
    sub.add_parser("status", help="o que já está preenchido / gerado no projeto")
    p = sub.add_parser("transcrever-brutos", help="transcreve cada take da câmera (para a decupagem) e escreve 06-transcricoes/brutos.md")
    p.add_argument("--pasta", help="pasta com os brutos (padrão: os importados no FilmCraft aberto, ou 02-brutos)")
    p.add_argument("--so", help="só estes takes, ex.: C2347,C2348")
    p.add_argument("--refazer", action="store_true", help="transcreve de novo os que já foram transcritos")
    p = sub.add_parser("decupar", help="mostra os cortes da decupagem aprovada (decupagem-<seq>.md); --aplicar monta a sequência")
    p.add_argument("sequencia")
    p.add_argument("--plano", help="outro arquivo de decupagem (padrão: 06-transcricoes/decupagem-<seq>.md)")
    p.add_argument("--aplicar", action="store_true")
    p = sub.add_parser("transcrever", help="exporta o áudio da sequência, transcreve com Whisper e divide por blocos")
    p.add_argument("sequencia")
    p = sub.add_parser("blocos", help="refaz só o documento por blocos a partir da transcrição existente")
    p.add_argument("sequencia")
    sub.add_parser("plano", help="valida o plano-de-cenas.md e mostra quais motions faltam renderizar")
    p = sub.add_parser("gatilhos", help="confere se cada frase-gatilho do plano (ou de um rascunho) aparece na transcrição; não precisa do FilmCraft nem dos .mov")
    p.add_argument("sequencia")
    p.add_argument("--plano", help="outro arquivo de plano, ex.: 04-plano-de-cenas/rascunho-corpo.md")
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
    p.add_argument("--prefixo", help="início do caminho da mídia a reconectar (padrão: a letra do Google Drive deste computador)")
    p = sub.add_parser("exportar-xml", help="exporta XML (FCP7) das sequências; versões anteriores vão para backup")
    p.add_argument("sequencias", nargs="*")
    p.add_argument("--destino")
    a = ap.parse_args(argv)
    if a.cmd == "painel":
        from . import painel
        saida, dados = painel.gerar(abrir=not a.sem_abrir)
        print(f"✓ painel: {saida} ({len(dados['projetos'])} VSLs)")
        return
    if a.cmd == "escolher-pasta":
        print(vsls.escolher_pasta() or "✗ nenhuma pasta escolhida")
        return
    try:
        if a.cmd == "vsls":
            return cmd_vsls(a)
        if a.cmd == "campanha":
            return cmd_campanha(a)
        if not a.projeto:
            ap.error("informe --projeto <VSL> (o nome ou a pasta)")
        if a.cmd == "nova":
            return cmd_nova(a)
        proj = Projeto(vsls.resolver(a.projeto))
        globals()["cmd_" + a.cmd.replace("-", "_")](proj, a)
    except (FileNotFoundError, FileExistsError, KeyError, ValueError, FilmCraftError) as e:
        print(f"✗ {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
