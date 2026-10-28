"""Projeto de VSL: lê projetos/<VSL>/config.json e resolve os caminhos das pastas do modelo.

Caminhos relativos no config.json são relativos à pasta do projeto. Tudo que não estiver no config usa PADRAO.
"""
import copy
import json
import os

PADRAO = {
    "nome": "",
    "filmcraft": {"projeto": ""},                  # caminho do .fcproj
    "sequencias": {},                              # chave curta → nome da sequência no FilmCraft
    "roteiro": "01-roteiro/teleprompter.txt",
    "plano_de_cenas": "04-plano-de-cenas/plano-de-cenas.md",
    "pastas": {"motions": "05-motions", "transcricoes": "06-transcricoes", "exports": "07-exports"},
    "takes": {"prefixo": "C", "escala": 100.0, "ancora": [1080.0, 1920.0]},
    "motions": {"trilha": "V2", "escala": 200.0, "antecedencia_s": 0.2, "fade_s": 0.5, "folga_s": 0.1,
                "minimo_s": 1.0,
                # usados pelo gerador de motions (3-motions/motions.mjs)
                "modelo": "shark-vsl", "campanha": "bf26", "faixa": {"top": 130, "height": 430}, "referencia": "", "hyperframes": "0.8.176"},
    "transcricao": {"modelo": "large-v3-turbo", "idioma": "pt", "nomes": [], "grafias": [], "sinonimos": {}},
    "blocos": {"ancoras": {}, "versao_curta": False},
    "drive": {"entrega_xml": ""},
}


def _merge(base, extra):
    for k, v in extra.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _merge(base[k], v)
        else:
            base[k] = v
    return base


class Projeto:
    def __init__(self, pasta):
        self.pasta = os.path.abspath(pasta)
        arq = os.path.join(self.pasta, "config.json")
        if not os.path.exists(arq):
            raise FileNotFoundError(f"não achei {arq}: copie projetos/_MODELO-VSL e preencha o config.json")
        self.cfg = _merge(copy.deepcopy(PADRAO), json.load(open(arq, encoding="utf-8")))

    def caminho(self, rel):
        return rel if os.path.isabs(rel) else os.path.join(self.pasta, rel)

    def pasta_de(self, chave):
        p = self.caminho(self.cfg["pastas"][chave])
        os.makedirs(p, exist_ok=True)
        return p

    def sequencia(self, chave_ou_nome):
        """Aceita a chave do config ("corpo") ou o próprio nome da sequência."""
        return self.cfg["sequencias"].get(chave_ou_nome, chave_ou_nome)

    def chave(self, chave_ou_nome):
        for k, v in self.cfg["sequencias"].items():
            if chave_ou_nome in (k, v):
                return k
        return "".join(c if c.isalnum() else "-" for c in chave_ou_nome.lower()).strip("-")

    def arquivo_transcricao(self, chave_ou_nome, ext="json"):
        return os.path.join(self.pasta_de("transcricoes"), f"{self.chave(chave_ou_nome)}.{ext}")

    def plano(self, chave=None):
        """Caminho do plano de cenas: um só para o projeto, ou um por sequência ({"corpo": "...", "curto": "..."})."""
        p = self.cfg["plano_de_cenas"]
        if isinstance(p, dict):
            if chave is None:
                return [self.caminho(v) for v in p.values()]
            k = self.chave(chave)
            if k not in p:
                raise KeyError(f"sem plano de cenas para '{k}' em plano_de_cenas do config.json")
            return self.caminho(p[k])
        return self.caminho(p) if chave is not None else [self.caminho(p)]

    def __getitem__(self, k):
        return self.cfg[k]
