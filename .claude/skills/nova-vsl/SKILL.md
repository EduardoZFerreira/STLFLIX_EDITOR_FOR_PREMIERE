---
name: nova-vsl
description: Cria e configura a pasta de uma VSL nova em projetos/ (config.json, roteiro, pastas de assets) e liga o projeto do FilmCraft. Use quando o editor começa uma VSL nova ou pede para configurar o projeto.
---

# Começar uma VSL

1. Pergunte o nome curto da VSL (sem espaços, ex.: `VSL-Shark`) se ele não disse. Crie a pasta:
   `./stlflix.cmd --projeto projetos/<VSL> nova --nome "<nome legível>"`
2. Preencha o `projetos/<VSL>/config.json` junto com o editor:
   - `filmcraft.projeto`: caminho do `.fcproj` (peça para ele salvar o projeto antes, se ainda não existe).
   - `sequencias`: chave curta → nome exato da sequência no FilmCraft (`"corpo": "Corpo decupado"`, `"lead-a": "Lead A"`). Com o FilmCraft aberto pelo `abrir`, o `status` mostra se os nomes batem.
   - `takes`: `prefixo` do nome dos arquivos da câmera (ex.: `C23`), `escala` e `ancora` do enquadramento aprovado. Padrão do Shark: escala 114, âncora [1080, 1900]. Se o editor ajustou um take à mão, leia a escala/âncora dele com `sequence.inspect` e use os mesmos valores.
   - `motions.referencia`: um quadro do apresentador (PNG 1080×1920) em `04-plano-de-cenas/referencia.png`, só para a prévia. Pode exportar com `file.exportFrame`.
   - `motions.campanha`: pasta em `2-design-system/campanhas/` (hoje `bf26`).
   - `transcricao.nomes` e `grafias`: nomes de produto que o Whisper precisa acertar.
   - `blocos.versao_curta`: `["curto"]` se houver uma sequência com a versão curta das falas.
   - `drive.entrega_xml`: pasta no Drive onde os XMLs são entregues.
   - `plano_de_cenas` pode ser um caminho só ou um por sequência (`{"corpo": "...", "curto": "..."}`): cada sequência com falas diferentes precisa do seu plano.
3. O roteiro vai em `01-roteiro/teleprompter.txt`, com os blocos marcados `--- BLOCO 5 · Título ---` (leads: `--- LEAD A · Título ---`). É ele que divide a transcrição por blocos.
4. Brutos e B-rolls: se ficam no Drive, não copie; deixe um atalho ou anote o caminho.
5. Rode `./stlflix.cmd --projeto projetos/<VSL> abrir` e depois `status`, e mostre o que falta.

O exemplo completo de plano fica em `04-plano-de-cenas/EXEMPLO-plano-de-cenas.md`.
