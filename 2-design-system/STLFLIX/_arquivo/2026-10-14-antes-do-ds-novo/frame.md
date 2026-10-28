---
version: alpha
name: STLFLIX — Frame (video / frame layer)
description: >
  Spec de marca da STLFLIX para motions e letterings HyperFrames, derivado de
  `identidade_stlflix.md` (guia "Primary Brand", banners do 4º aniversário e fotos de estúdio).
  Azul-noite com spot de luz azul, títulos sans geométrica black em caixa-alta com palavra-chave
  em azul-céu, texto em sans geométrica leve, pílula "ao vivo" com borda em gradiente. Sem roxo.
  Copie este arquivo para a raiz de cada projeto como `frame.md`.
unit: the frame — 1920×1080 primary; 1080×1920 (9:16) and 1080×1080 (1:1) documented
principle: atoms are sacred · composition is free · numbers come from the script

colors:
  # — Primary Brand (oficial) —
  b1-lavender: "#7E8FF2"
  b2-blue: "#5166E6"
  b3-blue-mid: "#3947A1"
  b4-navy: "#20295C"
  b5-navy-deep: "#10142E"
  # — apoio observado nos banners —
  sky: "#3EA6FF"
  sky-deep: "#1E7BFF"
  night: "#060918"
  night-alt: "#0A0F2A"
  white: "#FFFFFF"
  callout-blue: "#1E6FD0"   # aproximado ("-ish" no guia)
  # — tons medidos nas fotos de estúdio (fundos e degradês) —
  studio-light: "#3D80F5"
  studio-light-peak: "#5B95FF"
  studio-royal: "#11327D"
  studio-royal-deep: "#0B276C"
  studio-transition: "#04103A"
  studio-vignette: "#010525"
  studio-vignette-deep: "#010312"
  studio-floor-reflection: "#004A9D"

typography:
  # Fontes oficiais PENDENTES: Montserrat e Lexend são aproximações aprovadas.
  # Arquivos: assets/STLFLIX/fonts/ (fonts.css declara as duas, pesos 100–900).
  # — texto (Lexend 300–500) —
  body:    { fontFamily: "Lexend", cqw: 1.3, weight: 300, lineHeight: 1.5 }
  lead:    { fontFamily: "Lexend", cqw: 1.8, weight: 400, lineHeight: 1.4 }
  emphasis:{ fontFamily: "Lexend", cqw: 1.8, weight: 500, lineHeight: 1.4, color: "{colors.sky}" }
  label:   { fontFamily: "Lexend", cqw: 0.8, weight: 500, tracking: "0.12em", upper: true }
  # — títulos (Montserrat 800/900, caixa-alta) —
  h3:      { fontFamily: "Montserrat", cqw: 2.8, weight: 800, lineHeight: 1.1, upper: true }
  h2:      { fontFamily: "Montserrat", cqw: 4.5, weight: 900, lineHeight: 1.0, tracking: "-0.01em", upper: true }
  h1:      { fontFamily: "Montserrat", cqw: 7.5, weight: 900, lineHeight: 0.95, tracking: "-0.02em", upper: true }
  display: { fontFamily: "Montserrat", cqw: 11.0, weight: 900, lineHeight: 0.9, tracking: "-0.02em", upper: true }

spacing:
  pad-x: "5.5cqw"
  pad-y: "5.5cqw"
  gap-lg: "3.5cqw"
  gap-md: "2cqw"
  gap-sm: "1cqw"
  grid-cell: "56px"   # na base 1920 de largura; escala junto com o quadro

components:
  background:
    base: "{colors.night} → {colors.night-alt}"
    spot: "brilho radial {colors.studio-light} (pico {colors.studio-light-peak}) no canto superior esquerdo, caindo para {colors.studio-royal} → {colors.studio-transition} → {colors.studio-vignette}"
    grid: "linhas 1px {colors.b1-lavender} a ~16% de opacidade, células de {spacing.grid-cell}, esmaecendo para baixo"
    description: "Só em quadros cheios. Em overlays .mov o fundo é TRANSPARENTE e este tratamento não entra."
  title:
    typography: "{typography.h1} / {typography.display}"
    color: "{colors.white}; palavra-chave em {colors.sky}"
    description: "Caixa-alta pesada. Uma palavra/expressão-chave por título em azul-céu."
  eyebrow:
    typography: "{typography.label}"
    color: "{colors.b1-lavender}"
  live-pill:
    backgroundColor: "{colors.b5-navy-deep}"
    border: "1.5px em gradiente {colors.white} → {colors.b1-lavender} → {colors.b2-blue}"
    glow: "brilho externo {colors.b1-lavender}"
    content: "bolinha branca brilhante · TEXTO | TEXTO (separador vertical fino)"
    typography: "{typography.label}"
    shape: "pílula (radius 999px)"
    description: "Estados ativos e números-chave (ex.: ● AO VIVO | 100% GRATUITO)."
  callout-box:
    backgroundColor: "{colors.callout-blue}"
    radius: "0.8cqw"
    color: "{colors.white}; trecho em negrito escuro ({colors.b5-navy-deep})"
  button:
    background: "linear-gradient({colors.b2-blue} → {colors.sky-deep})"
    shape: "pílula"
    shadow: "sombra azul ({colors.sky-deep} ~40%)"
    color: "{colors.white}"
  logo:
    symbol: "assets/STLFLIX/logos/png/logo_STL.png (S em gradiente azul, fundo transparente, 1080×1080)"
    full-on-dark: "assets/STLFLIX/logos/png/logo-stlflix-branco.png (padrão: S em gradiente + STLFLIX branco, 725×192, transparente)"
    full-on-light: "assets/STLFLIX/logos/png/logo-stlflix-preto.png (original: S em gradiente + STLFLIX preto, 725×192, transparente)"
    max-width: "~725px no quadro 1920 (a resolução é 725px; maior que isso borra)"
    description: "Nunca redesenhar, distorcer ou recolorir o símbolo. Em fundo escuro/azul use sempre a versão branca."
---

## Overview

STLFLIX é uma plataforma de arquivos para impressão 3D, com a mensagem "como viver de impressão 3D". A marca é **azul e noturna**: um palco escuro com spot de luz azul, como produtos impressos fotografados em estúdio. Os títulos têm energia de evento (caixa-alta pesada, palavra-chave acesa em azul-céu). O texto de apoio é leve e arejado.

## The Frame

- **Overlay (padrão deste workspace):** fundo transparente, export `.mov` ProRes 4444. Só tipografia, pílulas, logo e objetos entram. Nada de spot ou grid.
- **Quadro cheio:** usa o tratamento `background` completo: azul-noite, spot no canto superior esquerdo, grid lavanda esmaecendo para baixo.
- 3D / produto: objeto sobre piso escuro reflexivo (`studio-floor-reflection`) com luz `studio-light`.

## Colors

- A família azul é a marca inteira. **Nunca roxo** e nunca as cores semânticas do painel.
- `b1–b5` é a escada oficial: lavanda para detalhe e eyebrow, `b2` para ação, `b4`/`b5` para superfícies.
- `sky` / `sky-deep` são o destaque: palavra-chave, datas, frases de chamada ("imprima e venda!").
- `white` é a cor dos títulos.
- Os tons `studio-*` servem só para fundos, degradês e iluminação 3D.

Cores do painel (`#3EDB9B`, `#FFB84D`, `#FF5C7A`, `#4F8BFF`, `#35C8F2`, `#B08CFF`) são de UI interna e **não entram nos vídeos**.

## Typography

- Títulos: Montserrat 800/900, sempre caixa-alta, tracking levemente negativo.
- Texto: Lexend 300–500. O destaque dentro do texto sobe o peso para 500 e fica em `sky`.
- Arquivos locais: `assets/STLFLIX/fonts/` (Montserrat e Lexend variáveis). Copie a pasta para o projeto e inclua `fonts/fonts.css`. Nunca carregue do Google Fonts online.
- Fontes oficiais ainda pendentes. Quando chegarem, troque `fontFamily` aqui e o `@font-face` no `fonts.css`.
- Para kinetic type com SplitText, divida o texto só depois de `document.fonts.ready`.

## Logo

- Símbolo: `logos/png/logo_STL.png` (1080×1080).
- Logotipo completo (símbolo + "STL" regular + "FLIX" bold):
  - `logos/png/logo-stlflix-branco.png`: **padrão nos vídeos** (fundo escuro). Derivado do preto: só o texto foi pintado de branco puro, o símbolo é o original.
  - `logos/png/logo-stlflix-preto.png`: original do cliente, para fundo claro.
- Os dois PNG têm 725×192. Use no máximo ~725 px de largura; para logo grande em tela cheia, peça o SVG.
- `logos/png/Bambu Lab.png` é de parceiro, sem transparência. Não é marca STLFLIX.

## Do's & Don'ts

- ✅ Uma palavra-chave azul-céu por título.
- ✅ Pílula "ao vivo" para status e números-chave.
- ✅ Brilho e glow azuis, gradientes `b2 → sky-deep`.
- ❌ Roxo, magenta ou qualquer cor fora da família azul (exceto branco).
- ❌ Títulos em caixa-baixa ou peso leve.
- ❌ Recolorir ou distorcer o símbolo.

## Approved Entities

TODO: produtos, planos, slogans e números oficiais. Já vistos nos banners: "O MAIOR ANIVERSÁRIO" (4º aniversário), "imprima e venda!", "como viver de impressão 3D", "AO VIVO | 100% GRATUITO".

## Known Gaps

- Fontes oficiais (Montserrat e Lexend são aproximações).
- Logotipo completo em SVG ou PNG de alta resolução (o atual tem 725 px de largura).
- `callout-blue` é aproximado.
