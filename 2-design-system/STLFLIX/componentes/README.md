# Componentes STLFLIX

Sub-composições HyperFrames prontas, do projeto STLFLIX × Thales Brandão (github.com/sherecks/stlflix-design-system).

- Idênticas às do repositório: usam `assets/tokens.css` (relativo) e esperam a biblioteca ligada em `<projeto>/assets`. Copie para o `compositions/` do projeto; ver `../frame.md`.
- Para ver todas em sequência: abra `testes/stlflix-vitrine` com `npx hyperframes preview`.
- Os textos padrão são do vídeo do Thales. Troque pelas variáveis (quando existem) ou editando a cópia no projeto.

| arquivo | o que mostra | variáveis |
|---|---|---|
| `title-card.html` | abertura em tela cheia: título do vídeo ("5 coisas sobre impressão 3D…") com brilho de fundo | — |
| `lower-third.html` | nome e descrição de quem fala | `name`, `role` |
| `chapter-card.html` | número grande em accent + "COISA N DE 5" + título do capítulo | `num`, `kicker`, título |
| `impact-phrase.html` | frase em duas partes; a segunda em gradiente | `lead`, `punch` |
| `chips-sequence.html` | chips entrando em sequência, com rodapé opcional | `chips`, `footer`, `tone` |
| `before-after.html` | coluna "Antes" com ✕ e "Hoje" com ✓ | — |
| `symptoms.html` | sintomas com ✕ e uma frase-conclusão entre aspas | — |
| `objections.html` | objeções em lista e um veredito | `items`, `verdict` |
| `summary-checklist.html` | "Resumindo": checklist dos pontos do vídeo | — |
| `time-bars.html` | barras comparando tempos (1 cor 3 h × 4 cores 12–14 h) | — |
| `ratio-dots.html` | proporção em pontos (9/10) + frase | — |
| `speed-counter.html` | contador de mm/s com marcas 300/400/500 | — |
| `speed-slider.html` | régua "mais rápido ↔ mais devagar" por tipo de peça | — |
| `speed-risks.html` | curva + riscos (↓ acabamento, resistência, precisão) | — |
| `price-card.html` | preço caindo em contagem (R$ 50.000 → R$ 30.000 → máquina de entrada) | — |
| `parts-assembly.html` | itens com ✓ + frase final ("Expectativa certa.") | — |
| `purge-diagram.html` | diagrama: filamento, bico, blob de purga e pilha de descarte | — |
| `color-strip.html` | faixa de cores com frase curta ("Lindas. Mas demoram.") | — |
| `ready-models-flow.html` | fluxo Baixa → Abre no software → Imprime, com quem cria os modelos | — |
| `comment-cta.html` | chamada para comentar com seta para baixo | — |
| `end-cta.html` | encerramento: pílula Like + Inscreva-se, pergunta, logo, "link na descrição" | — |
