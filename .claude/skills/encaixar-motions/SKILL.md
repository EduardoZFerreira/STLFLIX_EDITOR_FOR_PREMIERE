---
name: encaixar-motions
description: Coloca os motions renderizados na timeline do FilmCraft (V2, escala 200) no tempo de cada frase-gatilho, e aplica o enquadramento padrão dos takes. Use quando o editor pedir para adicionar/encaixar os motions numa sequência ou ajustar escala e âncora dos takes.
---

# Encaixar os motions e enquadrar

Precisa: FilmCraft aberto pelo `abrir`, transcrição da sequência (`06-transcricoes/<seq>.json`) e os `.mov` em `05-motions`.

## Motions

1. Mostre o plano de encaixe (não muda nada):
   `./stlflix.cmd --projeto <VSL> motions <seq>`
   Repasse a tabela: timecode de cada motion, nota da frase e o que ficou de fora (frase não achada, sem `.mov`, cena de outro trecho). Se o config tem um plano por sequência, ele usa o da `<seq>`; outro plano: `--plano <caminho>`.
2. Espere a aprovação ("Coloque…"). Antes de aplicar numa sequência que já tem motions ajustados à mão, sugira duplicar a sequência como backup.
3. `./stlflix.cmd --projeto <VSL> motions <seq> --aplicar`
   Ele tira os `.mov` antigos da V2, coloca os novos (escala 200) e liga a trilha.
4. Confira alguns quadros com `file.exportFrame` (veja `CLAUDE.md` → operar o FilmCraft) e peça para o editor revisar na timeline e **salvar com Ctrl+S**.

## Enquadramento dos takes

1. `./stlflix.cmd --projeto <VSL> enquadrar [seqs]` mostra quantos takes estão fora da escala/âncora do config.
2. Com o ok: `enquadrar [seqs] --aplicar`. Vale também dentro de sequências aninhadas. Só mexe nos clipes cujo nome começa com `takes.prefixo`.
3. Lembre o Ctrl+S.

## Se algo não aparece

- Motion na timeline mas não no monitor/render: trilha V2 desligada. O `--aplicar` liga; se foi importado de XML, ela pode vir desligada de novo (`checar` acusa).
- Motion no lugar errado: a frase aparece duas vezes na montagem. Peça ao editor uma frase-gatilho mais específica no plano.
