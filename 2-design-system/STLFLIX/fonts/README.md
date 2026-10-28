# Fontes STLFLIX

## Oficiais (desde 2026-10-14)

| Família | Uso | Arquivos | Licença |
| --- | --- | --- | --- |
| Sora | Títulos, números, frases de impacto (400, 700) | `sora-latin-{400,700}-normal.woff2` | OFL |
| Inter | Texto, chips, legendas (400, 600, 700) | `inter-latin-{400,600,700}-normal.woff2` | OFL |

Vieram do design system github.com/sherecks/stlflix-design-system. Os arquivos cobrem só o subconjunto latino, que inclui os acentos do português. Elas são declaradas em `../tokens.css` (o que as composições usam) e em `fonts.css`.

O próprio `design.md` marca Sora + Inter como proposta provisória, porque as fontes da plataforma não foram confirmadas. Para fechar: abra a plataforma → F12 → selecione um título → aba *Computed* → `font-family`.

## Versões anteriores (não usar em projetos novos)

`Montserrat/`, `Lexend/` e `SpaceGrotesk/` ficam aqui só para projetos antigos que ainda apontam para elas.

## Disponíveis no Drive da empresa (ainda não baixadas)

Pasta do Drive: https://drive.google.com/drive/folders/1-hZ5xM8EtEsh9OfFiXRe28HyRg6TXn5r

- **Google Fonts (OFL, uso livre):** Arimo, Bebas Neue, Bilbo Swash Caps, DM Mono, DM Sans, Homemade Apple, Inter, Italianno, Luxurious Script, Nunito, Open Sans, Oswald, Playfair Display, Plus Jakarta Sans, Poppins, Prompt, Space Grotesk.
- **Display de terror (licença comercial, confirmar antes de usar):** Bloodbeth (ATP), Chill Blood, Dirty Bleed Display (AT AIM), Shiver Grim (iFonts).

Para adicionar uma fonte, crie a pasta da família aqui, inclua o arquivo de licença e acrescente o `@font-face` no `fonts.css` (e no `tokens.css`, se for oficial).
