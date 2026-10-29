"""Campanhas visuais dos motions: 2-design-system/campanhas/<id>/ com campanha.json (nome, cores, texto do logo),
os ícones em PNG transparente (520 px de altura, como o kit BF26) e o logo-kv.png.

    stlflix campanha listar
    stlflix campanha nova <id> --nome "Natal 2026" [--de <pasta do design>] [--cores "#..,#..,#..,#.."] [--barra #..] [--brilho #..]
    stlflix campanha importar <id> --de <pasta do design>      ícones e logo novos (ou atualizados)
    stlflix campanha conferir <id>

O motor (3-motions/modelos/shark-vsl/motor.mjs) lê o campanha.json; a amostra renderizada sai com
node 3-motions/motions.mjs amostra --campanha <id>.
"""
import json
import os
import re
import subprocess
import unicodedata

import numpy as np

from .vsls import KIT

PASTA = os.path.join(KIT, "2-design-system", "campanhas")
ALTURA_ICONE = 520                                     # padrão do kit BF26
LARGURA_LOGO = 1680
IMAGEM = (".png", ".webp")
HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")


def slug(nome):
    s = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def pasta(cid):
    return os.path.join(PASTA, cid)


def ler(cid):
    try:
        return json.load(open(os.path.join(pasta(cid), "campanha.json"), encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def icones(cid):
    p = pasta(cid)
    return sorted(n[:-4] for n in os.listdir(p) if n.endswith(".png") and not n.startswith("logo")) if os.path.isdir(p) else []


def listar():
    """[{id, nome, icones, logo}] das campanhas (pastas que começam com "_" são de teste e ficam de fora)."""
    if not os.path.isdir(PASTA):
        return []
    return [dict(id=c, nome=ler(c).get("nome") or c, icones=icones(c), logo=os.path.exists(os.path.join(pasta(c), "logo-kv.png")))
            for c in sorted(os.listdir(PASTA)) if os.path.isdir(pasta(c)) and not c.startswith("_")]


def _rgba(arquivo):
    """(altura, largura, pixels RGBA) decodificados pelo ffmpeg."""
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                        "-of", "csv=p=0", arquivo], capture_output=True, text=True, check=True)
    w, h = map(int, r.stdout.strip().split(",")[:2])
    px = subprocess.run(["ffmpeg", "-v", "error", "-i", arquivo, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgba", "-"],
                        capture_output=True, check=True).stdout
    return h, w, np.frombuffer(px, np.uint8).reshape(h, w, 4)


def _preparar(origem, destino, altura=None, largura=None):
    """Recorta a borda transparente e redimensiona (altura fixa para ícone, largura máxima para logo).
    Devolve um aviso, ou None se ficou tudo certo. Imagem sem transparência não entra."""
    h, w, px = _rgba(origem)
    alfa = px[:, :, 3]
    if alfa.min() == 255:
        return "sem fundo transparente: peça ao design o PNG com fundo transparente"
    ys, xs = np.nonzero(alfa > 8)
    if not len(ys):
        return "imagem vazia (tudo transparente)"
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    escala = f"scale=-1:{altura}:flags=lanczos" if altura else f"scale='min({largura},iw)':-1:flags=lanczos"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", origem, "-vf", f"crop={x1 - x0}:{y1 - y0}:{x0}:{y0},{escala}",
                    "-frames:v", "1", "-pix_fmt", "rgba", destino], check=True)
    if altura and (y1 - y0) < altura * 0.8:
        return f"resolução baixa ({y1 - y0} px de altura, o padrão é {altura}): pode ficar borrado, peça uma versão maior"
    return None


def importar(cid, de):
    """Copia as imagens da pasta do design para a campanha. Arquivo com "logo" ou "kv" no nome vira o logo-kv.png.
    Devolve [(arquivo de origem, nome na campanha ou None, aviso)]."""
    destino = pasta(cid)
    os.makedirs(destino, exist_ok=True)
    feitos = []
    for n in sorted(os.listdir(de)):
        base, ext = os.path.splitext(n)
        if ext.lower() not in IMAGEM:
            continue
        logo = bool(re.search(r"logo|\bkv\b|key ?visual", base, re.I))
        nome = "logo-kv" if logo else slug(base)
        saida = os.path.join(destino, nome + ".png")
        temp = saida + ".tmp.png"
        aviso = _preparar(os.path.join(de, n), temp, altura=None if logo else ALTURA_ICONE, largura=LARGURA_LOGO if logo else None)
        if os.path.exists(temp) and not (aviso or "").startswith(("sem fundo", "imagem vazia")):
            os.replace(temp, saida)
            feitos.append((n, nome, aviso))
        else:
            if os.path.exists(temp):
                os.remove(temp)
            feitos.append((n, None, aviso))
    return feitos


def nova(cid, nome, de=None, cores=None, barra=None, brilho=None):
    if cid != slug(cid):
        raise ValueError(f"use um código simples para a campanha, ex.: {slug(cid) or 'natal26'}")
    if os.path.exists(pasta(cid)):
        raise FileExistsError(f"a campanha {cid} já existe: use 'campanha importar' para trocar ícones e logo")
    base = ler("bf26").get("cores") or {}
    degrade = cores or base.get("degrade")
    cfg = {"nome": nome, "logo": {"arquivo": "logo-kv.png", "texto": nome},
           "cores": {"degrade": degrade, "barra": barra or degrade[-1], "brilho": brilho or degrade[0]}}
    os.makedirs(pasta(cid))
    json.dump(cfg, open(os.path.join(pasta(cid), "campanha.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return importar(cid, de) if de else []


def conferir(cid):
    """Problemas que estragariam os motions da campanha (lista vazia = tudo certo)."""
    if not os.path.isdir(pasta(cid)):
        return [f"a campanha {cid} não existe em 2-design-system/campanhas"]
    erros, cfg = [], ler(cid)
    if not cfg:
        erros.append("falta o campanha.json (ou ele está com erro de escrita)")
    cores = cfg.get("cores", {})
    for c in list(cores.get("degrade") or []) + [cores.get("barra"), cores.get("brilho")]:
        if c is not None and not HEX.match(str(c)):
            erros.append(f"cor inválida: {c} (use o formato #RRGGBB)")
    if cfg and len(cores.get("degrade") or []) < 2:
        erros.append("o degradê precisa de pelo menos 2 cores")
    if not os.path.exists(os.path.join(pasta(cid), "logo-kv.png")):
        erros.append("falta o logo-kv.png (a peça 'logo' do plano não vai funcionar)")
    nomes = icones(cid)
    if not nomes:
        erros.append("nenhum ícone (.png) na campanha")
    for n in nomes:
        if n != slug(n):
            erros.append(f"nome de ícone com espaço, acento ou maiúscula: {n}.png (use {slug(n)}.png)")
        h, _, px = _rgba(os.path.join(pasta(cid), n + ".png"))
        if px[:, :, 3].min() == 255:
            erros.append(f"{n}.png sem fundo transparente")
        elif abs(h - ALTURA_ICONE) > 2:
            erros.append(f"{n}.png com {h} px de altura (o padrão é {ALTURA_ICONE}: importe de novo com 'campanha importar')")
    return erros
