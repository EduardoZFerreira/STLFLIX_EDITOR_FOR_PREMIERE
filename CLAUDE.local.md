# Nesta máquina: Premiere Pro no lugar do FilmCraft

**Isto vale para quem usa o Premiere no lugar do FilmCraft e tem prioridade sobre o `CLAUDE.md` e as skills.** Aqui o editor usa o **Adobe Premiere Pro**, operado pelo conector MCP (ferramentas `mcp__premiere-pro__*`). O FilmCraft não é usado: ignore `stlflix abrir`, a porta 9876, o token e o aviso "[FALTA] FilmCraft" do instalador.

Esta versão do kit é uma adição ao STLFLIX_EDITOR original (`sherecks/STLFLIX_EDITOR`): só três arquivos novos, `CLAUDE.local.md`, `premiere.cmd` e `4-filmcraft/stlflix/premiere.py`, e nenhum arquivo do kit foi alterado. Eles vivem na branch `premiere` do fork `EduardoZFerreira/STLFLIX_EDITOR_FOR_PREMIERE`. Para usar, clone o fork nessa branch e instale o kit normalmente (o aviso "[FALTA] FilmCraft" do instalador pode ser ignorado). Não faça PR para o repositório original sem o dono pedir.

## Como funciona

O Python do kit não fala com o Premiere: **quem opera o Premiere é você**, pelo conector. A troca é por arquivos:

- **Premiere → kit**: exporte a sequência em **XML (FCP7)** com `export_as_fcp_xml` e, quando precisar, o áudio em **WAV** com `export_sequence`. O `premiere.cmd` lê esses arquivos.
- **kit → Premiere**: a decupagem vira um **XML de uma sequência nova** (importada com `import_fcp_xml`, `mode: "into_open_project"`); os motions viram uma **lista JSON** que você coloca clipe a clipe.

```
./premiere.cmd --projeto <VSL> decupar <seq> --ref <xml> [--escala 50] [--nome "..."]
./premiere.cmd --projeto <VSL> transcrever <seq> --xml <xml> --wav <wav>
./premiere.cmd --projeto <VSL> motions <seq> --ref <xml> [--plano arquivo] [--escala N]
./premiere.cmd --projeto <VSL> checar --xml <xml> [--xml outro.xml]
./premiere.cmd --projeto <VSL> entregar-xml <arquivo.xml>... [--destino pasta]
```

**Rode o `premiere.cmd` (e o `stlflix.cmd`) pelo PowerShell** (`.\premiere.cmd …`): o kit está numa pasta com espaço ("Editor JP"), e pelo Git Bash o `cmd` do Windows quebra o caminho quando algum argumento tem aspas.

Nenhum desses comandos muda o projeto do Premiere: eles só leem e escrevem arquivos. Quem muda o projeto são as ferramentas do conector, e **a regra "mostrar antes de mudar" continua valendo para elas**: mostre o que vai mudar e espere o editor aprovar antes de qualquer `import_fcp_xml`, `overwrite_clip`, `set_clip_*`, `relink_media`, `remove_from_timeline` etc.

Os comandos que não dependem do editor de vídeo continuam no `./stlflix.cmd` de sempre: `painel`, `vsls`, `nova`, `status`, `plano`, `gatilhos`, `blocos`, `campanha`, `transcrever-brutos --pasta <pasta dos brutos>`. O `motions.mjs` (HyperFrames) também não muda.

## Pegadinhas do conector

- **Antes de tudo**: `verify_premiere_connection` (backend `cep`). Confira com `get_project_info` se o projeto aberto é o da VSL. Se for outro, pare e pergunte.
- **Exportar XML abre a janela "Translation Report"** quando a sequência tem efeitos que o XML não carrega (Grow, Shrink, Rounded Crop…). **O conector fica travado até o editor fechar essa janela**: avise logo depois de exportar.
- `export_as_fcp_xml` e `export_sequence` exportam a **sequência ativa**: rode `set_active_sequence` antes.
- `import_fcp_xml` **sempre com `mode: "into_open_project"`**. O padrão (`new_project`) troca o projeto aberto.
- O tamanho e o fps variam (ex.: VSL Cotrim = 1080x1920 a 29,97, com brutos 4K 23,976 em escala 50). Não assuma 2160x3840 nem escala 200: leia da sequência (`--ref`).
- Tempo: o Premiere usa os mesmos 254.016.000.000 ticks por segundo do FilmCraft; as ferramentas aceitam segundos.
- `get_clip_properties` / `get_effect_properties` só acham clipes da **sequência ativa** (`set_active_sequence` antes).
- `import_fcp_xml` cria uma pasta (bin) com o nome do arquivo XML e **reaproveita** os brutos que já estão no projeto (não duplica).
- `set_item_in_out` deixa a marca de entrada/saída no item do projeto; depois de colocar os motions, limpe com `clear_item_in_out`. A saída arredonda para baixo e o clipe pode ficar até 1 quadro mais curto que a lista: é normal.
- `set_clip_scale` só quando a escala do clipe (`get_effect_properties`, efeito Motion) for diferente da lista: um .mov 1080x1920 numa sequência 1080x1920 já entra em 100.
- Testado em 05-11-2026 num projeto de teste (bruto 23,976 em sequência 29,97): cortes, crossfades, escala dos takes, marcadores e motions entram certos, com áudio e vídeo no mesmo ponto do bruto.
- **Cores por seção (`[cor: Rose]` no título da seção da decupagem):** o conector não lê a cor de um clipe da timeline, só a do item do projeto (que fica com a cor do primeiro clipe que o usa). Para saber se as cores chegaram, o editor precisa olhar a timeline. Se vierem todas iguais, não dá para corrigir clipe a clipe pelo conector: ofereça colorir os marcadores de seção (`add_markers_batch` aceita cor) ou o editor aplica à mão, usando os marcadores de seção como guia.
- **Bin duplicado:** o `import_fcp_xml` cria uma pasta com o nome do XML (ex.: `decupagem-vsl.premiere.prproj`) e, quando os brutos estão num caminho do Drive, pode criar cópias novas de C2458/C2459 em vez de reaproveitar os itens que já estavam em `01_FOOTAGEs`. Avise o editor: a sequência nova usa as cópias da pasta nova (mesmos arquivos), e ele pode mover a pasta para dentro de `01_FOOTAGEs`.
- Com muitas seções, o XML traz um marcador por quadro: seções, "Conferir" e "TELA:" do mesmo quadro viram um marcador só (ex.: "BLOCO + Conferir").
- Salvar continua com o editor (**Ctrl+S no Premiere**). Só use `save_project` se ele pedir.

## Cada etapa no Premiere

**Configurar a VSL** (skill `nova-vsl`): no `config.json`, use `"premiere": {"projeto": "<caminho do .prproj>"}` no lugar de `filmcraft.projeto`. Os nomes em `sequencias` são os nomes das sequências no Premiere. Para "abrir o projeto", use `open_project` com esse caminho, só se o editor pedir: isso fecha o projeto atual.

**Transcrever os brutos**: pegue os caminhos dos takes no Premiere (`list_project_items` / `get_full_sequence_info`, campo `sourceMediaPath`) e rode `./stlflix.cmd --projeto <VSL> transcrever-brutos --pasta "<pasta dos brutos>"`.

**Decupar** (skill `decupar`, passos 1 a 3 iguais; muda só a montagem):
1. Exporte o XML de referência de uma sequência do projeto (para o fps e o tamanho): `set_active_sequence` → `export_as_fcp_xml` em `06-transcricoes/_ref-<seq>.xml` → peça para fechar o Translation Report.
2. `./premiere.cmd --projeto <VSL> decupar <seq> --ref <xml> --escala <escala dos takes>` mostra a tabela e grava `06-transcricoes/decupagem-<seq>.premiere.xml`. A escala dos takes está no "Motion" dos clipes da câmera (`get_clip_properties`) ou no `takes.escala` do config.
3. Mostre a tabela; com a aprovação, rode `import_fcp_xml` (`path` = esse XML, `mode: "into_open_project"`). Entra uma **sequência nova** (`<seq> (decupagem dd-mm HHhMM)`), e a sequência original não é tocada (não precisa de backup). Os cortes, os crossfades Cross Fade (+3dB) de 3/10 quadros e os marcadores (blocos, "Conferir", "TELA: …") vêm no XML.
4. Confira com `get_full_sequence_info` (número de clipes e duração batem com o resumo) e peça para o editor revisar. Se ele quiser que essa passe a ser a sequência do config, atualize `sequencias.<seq>` com o nome novo.
- Diferente do FilmCraft: o Premiere não recebe a transcrição nem os marcadores no bruto (visualizador de origem), e os marcadores chegam sem cor.

**Transcrever uma sequência** (skill `transcrever`):
1. `set_active_sequence` → `export_as_fcp_xml` em `06-transcricoes/<seq>.premiere-ref.xml` (fechar o Translation Report).
2. `get_encoder_presets` com `format: "WAV"` → `export_sequence` com esse preset em `06-transcricoes/<seq>_mix.wav` (pode levar alguns minutos; nunca sobrescreva: se existir, mova o antigo para `_… anteriores (dd-mm HHhMM)`).
3. `./premiere.cmd --projeto <VSL> transcrever <seq> --xml <xml> --wav <wav>` gera o `.json`, o `cortes.json` e o documento por blocos, como no kit.

**Encaixar os motions** (skill `encaixar-motions`):
1. Exporte o XML de referência da sequência (como acima) e rode `./premiere.cmd --projeto <VSL> motions <seq> --ref <xml>`. Ele mostra a tabela e grava `06-transcricoes/motions-<seq>.premiere.json`, com cada clipe (`nome_item`, `inicio_s`, `entrada_s`, `saida_s`), a trilha (`trilha_video_indice`, 0 = V1) e a `escala` (largura da sequência / 1080 × 100; 100 numa 1080x1920).
2. Mostre a tabela; com a aprovação: `import_media` nos `.mov` que ainda não estão no projeto → para cada clipe: `set_item_in_out` no item (entrada/saída) → `overwrite_clip` (`item_id`, `start_seconds`, `track_index`) → `set_clip_scale`. Se já houver motions antigos (.mov) na trilha, mostre e peça antes de tirar (`remove_from_timeline`).
3. Confira com `get_full_sequence_info` na trilha (`track_index`) e veja se ela está visível (`toggle_track_visibility` só se estiver apagada).

**Enquadrar os takes**: `set_clip_scale` / `set_clip_anchor_point` (ou `set_clip_properties_batch`) nos clipes da V1 cujo nome começa com `takes.prefixo`. Mostre quantos clipes vão mudar antes.

**Checar antes de exportar** (skill `finalizar`):
- `./premiere.cmd --projeto <VSL> checar --xml <xml da sequência>`: trilha desligada com clipes, áudio faltando, mídia que não existe no disco.
- `check_offline_media`: mídia offline no Premiere. `audit_timeline_health` para buracos e clipes desligados.
- Quadro preto (Drive ilegível): `export_frame` de 1 quadro por arquivo do Drive e meça a luma com ffmpeg (`scale=54:96,format=gray`; média < 4 = preto).
- Pan de um lado só / som dobrado: veja `get_clip_volume` e `get_track_info` nas trilhas de áudio.

**Reconectar a mídia do Drive** (MEDIA UNREADABLE): `check_offline_media` → `relink_media` com o mesmo caminho (mostre a lista antes).

**Entregar os XMLs**: para cada sequência, `set_active_sequence` → `export_as_fcp_xml` na pasta temporária → `./premiere.cmd --projeto <VSL> entregar-xml <arquivos> [--destino]` (guarda os anteriores em `_XML anteriores (…)`).

**Exportar o vídeo**: só quando o editor pedir, com `export_sequence` e o preset que ele escolher.
