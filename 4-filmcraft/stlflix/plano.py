"""Plano de cenas (escrito pelo editor a partir da transcrição e da copy).

Formato, uma cena por item de lista:

    ## Bloco 05 · Luan
    - **B05A** · Caminho 1 · Marketplace — "O primeiro caminho é o marketplace"
      tela: CAMINHO 1 / Marketplace        ← linhas recuadas são notas para o motion (o encaixe ignora)

- **B05A** é o código da cena: o .mov renderizado se chama B05A-qualquer-coisa.mov.
- Depois do travessão (—), entre aspas, a FRASE-GATILHO: as primeiras palavras que a pessoa fala quando o motion
  deve aparecer. Copie da transcrição, não do roteiro (o que vale é o que foi falado).
- O título "## Bloco NN" agrupa as cenas; ele ajuda a achar a frase certa quando ela se repete no vídeo.
"""
import re

CENA = re.compile(r'^\s*[-*]\s*\*\*\s*([A-Z]{1,3}\d+[A-Z]*\d*)\s*(?:·\s*([^*]*?))?\s*\*\*\s*(?:·\s*(.*?))?\s*[—–-]{1,2}\s*["“](.+?)["”]')
BLOCO = re.compile(r"^#{2,3}\s*(?:Bloco|BLOCO|Lead|LEAD)\s+([0-9A-Z]+)")


def ler(caminho):
    """[{id, nome, gatilho, bloco, linha}] na ordem do arquivo."""
    cenas, bloco = [], None
    for k, linha in enumerate(open(caminho, encoding="utf-8"), 1):
        m = BLOCO.match(linha)
        if m:
            bloco = m.group(1).lstrip("0") or "0"
            continue
        m = CENA.match(linha)
        if m:
            nome = (m.group(2) or m.group(3) or "").strip(" ·")
            cenas.append(dict(id=m.group(1), nome=nome, gatilho=m.group(4).strip(), bloco=bloco, linha=k))
    return cenas


def validar(cenas):
    """Erros comuns de escrita do plano."""
    erros, vistos = [], set()
    for c in cenas:
        if c["id"] in vistos:
            erros.append(f"linha {c['linha']}: código repetido {c['id']}")
        vistos.add(c["id"])
        if len(c["gatilho"].split()) < 3:
            erros.append(f"linha {c['linha']}: {c['id']} tem frase-gatilho curta demais (use 4 a 8 palavras)")
    return erros
