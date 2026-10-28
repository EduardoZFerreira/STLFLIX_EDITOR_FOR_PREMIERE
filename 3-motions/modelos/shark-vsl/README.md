# Modelo Shark-VSL

Lettering animado na **faixa acima da cabeça do apresentador**, numa VSL 9:16 (1080×1920). Aprovado nas VSLs do Shark (682_[BLACK26], leads e corpo, outubro de 2026).

- **Visual:** design system STLFLIX (Sora + Inter, gradiente verde→azul na palavra-chave), números de resultado em verde com brilho, frase de impacto circulada à mão nas cenas com título no topo, poeira de partículas opcional.
- **Peças:** kicker, título, frase (peso variável), número (com contagem), legenda, ícone, ícones, logo, CTA, chips. A sintaxe está em `5-guias/plano-de-cenas.md`.
- **Faixa:** `top` 130 px e `height` 430 px por padrão. Ajuste em `motions.faixa` no `config.json` se o apresentador estiver mais alto ou mais baixo no quadro.

## Como criar um modelo novo

1. Copie esta pasta para `3-motions/modelos/<nome-do-modelo>/`.
2. Mude o `motor.mjs`. Ele precisa exportar `construir(cenas, { pasta, faixa, campanha, so })`, que escreve `compositions/`, `index.html` e `cenas.json` na pasta e devolve `{ total, lista }`.
3. Num projeto, use `"motions": { "modelo": "<nome-do-modelo>" }` no `config.json`.
4. Teste com `render --so` em duas ou três cenas antes de liberar para o time.

O plano de cenas (frases-gatilho e peças) é o mesmo para todos os modelos. Um modelo novo pode reaproveitar as peças existentes com outro visual, ou ler peças novas pelo `json: {...}` até ganharem sintaxe própria.
