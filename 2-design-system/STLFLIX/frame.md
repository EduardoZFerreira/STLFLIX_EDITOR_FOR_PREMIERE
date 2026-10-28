---
version: 2
name: STLFLIX — Frame (camada de vídeo)
description: >
  Design system oficial da STLFLIX para motions e overlays HyperFrames, adotado em 2026-10-14 a partir de
  github.com/sherecks/stlflix-design-system (projeto STLFLIX × Thales Brandão). Fundo escuro, painéis
  arredondados, barra de destaque azul-índigo, Sora nos títulos e Inter no texto, gradiente ciano→azul→violeta
  em no máximo uma palavra-chave por cena, verde-lima só em CTA.
  Detalhe e origem de cada token: design.md. Valores prontos para uso: tokens.css.
unit: o quadro — 1920×1080 (16:9) como base; escalar proporcionalmente para 9:16 e 1:1
principle: fundo escuro · 1 destaque de cor por frase · números batem com a fala · nada parado > ~6 s

colors:
  bg: "#0D0E14"          # cenas cheias e cards
  bg-navy: "#06092B"     # alternativa azulada (theme-color do site)
  surface: "#15161E"     # painéis, chips, molduras (painel de overlay a 92% de opacidade)
  text: "#F6FAFE"        # texto principal (cor do wordmark)
  text-dim: "#9A9CAB"    # legendas, eyebrows, apoio
  accent: "#5665F0"      # barra de destaque, números de capítulo, botões
  logo-a: "#3947A1"      # gradiente do símbolo
  logo-b: "#68ADF7"
  cta: "#B8F23C"         # SÓ em CTA (inscreva-se, link na descrição)
  ok: "#3DDC84"          # checks em comparações
  no: "#FF5C5C"          # ✕ em comparações
  grad-title: "linear-gradient(90deg, #22D3EE, #4F63E8, #B14CF0)"   # 1 palavra-chave por cena, no máximo

typography:
  title:   { fontFamily: "Sora", weight: 700 }      # títulos, números, frases de impacto
  body:    { fontFamily: "Inter", weight: "400/600/700" }
  scale-1080p:
    chapter: 104px      # título de capítulo (96–120)
    impact: 80px        # frase de impacto (72–88)
    body: 44px          # corpo e chips (40–48)
    caption: 32px       # legenda de apoio (mínimo)

shape:
  radius: 28px          # painéis e cards (24–32)
  radius-chip: 999px
  shadow: "0 24px 60px rgba(0,0,0,0.45)"

components:
  anchor:      "lettering ancorado embaixo à esquerda (left 120, bottom 120, máx. ~44% da altura): barra accent de 10px + painel surface 92%. Sem fill de tela e sem scrim."
  panel:       "surface rgba(21,22,30,.92), radius 28, padding 30×46, shadow"
  chip:        "pílula surface, Inter 600 44px, padding 20×36"
  mark:        "círculo 44px com ✓/✕ (ok/no) ou número, Sora 700"
  grad-word:   "palavra-chave em grad-title (background-clip: text)"
  chapter-num: "número grande em accent atrás/ao lado do título (1–5)"
  full-scene:  "só abertura e fecho: fill bg num filho full-bleed (.hf-fill), nunca na raiz (mantém o alfa)"
  logo:        "stlflix.svg — wordmark claro, só sobre fundo escuro; no máximo fade/scale simples"

motion:
  engine: GSAP
  in:  "power3.out, 0.35–0.5 s"
  out: "power2.in"
  text: "palavra a palavra, sincronizado à fala, deslocamento vertical 12–20 px + fade"
  chapter-transition: "wipe horizontal em accent, 0.4 s"
  avoid: "glitch exagerado, shake, zoom agressivo"
---

## Como usar num projeto

Ligue a biblioteca ao projeto por junção (nada é copiado):

```powershell
New-Item -ItemType Junction -Path "<projeto>\assets" -Target "<workspace>\assets\STLFLIX"
```

Nas composições, com caminho **relativo** (igual ao repositório original; `/assets/...` quebra no Studio):

```html
<link rel="stylesheet" href="assets/tokens.css" />
<img src="assets/stlflix.svg" alt="STLFLIX" />
```

Componentes prontos em `componentes/` (catálogo em `componentes/README.md`). Copie para o `compositions/` do projeto (pasta real, não junção) os que for usar e ajuste as variáveis. Os templates são editados por projeto, ao contrário de fontes e logos, que sempre vêm da biblioteca.

## Regras

- Overlays sobre fala: sem fill e sem scrim. O rosto e a impressora ficam livres; o lettering fica na faixa inferior esquerda.
- No máximo 1 destaque de cor por frase. O gradiente vai em 1 palavra-chave por cena. O verde-lima é só para CTA.
- Números e unidades na tela batem exatamente com a fala.
- Entregáveis: `.mov` transparente (ProRes 4444), um por cena, para o editor.

## Variante 9:16 (reels), aprovada em 2026-10-14

Ainda não aplicada aos componentes. É o padrão para o próximo projeto vertical. Referência funcionando: `testes/stlflix-reels/compositions/chapter-card-9x16.html`.

- **Quadro:** 1080×1920. Conteúdo **centralizado** (pilha vertical, `text-align: center`).
- **Sem painel de fundo:** nada de `.hf-panel` nem caixa grande atrás do conteúdo, nem translúcida. Os elementos vão direto sobre o vídeo.
- **Legibilidade:** `text-shadow: 0 2px 18px rgba(0,0,0,.55), 0 1px 3px rgba(0,0,0,.5)` no texto; `--text-dim` sobe para `--text` a 85%.
- **Barra de destaque:** horizontal (140×10 px) acima do bloco, abrindo do centro (`scaleX`), em vez da barra vertical lateral.
- **Escala:** número 200 px, kicker 32 px (Inter 600, tracking .2em), título 84 px (Sora 700).
- **Movimento:** mesmos easings do sistema; o bloco sobe (`y: 44 → 0`) em vez de deslizar da esquerda; sai subindo (`y: -30`).
- **Em aberto:** o número em `--accent` (#5665F0) perde contraste sobre roupa ou fundo escuro. Opções: sombra mais forte, `--logo-b` (#68ADF7) só no número, ou posicionar o bloco sobre área clara.
