---
name: nova-vsl
description: Cria e configura a pasta de uma VSL nova onde o editor quiser no computador (config.json, roteiro, pastas de assets), escolhe a campanha e liga o projeto do FilmCraft. Use quando o editor começa uma VSL nova, pede para configurar o projeto, ou traz a pasta de uma VSL de outro lugar.
---

# Começar uma VSL

1. **Nome**: pergunte o nome curto da VSL (sem espaços, ex.: `VSL-Ender-3`) se ele não disse. Confira com `./stlflix.cmd vsls` que não existe outra com o mesmo nome.
2. **Onde salvar**: a pasta fica onde o editor quiser; tudo o que o kit gerar para a VSL vai para dentro dela. Pergunte onde. Sugestões:
   - junto do projeto do FilmCraft (a pasta onde está o `.fcproj`), se ele já existe;
   - num disco do computador, **não no Google Drive**: os renders dos motions ficam lentos e a pasta de trabalho usa atalhos que o Drive não aceita.
   Se ele não souber o caminho, rode `./stlflix.cmd escolher-pasta`: abre a janela do Windows e devolve o caminho escolhido. A VSL vai numa subpasta com o nome dela dentro do que ele escolher.
3. **Campanha**: liste as pastas de `2-design-system/campanhas/` e pergunte qual é a da VSL (cores e elementos da campanha nos motions). Se só existir uma, confirme com ele.
4. Crie: `./stlflix.cmd --projeto "<pasta escolhida>/<VSL>" nova --nome "<nome legível>" --campanha <campanha>`. O comando já anota a VSL na lista deste computador; dali em diante use só `--projeto <VSL>`.
5. Preencha o `config.json` da VSL junto com o editor:
   - `filmcraft.projeto`: caminho do `.fcproj` (peça para ele salvar o projeto antes, se ainda não existe).
   - `sequencias`: chave curta → nome exato da sequência no FilmCraft (`"corpo": "Corpo decupado"`, `"lead-a": "Lead A"`). Com o FilmCraft aberto pelo `abrir`, o `status` mostra se os nomes batem.
   - `takes`: `prefixo` do nome dos arquivos da câmera (ex.: `C23`), `escala` e `ancora` do enquadramento aprovado. Pergunte o enquadramento desta VSL; se o editor ajustou um take à mão, leia a escala/âncora dele com `sequence.inspect` e use os mesmos valores. (Referência: na VSL-Shark foi escala 114, âncora [1080, 1900].)
   - `motions.referencia`: um quadro do apresentador (PNG 1080×1920) em `04-plano-de-cenas/referencia.png`, só para a prévia. Pode exportar com `file.exportFrame`.
   - `transcricao.nomes` e `grafias`: nomes de produto que o Whisper precisa acertar.
   - `blocos.versao_curta`: `["curto"]` se houver uma sequência com a versão curta das falas.
   - `drive.entrega_xml`: pasta no Drive onde os XMLs são entregues.
   - `plano_de_cenas` pode ser um caminho só ou um por sequência (`{"corpo": "...", "curto": "..."}`): cada sequência com falas diferentes precisa do seu plano.
6. O roteiro vai em `01-roteiro/teleprompter.txt`, com os blocos marcados `--- BLOCO 5 · Título ---` (leads: `--- LEAD A · Título ---`). É ele que divide a transcrição por blocos. Se o roteiro do editor não tiver as marcações, ofereça marcar e mostre antes de salvar.
7. Brutos e B-rolls: se ficam no Drive, não copie; deixe um atalho ou anote o caminho.
8. Rode `./stlflix.cmd --projeto <VSL> abrir` e depois `status`, e mostre o que falta. Lembre que o painel (`./stlflix.cmd painel` ou o atalho "Painel STLFLIX" da área de trabalho) já mostra a VSL nova no menu.

**VSL que já existe em outra pasta** (copiada de outro editor, movida de disco, criada antes desta versão do kit): `./stlflix.cmd vsls --anotar "<pasta>"`. Para tirar da lista sem apagar nada: `./stlflix.cmd vsls --tirar <VSL>`.

O exemplo completo de plano fica em `04-plano-de-cenas/EXEMPLO-plano-de-cenas.md`.
