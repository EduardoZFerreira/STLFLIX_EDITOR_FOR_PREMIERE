# FilmCraft + IA: guia do que aprendemos editando VSLs

Contexto para continuar o trabalho em outra conversa. Projetos: **VSL-Hugo** (VSL Black November 2026, STLFLIX) e **VSL-Shark** (VSL 682 [BLACK26], apresentado pelo Lincoln). Editor: FilmCraft 0.9.0 no Windows, controlado ao vivo por um agente via canal de controle. O usuário revisa tudo na timeline e salva com Ctrl+S.

> **Leia como aprendizado, não como configuração.** Os caminhos com `C:\Users\joaop\...`, os valores de enquadramento e o estado das seções 8 e 9 são do computador e das VSLs onde isso foi aprendido. Em outra VSL ou outro computador, os caminhos vêm do `config.json` da VSL e o token de `~/.config/filmcraft/control_token` (o `stlflix abrir` já cuida disso).

---

## 1. Como se conectar ao FilmCraft

**Abrir o app com controle:**
```
"C:\Program Files\FilmCraft\filmcraft.exe" --control 9876 "C:\Users\joaop\OneDrive\Desktop\Filmcraft\VSL-Shark.fcproj"
```
- **A partir da versão 0.13, o controle exige um token.** Sem a variável de ambiente `FILMCRAFT_CONTROL_TOKEN` (64 caracteres hexadecimais aleatórios), o servidor de controle fica desligado sem aviso, mesmo com `--control`. O token está em `C:\Users\joaop\.config\filmcraft\control_token`. Abra o app com ele (PowerShell):
  ```
  $env:FILMCRAFT_CONTROL_TOKEN=(Get-Content "$env:USERPROFILE\.config\filmcraft\control_token" -Raw).Trim(); Start-Process "C:\Program Files\FilmCraft\filmcraft.exe" -ArgumentList '--control','9876','"<projeto>.fcproj"'
  ```
  Todo pedido JSON precisa do campo `"token": "<o mesmo valor>"`; sem ele vem "control authentication failed". O `filmcraft-cli --bridge` lê a mesma variável de ambiente.
- Se o app foi aberto sem `--control`, a porta 9876 fica fechada. Peça para o usuário **salvar (Ctrl+S)**, feche com `CloseMainWindow()` (PowerShell) e reabra com o comando acima. Confira a porta antes de continuar.
- Protocolo: uma linha JSON por pedido em 127.0.0.1:9876, no formato `{"id", "method", "params"}`, com resposta `{"ok", "result"|"error"}`.
- Métodos: `engine.execute` (`{command, params}`), `ui.screenshot`, `ui.click`, `ui.set`, `ui.inspect`, `ui.elements`, `perf.stats`.

**Cliente Python mínimo** (usado em todos os scripts):
```python
import json, os, socket
class FC:
    def __init__(self, port=9876):
        self.s = socket.create_connection(("127.0.0.1", port))
        self.f = self.s.makefile("rw", encoding="utf-8"); self.n = 0
        self.token = os.environ.get("FILMCRAFT_CONTROL_TOKEN") or open(
            os.path.expanduser(r"~\.config\filmcraft\control_token")).read().strip()   # FilmCraft >= 0.13
    def call(self, method, **params):
        self.n += 1
        req = {"id": self.n, "method": method, "params": params, "token": self.token}
        self.f.write(json.dumps(req) + "\n"); self.f.flush()
        r = json.loads(self.f.readline())
        if not r.get("ok"): raise RuntimeError(f"{method} {params}: {r.get('error')}")
        return r.get("result")
    def run(self, command, **params):
        return self.call("engine.execute", command=command, params=params)
```

**CLI:** `C:\Program Files\FilmCraft\filmcraft-cli.exe`
- `commands <filtro>` lista os comandos com a assinatura dos parâmetros. **Sempre confira a assinatura antes de usar um comando novo.** `describe <id>` mostra um comando.
- `--bridge 127.0.0.1:9876 --compact exec <cmd> '<json>'` executa no app aberto.
- **Modo sem interface:** `--project X.fcproj [--save | --save-as Y] exec|run|inspect|render|export`. Útil para tarefas paralelas sem tocar no app, por exemplo o bake de LUT. Trabalhe sempre numa **cópia** do projeto.

**Python no Windows:** rode com `python -X utf8`. Dentro do venv, use `-I -X utf8` (o `-I` ignora `PYTHONIOENCODING`).

---

## 2. Unidades de tempo

- **Ticks:** 254.016.000.000 por segundo. 1 frame a 23,976 fps = 10.594.584.000 ticks.
- `sequence.inspect` devolve `start`/`end`/`sourceIn`/`sourceOut` em ticks e `startFrame`/`endFrame` em frames.
- **Timecode:** a timeline mostra 24 frames nominais, então `frames = (min·60 + s)·24 + f`. O segundo real difere em 0,1%. Fale com o usuário sempre em timecode (MM:SS:FF).
- **Keyframes ficam em tempo de mídia (source).** Cópias e cortes de um clipe levam todos os keyframes junto.

---

## 3. Comandos e pegadinhas de parâmetro

| Comando | Observação |
|---|---|
| `sequence.inspect {item?}` | **Passe `item=<id da sequência>`** sempre que possível. A sequência ativa muda sozinha, por exemplo quando o usuário clica em outra aba. |
| `sequence.open {item}` | Torna a sequência ativa (muda a tela do usuário). |
| `project.inspect` | Árvore em `root.children[]`, com `{item, type: "Sequence"|"Still Image"|..., name, duration}`. |
| `timeline.place` | `{item, track:"V1"|"V3"|"new", time, sourceIn, duration, insert:false, audio:false/video:false}` → `{"clips":[ids]}` |
| `timeline.move` | `{moves:[{clip, track, time}], insert:false, linked:false, copy:true}` → `copied:[ids]`. Use para **copiar um clipe com os keyframes**. |
| `timeline.trim` | `{clip, edge:"in"|"out", mode:"regular", delta: ticks}` |
| `edit.clear {clips:[ids]}` | Remove sem ripple. |
| `effects.apply {clips:[ids], effect:"lumetri"}` | É `clips` (lista), não `clip`. O índice do efeito novo **não** é o último: localize por nome em `c["effects"]`. |
| `effects.setParam {clip, effect:index, param, value, time?, keyframe?}` | Parâmetros do tipo "choice" vão como **índice**, nunca como nome. `motion`: `scale` (%), `position` [x,y], `anchor` [x,y]. |
| `effects.setInterpolation {clip, effect, param, mediaTime, interpolation}` | `mediaTime` tem que ser exatamente `clip.sourceIn + (tseq − clip.start)`. Se o keyframe foi encostado no fim do clipe, recalcule, senão dá "no keyframe at that time". |
| `effects.toggleAnimation` | Desliga a animação e apaga os keyframes do parâmetro. |
| `lumetri.setInputLut {clip, lut:"builtin:slog3-sgamut3cine-to-rec709"}` | |
| `sequence.deleteTracks {video: id}` | **Nunca use `"empty"`** se o usuário tem trilhas vazias de propósito (havia uma V4). Apague só a trilha temporária, pelo id. |
| `project.select {items:[seqId]}` + `edit.duplicate` | Backup da sequência antes de operações destrutivas. |
| `clip.rename {clip, name}` | |
| `file.import {paths:[...]}` | Importa para a raiz do projeto. |
| `media.status` | Lista `{item, name, path, status, proxy}`. `status` diz "online" mesmo quando o arquivo está ilegível (ver seção 6). |
| `media.relink {item, path}` | Reconectar no mesmo caminho resolve o "MEDIA UNREADABLE". |
| `media.attachProxies {item, path}` | |
| `file.exportFrame {path, format:"png", depth:16, target:"program", time}` | O PNG sai **RGBA**. Use para checar a renderização real. |
| `scopes.read` | Resumo de luma/cor num tempo. Rápido para saber se uma camada está renderizando. |
| `playhead.set {time}` + `ui.screenshot {path, panel:"program"}` | O retângulo do quadro dentro da captura **muda quando o painel é redimensionado**: localize-o antes de recortar. |
| `ui.click {id:"timeline.track.A3.muted"}` | Muta uma trilha. `mixer.setStrip mute` **não** muta a trilha. |
| `file.exportMedia` | `{path, preset:"Social Vertical 1080×1920", sequence, range:"inOut"|"custom", startSeconds?, endSeconds?, loudnessLufs:-14, hardwareEncoding:"auto", wait:false}` |
| `jobs.list` / `jobs.cancel {job}` | Acompanhar e cancelar exportações. `export.queue.cancel` não cancela jobs criados por `file.exportMedia`. |
| `file.exportInterchange {format:"xml", path, sequence}` | FCP7 XML (xmeml). Leva cortes, escala e âncora (`centerOffset`) e os .mov de motion. |
| `lut.export`, `lut.import`, `prefs.get/set`, `prefs.schema` | |

---

## 4. Estrutura do arquivo .fcproj (leitura sem o app aberto)

- É um JSON, com o projeto em `p["project"]["items"]`: um dicionário cuja **chave é string** (`items["14"]`).
- **Sequência:** `items[id]["kind"]["Sequence"]` traz `video_tracks[]`, `audio_tracks[]`, `markers[]` e `settings`. Cada clipe tem `{id, item, name, start, duration, source_in, speed, enabled, effects[]}`. Os parâmetros dos efeitos têm a forma `{"value": {"Float": 114.0}}`, `{"Vec2": {...}}` ou `{"Text": ...}`. No arquivo o id do clipe é `id`; na API ao vivo é `clip`.
- **Caminho da mídia:** `items[id]["kind"]["Media"]["media"]["File"]["path"]`.
- **Autosaves** ficam em `Desktop\Filmcraft\Auto-Save`; o snapshot de recuperação fica em `%APPDATA%\FilmCraft\Recovery\<n>-<pid>\snapshot.fcproj`.
- **Para analisar com o app aberto sem controle**, copie o .fcproj salvo e leia a cópia.

---

## 5. Fluxos que funcionaram

### 5.1 Transcrição
- Use faster-whisper `large-v3-turbo` em CUDA (RTX 4060), com `word_timestamps=True`, `language="pt"` e `condition_on_previous_text=False`. No `initial_prompt`, liste os nomes próprios: STLFLIX, STLIA, STL Seller, Tales, Cotrim, Luan, Lincoln, Igor, Arena 3D, TikTok Shop, Shopee…
- Carregue o WAV (16 kHz mono s16) com numpy. O PyAV deu erro de metadata.
- **Para ter tempos de timeline**, reconstrua o áudio da sequência: para cada clipe da A1, extraia `[sourceIn, sourceIn+dur]` com ffmpeg e coloque o trecho na posição `start` do buffer; o resto fica em silêncio. Transcreva esse WAV inteiro. Salve um mapa dos clipes para anotar "take + tempo no bruto" em cada fala.
- **Repetições escondidas:** o Whisper funde frases repetidas numa palavra esticada. Marque palavras com mais de ~0,8 s e retranscreva esse trecho isolado.
- **Grafia:** corrija nomes conforme o roteiro (Steliflix/STL Flix → STLflix, STLA → STLIA, Thales → Tales, Luana → Luan, Higor → Igor, "esse Netflix" → "a STLflix").
- **Divisão por blocos:** ache a primeira frase de cada bloco do roteiro (teleprompter) na transcrição com difflib, em ordem, e com override quando a gravação abre diferente do texto escrito.

### 5.2 Letterings e motions (HyperFrames → timeline)
- São .mov ProRes 4444 com alfa, em 1080×1920. Vão na **V2 em escala 200%** (sequência 2160×3840), sem mudar a posição.
- **Gatilho:** a primeira frase da cena, achada nos timestamps de palavra com difflib. A cena **começa 0,2 s antes** da primeira palavra.
- **Quando não cabe** antes da próxima cena (folga de 0,1 s): mantenha o começo e emende os **últimos 0,5 s (fade)** do .mov, em dois clipes. A última cena termina com a sequência.
- Antes de aplicar, mostre um plano em tabela (cena, tempo, inteiro/encurtado, confiança). Avise quando um motion perde mais da metade da duração.

### 5.3 B-roll 16:9 em sequência 9:16 (2160×3840)
- **Preencher a altura:** fonte 1920×1080 → `S = 3840/1080 = 355,556%`; fonte 4K 3840×2160 → `S = 177,778%`.
- **Posição para centrar o recorte em `cx` (pixels da fonte):** `x = 1080 + (cx_centro − cx)·S`, `y = 1920 + (cy_centro − cy)·S`. A janela visível tem `2160/S` px de largura da fonte (607 px no 1080p, 1215 px no 4K). Zoom extra: `S·z`, com cx/cy dentro dos limites.
- **Sem letterbox, nunca.** O usuário rejeita o "fit" de 112,5%.
- **Enquadramento por keyframes de Posição na timeline**, nunca por render prévio. O usuário revisa na timeline antes de qualquer render.
- **Rastreio da peça** (takes de produto em tripé): subtraia o fundo usando a mesa vazia como referência, ignore pele, tatuagem e a área com luz piscando, calcule o centróide ponderado por saturação, suavize (mediana + EMA) e gere um keyframe a cada 0,5 s quando a posição andar mais de 3%. Para descartar trechos: área da peça abaixo de 1,8% (mesa vazia) e área total acima de 40% (lente bloqueada ou desfoque).
- **Revisão:** gere uma folha de contato com os recortes 9:16 aplicados antes de mexer na timeline.
- **Insertos visuais na V3 sem áudio.** Para reaproveitar um trecho já enquadrado no pool, copie com `timeline.move copy:true` (os keyframes vão junto), apare e mova para a V3.
- **Vãos livres:** procure trechos da fala do Hugo sem nada na V2 e na V3 e cruze com a transcrição para sugerir onde entra cada B-roll. **Proponha antes; só coloque depois do "Coloque…" do usuário.** Cuidado com números na tela que contradizem a fala.

### 5.4 Cor
- **Câmera:** Sony FX30 em S-Log3/S-Gamut3.Cine (marcada como Rec.709) e subexposta ~1–1,5 stop, o que gera granulação.
- **Grade aprovada ("opção B", VSL-Hugo):** input LUT `builtin:slog3-sgamut3cine-to-rec709` + Lumetri com temperatura −75, tint −20, exposição +0,6, contraste 10, realces −10, pretos −20, saturação 85.
- **Levar a cor para outro app (bake em LUT):** gere uma HALD 16-bit 512×512 (64³), importe num projeto sem interface, numa sequência 512×512. Renderize primeiro **sem efeito** e compare com a entrada (erro precisa ser menor que 2/255, prova de que não há conversão escondida). Depois aplique o Lumetri idêntico, renderize com `file.exportFrame depth:16` e grave o .cube 64 (vermelho variando mais rápido). Resultado: 0,6/255 de erro médio em relação ao FilmCraft.
- **DaVinci Resolve 21.1 gratuito não aceita script externo** e só lista Lua no menu Workspace > Scripts. A ponte Python não roda. Saídas: LUT, XML ou arquivos de timeline para importar.

### 5.5 Áudio (VSL-Hugo)
- **Cadeia aprovada na A1:** EQ paramétrico passa-alta 80 Hz (12 dB/oit.) → notch 2415 Hz (chiado do motor de passo das impressoras), super estreito, −30 dB → DeNoise 15.
- **Manter o DeNoise em 20 ou menos.** Em 40 a voz ficou robotizada. Um notch em 6620 Hz abafou a voz e foi descartado.
- **Exportação:** −14 LUFS.

---

## 6. Problemas e como resolver

- **"MEDIA UNREADABLE" / mídia do Google Drive (G:).** O FilmCraft perde a leitura dos originais no G: de vez em quando, mesmo com o ffmpeg lendo normal e `media.status` dizendo "online".
  - Sintomas: B-rolls sem proxy somem do monitor, `file.exportFrame` sai preto e **a exportação sai preta sem nenhum aviso** (`offlineMedia` vazio). Um VSL de 19 min saiu ~80% preto.
  - Correção: `media.relink` de **todos** os itens do G: no mesmo caminho.
  - **Antes de qualquer exportação:** reconecte tudo e teste alguns quadros com `file.exportFrame`. Luma perto de 0 = problema.
  - Tenha proxies locais para os takes da câmera (`C:\FilmCraft\Proxies\VSL-Hugo\<nome>_Proxy.mov`). O monitor usa o proxy, mas a exportação usa o original.
- **Importação de XML (FCP7) do Premiere perde áudio:** os cortes de áudio encostados em crossfade vêm no XML com `start`/`end = -1` (a posição é dada pela transição), e o FilmCraft os descarta sem aviso. Na sequência "TAKES EXTRAS · VERSÕES CURTAS" entraram só 6 dos 81 cortes de áudio por trilha. Depois de importar, compare a contagem de clipes de áudio com a do XML. Para reconstruir: um corte de áudio por corte de vídeo (mesma posição e mesmo trecho da fonte), com o mesmo pan, e depois `sequence.applyAudioTransition {clip, effect:"constant_power", frames:6, edge:"out"}` nos cortes que tinham crossfade.
- **Sequência aninhada com pan 0 nas duas trilhas** (A1 e A2) toca o áudio dobrado (+5 a 6 dB). Use A1 = −100 e A2 = +100, como o resto. Para medir o nível, exporte um WAV (`file.exportMedia format:"wav"`) e use o `volumedetect` do ffmpeg.
- **Motions colocados que não aparecem no render:** confira se a trilha está ligada, porque a sequência pode ter a V2 desligada (`enabled: false` no `sequence.inspect`). Para religar: `timeline.setTrack {track: <id da trilha>, enabled: true}` (a sequência precisa estar aberta). Depois de colocar, sempre renderize alguns quadros com `file.exportFrame` para conferir.
- **Exportação lenta:** cerca de 2,7–3 quadros/s numa sequência 2160×3840 com takes 4K HEVC 10-bit, Lumetri e letterings ProRes. 19 min levam ~2h15.
  - Meia resolução (`scale:0.5`) e NVENC **não aceleram**. A GPU fica ociosa (~7%): o gargalo é o processamento no CPU.
  - A cadeia de áudio da A1 leva ~6× o tempo real, mas roda em paralelo.
  - O modo sem interface é igualmente lento por processo.
- **`wait:true` na exportação** trava o canal de controle durante todo o render e estoura o limite de 60 s da ponte, mas o job continua. Use `wait:false` e acompanhe com `jobs.list`.
- **Monitor de exportação:** a cada 5 min renderize um quadro de um take e de um B-roll do G:. Ao terminar, varra o arquivo a cada 5 s procurando trechos pretos.
- **Proxies com ffmpeg** saturaram o CPU e travaram o FilmCraft. Rode o ffmpeg com prioridade Idle.
- **Gravação no G: (Drive):** escreva primeiro numa pasta local e copie depois. Confira com `cmp`.

---

## 7. Preferências do usuário (seguir sempre)

- Responder em **português do Brasil**, com timecode da timeline.
- **Revisão na timeline antes de renderizar**: nada de render ou bake sem a aprovação dele.
- **Propor antes de colocar.** O padrão dele para autorizar é "Coloque…". Não mexer no projeto quando ele diz que está em outro.
- **Backup antes de operações destrutivas** (duplicar a sequência). Nunca sobrescrever exportações antigas: mover para uma subpasta `_… anteriores (data)`.
- **Não apagar trilhas vazias** que ele criou.
- **Processamento sutil**, sem efeito "robótico".
- **Lembrar de salvar (Ctrl+S)** ao fim de cada etapa.

**Decupagem (estilo medido nos ajustes dele):**
- Cabeça ~2 frames antes do início audível da fala. Use a energia do áudio, porque o início de palavra do Whisper adianta 0,3–0,5 s.
- Cauda 5–6 frames depois da fala.
- Cortar pausas e respirações de 0,3 s ou mais.
- Manter só a última repetição limpa quando ele tropeça.

**Crossfade de áudio (Constant Power, centrado):** 3 frames no meio de frase; ~9–12 frames em fim de frase, troca de assunto e entrada do CTA.

**Enquadramento dos takes:**
- VSL-Hugo: escala 110% e posição Y 1770 (subiu 150 px).
- VSL-Shark: **escala 114% e âncora Y 1900**, aplicado em todos os leads e no corpo.

---

## 8. Caminhos

Histórico das VSLs do Hugo e do Shark, no computador onde foram editadas. Não use em outra VSL.

| O quê | Caminho |
|---|---|
| Projetos FilmCraft | `C:\Users\joaop\OneDrive\Desktop\Filmcraft\VSL-Hugo.fcproj`, `…\VSL-Shark.fcproj` |
| Transcrições geradas | `C:\Users\joaop\OneDrive\Desktop\Filmcraft\Transcricoes\` (Hugo, B-rolls, Cruzamento, Shark Leads A-G, Shark Corpo) |
| LUT da grade B | `C:\Users\joaop\OneDrive\Desktop\Filmcraft\LUTs\VSL_Hugo_grade_B.cube`; cópia em `C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\LUT\VSL Hugo\` |
| VSL-Hugo · câmera | `G:\Drives compartilhados\GROWTH 2026\1. Campanhas\[BRA] Brasil\[BRA] Black Friday 2026\VSLs\659_[BLACK26]\Brutas\PT` (C2345–C2351) |
| VSL-Hugo · B-rolls | `…\659_[BLACK26]\Brutas\B - Rolls`; peças 3D em `G:\Drives compartilhados\MKT 2\STUDIO\00 - ASSETS\11. Assets Freela\Peças\02` |
| VSL-Hugo · letterings | `C:\Users\joaop\OneDrive\Desktop\Hyperframes\videos\vsl-black-november\renders\cenas` (plano em `plano-de-cenas.md`) |
| VSL-Shark · projeto | `G:\…\VSLs\682_[BLACK26]\` (Brutas, Copy, Assets) |
| VSL-Shark · roteiro | `…\682_[BLACK26]\Copy\VSL BLACK NOVEMBER 2026 · TELEPROMP.txt` (leads A–G + Atual; corpo em blocos 2–30) |
| VSL-Shark · motions | `…\682_[BLACK26]\Assets\Motion\Lead X - …\*.mov` (há um `LEIAME.txt`) |
| VSL-Shark · XMLs | `…\682_[BLACK26]\Assets\Lead A.xml` … `Lead G.xml`, `Corpo decupado sem cross fade.xml`; versões antigas em `_XML anteriores (22-10 16h)` |
| Proxies | `C:\FilmCraft\Proxies\VSL-Hugo` |

---

## 9. Estado no fim desta conversa (22/10/2026)

Histórico: como as VSLs do Hugo e do Shark estavam nessa data.

**VSL-Shark:**
- Leads A–G com takes em 114%/âncora Y 1900 e motions A1–G8 na V2 (escala 200).
- Corpo "Corpo decupado sem cross fade" com 802 cortes em 114%/âncora Y 1900.
- XMLs atualizados no Drive.
- Transcrições prontas para os motions do corpo (blocos 2–30).
- Os motions do "Lead Atual" (AT1–AT7) existem, mas não há sequência para eles.

**VSL-Hugo:**
- Montagem completa, com Out em 19:05:14.
- B-rolls e peças 3D na V3; grade B, áudio aprovado.
- Exportação completa ainda pendente: a última foi interrompida. Reconectar a mídia do G: antes de exportar.

**DaVinci:** o usuário migrou parte do trabalho para o Resolve gratuito. Lá não há controle por script; use LUT, XML e arquivos de timeline.
