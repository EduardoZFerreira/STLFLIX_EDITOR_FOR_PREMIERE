# STLFLIX — design.md (vídeo YouTube, 16:9)

> Origem dos tokens: **[exato]** = lido do arquivo do logo; **[est.]** = estimado a olho dos prints,
> confirme com conta-gotas (eyedropper) antes de travar. Nada aqui foi inventado sem marcação.

## Formato
- Canvas: 1920×1080, 16:9, YouTube (vídeo longo, ~7 min)
- Base: vídeo bruto (Thales falando) como track 0. Overlays entram por cima; não cobrir o rosto nem a impressora quando ele a mostra/aponta.

## Marca
- Nome: STLFLIX — "A melhor assinatura de STL"
- Papel no vídeo: plataforma que o Thales usa para baixar modelos prontos (cena de menção, ~12 s). O restante do vídeo é do canal dele; a STLFLIX entra como identidade visual e assinatura discreta.
- Tom: direto, didático, acessível. Sem jargão técnico gratuito.

## Logo
- Arquivo: `assets/stlflix.svg` (302×80). Ícone de "S" em fita + wordmark.
- Gradiente do ícone [exato]: `#3947A1` → `#68ADF7`
- Wordmark [exato]: `#F6FAFE` (claro) → **só funciona sobre fundo escuro**. Para fundo claro é preciso uma variante escura do wordmark (não temos).
- Uso: cena da plataforma, assinatura no canto (opcional) e end card. Não animar o logo mais que um fade/scale simples.

## Cores
| Token | Valor | Origem | Uso |
|---|---|---|---|
| `--bg` | `#0D0E14` | [est.] | fundo de cards e cenas cheias (prints da plataforma são quase pretos) |
| `--bg-navy` | `#06092B` | declarado no site (theme-color) | alternativa de fundo mais "azulada" |
| `--surface` | `#15161E` | [est.] | cards, chips, molduras |
| `--text` | `#F6FAFE` | [exato] (wordmark) | texto principal |
| `--text-dim` | `#9A9CAB` | [est.] | legendas, subtítulos |
| `--accent` | `#5665F0` | [est.] | botões, números de ranking, destaques (azul/indigo dos prints) |
| `--logo-a` | `#3947A1` | [exato] | gradiente |
| `--logo-b` | `#68ADF7` | [exato] | gradiente |
| `--cta` | `#B8F23C` | [est.] | botão lima do banner da loja: usar **só** em CTA (inscreva-se / link na descrição) |
| `--grad-title` | `#22D3EE → #4F63E8 → #B14CF0` | [est.] | gradiente ciano→azul→violeta dos títulos do banner: usar em 1 palavra-chave por cena, no máximo |
| `--ok` / `--no` | `#3DDC84` / `#FF5C5C` | não vem da marca | checks e ✕ nas comparações antes/hoje. Escolha minha; troque se preferir |

Tags de produto vistas no menu (não aparecem na fala, usar só se quiser reforçar o ecossistema): STLAI violeta, STLSELLER verde, STLACADEMY âmbar.

## Tipografia
- Não consegui identificar as fontes com certeza. Os prints mostram sans geométrica/grotesca, títulos em peso 600–700, corpo regular.
- Proposta provisória (Google Fonts, carrega no Hyperframes): **Sora** (títulos) + **Inter** (corpo/legendas).
- Para fechar: abra a plataforma → F12 → selecione um título → aba *Computed* → `font-family`. Me mande o nome e eu troco.
- Escala para 1080p: título de capítulo 96–120 px · frase de impacto 72–88 px · corpo/chips 40–48 px · legenda de apoio 32 px (mínimo).

## Linguagem visual
- Fundo escuro, cantos arredondados grandes (raio 24–32 px), chips arredondados, sombras suaves.
- Números grandes em `--accent` (referência: ranking 1–4 do "Top 20 mais baixados"). Reaproveitar isso nos cards de capítulo: **1, 2, 3, 4, 5** enormes atrás do título.
- Texto em `--text`; no máximo 1 destaque de cor por frase.
- Ícones: traço fino, cantos arredondados (sugestão; a marca usa ícones simples e arredondados).

## Movimento
- Base: GSAP, easing `power3.out` na entrada, `power2.in` na saída. Entradas de 0,35–0,5 s.
- Texto: palavra a palavra sincronizada à fala, com leve deslocamento vertical (12–20 px) + fade.
- Transições entre capítulos: wipe horizontal em `--accent` (0,4 s). Dentro do capítulo: cortes secos ou fade curto.
- Ritmo: nada parado por mais de ~6 s sem mudança visual (é vídeo falado, então alternar overlay/rosto).
- Não usar: glitch exagerado, shake, zoom agressivo (a marca é limpa/tech, não caótica).

## Regras de segurança visual
- Preço de impressora: **não usar** o print da STLSTORE (impressoras a R$ 4–10 mil) na cena do "~R$ 1.400". Contradiz a fala.
- Print da plataforma (Top 20 / Mais vendidos) só na cena da STLFLIX. Modelos do print são conteúdo da própria STLFLIX.
- Numerais e unidades em tela devem bater exatamente com o que ele diz (R$ 1.400, 300–500 mm/s, 3 h → 12–14 h).
