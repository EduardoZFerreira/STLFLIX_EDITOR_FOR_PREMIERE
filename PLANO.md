# STLFLIX_EDITOR: plano

Kit para o time de edição produzir **VSLs 9:16 da STLFLIX**. Ele junta o fluxo de edição no **FilmCraft** com os motions da marca feitos no **HyperFrames**. É distribuído como repositório Git: o editor cola o link no **Claude Code**, pede para instalar, e o Claude passa a operar o fluxo seguindo as instruções do repositório.

## Decisões (28/10/2026)

| Tema | Decisão |
|---|---|
| Quem opera | Cada editor usa o **Claude Code**. O repositório traz `CLAUDE.md` e skills com cada etapa; os scripts também funcionam sozinhos. |
| Distribuição | **Repositório Git** `STLFLIX_EDITOR`. Instalação: link → Claude Code → clonar → `instalar.ps1`. |
| Plano de cenas | **O editor escreve**, com base na transcrição e na copy. O kit traz o formato padrão, um exemplo e o gerador de motions. |

## Fluxo que o kit cobre

1. **Roteiro**: teleprompter com `--- BLOCO N · TÍTULO ---`.
2. **Gravação** e cópia dos brutos para o Drive.
3. **Decupagem** no FilmCraft, seguindo `5-guias/estilo-de-edicao.md`.
4. **Transcrição** com Whisper, dividida pelos blocos do roteiro.
5. **Plano de cenas**, escrito pelo editor.
6. **Render dos motions** no HyperFrames: .mov ProRes 4444 transparente, 1080×1920.
7. **Encaixe automático** dos motions na V2, cada um na sua frase.
8. **Acabamento**: escala e âncora dos takes, LUT da câmera, pan do áudio, B-roll 9:16 por keyframes.
9. **Checagens antes de exportar**: mídia do Drive legível, trilhas ligadas, pan, áudio perdido na importação de XML.
10. **Exportação** do vídeo e dos XMLs para o Drive.

## Estrutura

```
STLFLIX_EDITOR/
├─ CLAUDE.md               instruções para o Claude Code operar o kit
├─ stlflix.cmd             atalho para os comandos de edição
├─ COMECE-AQUI.md          para o editor: instalar e começar uma VSL
├─ .claude/skills/         uma skill por etapa (transcrever, encaixar motions, checar antes de exportar…)
├─ painel/                 modelo.html; o stlflix painel gera index.html (ferramentas, o que falta em cada VSL, passo a passo)
├─ 1-instalacao/           instalar.ps1 (ferramentas, ambiente Python, token do FilmCraft)
├─ 2-design-system/        assets STLFLIX: tokens, fontes, logos, ícones, componentes
├─ 3-motions/              template HyperFrames: plano de cenas → .mov
├─ 4-filmcraft/            scripts de edição (conexão, transcrição, encaixe, enquadramento, B-roll, checagens, LUT)
├─ 5-guias/                aprendizados, estilo de edição, problemas comuns
└─ projetos/_MODELO-VSL/   pasta de assets a preencher, copiada para cada VSL nova
   ├─ 01-roteiro/          teleprompter.txt (obrigatório)
   ├─ 02-brutos/           takes da câmera, ou atalho para o Drive
   ├─ 03-b-rolls/
   ├─ 04-plano-de-cenas/   plano-de-cenas.md (o editor escreve)
   ├─ 05-motions/          gerado
   ├─ 06-transcricoes/     gerado
   ├─ 07-exports/          gerado
   └─ config.json          nome, resolução, escala/âncora dos takes, LUT, pasta no Drive
```

## Ferramentas que o editor precisa

| Ferramenta | Para quê | Observação |
|---|---|---|
| ArtCraft Launcher → FilmCraft | Edição | Fixar a versão: a 0.13 passou a exigir `FILMCRAFT_CONTROL_TOKEN` para o controle |
| Claude Code | Operar o kit | |
| Git | Instalar e atualizar o kit | |
| Node.js | HyperFrames (motions) | Versão do HyperFrames fixa no `package.json` (hoje 0.8.176) |
| Python 3.12 | Transcrição e scripts | O instalador cria o ambiente com `faster-whisper` e `numpy` (`4-filmcraft/pyproject.toml`; extra `[gpu]` com NVIDIA) |
| ffmpeg | Áudio, quadros, checagens | |
| Placa NVIDIA (recomendado) | Whisper rápido | Sem GPU funciona, só que mais devagar |
| Google Drive para desktop | Brutos e entregas | Pastas usadas como "disponíveis off-line" evitam o "MEDIA UNREADABLE" |

## Fases

| Fase | Entrega | Status |
|---|---|---|
| 0. Resgatar | Scripts e guias copiados para `4-filmcraft/_legado` e `5-guias` | **feito** |
| 1. Generalizar | `4-filmcraft/stlflix` (CLI com 11 comandos) lendo o `config.json`; modelo de projeto; exemplo de plano; guia de estilo em português | **feito** — testado numa cópia do VSL-Shark |
| 2. Template de motions | `3-motions/motions.mjs` (validar, gerar, prévia, render, migrar) + `2-design-system` + guia `5-guias/plano-de-cenas.md` | **feito** — composições idênticas às do Shark e render idêntico pixel a pixel |
| 3. Instalador | `1-instalacao/instalar.ps1` (`-Verificar`, `-BaixarModelo`) + `stlflix.cmd` + comando `nova` | **feito** — instalação completa testada nesta máquina |
| 4. Claude Code | `CLAUDE.md` + 8 skills em `.claude/skills/` + `COMECE-AQUI.md` | **feito** — falta testar com um editor (Fase 6) |
| 5. Painel | `stlflix painel` → `painel/index.html`: ferramentas (do instalador), status de cada VSL, próximo passo com pedido para copiar, passo a passo e pasta da VSL | **feito** |
| 6. Piloto | Um editor usa o kit numa VSL real | |
| 7. Distribuição | Repositório no GitHub, versão e changelog | |

## Aprendizados da Fase 1

- **A frase-gatilho no plano de cenas resolve o encaixe.** Com a frase escrita pelo editor, 144 de 145 motions do corpo do Shark caíram exatamente no lugar aprovado, em menos de 5 s. O único diferente foi uma fala que aparece duas vezes na montagem.
- **Cada sequência precisa do seu plano.** O plano do corpo completo aplicado ao corpo curto perde cenas, porque o curto usa outras versões das falas. O `config.json` aceita um plano por sequência (`"plano_de_cenas": {"corpo": "…", "curto": "…"}`).
- **As checagens precisam ser testadas com problema de verdade.** Desligar a V2 e jogar o áudio para a esquerda numa cópia confirmou que o `checar` pega os dois.

## Aprendizados da Fase 2

- **Um plano, duas funções.** O mesmo `plano-de-cenas.md` traz a frase-gatilho (encaixe na timeline) e a descrição do motion (geração). O editor não mantém dois arquivos.
- **O motor do Shark virou o motor do kit sem mudança visual.** As 205 cenas aprovadas (corpo e leads) passam pela linguagem do plano e voltam idênticas; as 145 composições do corpo saem byte a byte iguais às originais; o render de teste saiu idêntico pixel a pixel.
- **Assets com licença restrita ficam fora do Git**: a Arial Bold das etiquetas da prévia vem do Windows de cada editor.
- **Testar com poucas cenas** (`render --so B05H,B05I`): cada cena leva cerca de meio minuto de render.

## Aprendizados das Fases 3 e 4

- **O ambiente Python fica fora do kit**, em `%LOCALAPPDATA%\STLFLIX_EDITOR\venv`: com placa NVIDIA ele tem ~2 GB de bibliotecas CUDA, que não podem ir para o OneDrive nem para o Git. O atalho `stlflix.cmd` na raiz chama esse Python.
- **Recomendar clonar fora do OneDrive** (`C:\STLFLIX_EDITOR`): os renders e as pastas de trabalho dos motions são pesados.
- **Saída redirecionada no Windows** (como o Claude Code lê) cai em cp1252 e quebra com ✓/✗: o `stlflix` força UTF-8.
- O FilmCraft não tem instalador por winget: o script só confere a versão e abre o site do ArtCraft Launcher.

## Aprendizados da Fase 5

- **O painel é gerado, não um servidor.** `stlflix painel` lê as pastas e grava uma página estática com os dados embutidos; para atualizar, roda de novo. Nada fica rodando e funciona sem internet.
- **Uma fonte só para as ferramentas**: o painel roda o próprio instalador em `-Verificar -Json`, então a lista do painel e a do instalador nunca divergem.
- O painel não conecta no FilmCraft: o que está na timeline (motions colocados, enquadramento) continua sendo visto com `status`, `motions` e `checar`.

## Ainda a portar do `_legado`

- B-roll 16:9 → 9:16 por keyframes (análise de rosto/assunto + keyframes).
- Peças 3D: análise, cortes e enquadramento que acompanha a peça.
- Bake da cor (LUT) a partir da correção do FilmCraft.
- Reconstrução do áudio perdido na importação de XML.
- Decupagem automática (cortes por energia, pausas, tropeços e crossfades) — maior, fica para depois do piloto.

## Pendências

- Conta ou organização do GitHub e se o repositório será privado.
- Nome e e-mail do Git nesta máquina, para os commits.
- Licenças de fontes e músicas que entram no repositório.
