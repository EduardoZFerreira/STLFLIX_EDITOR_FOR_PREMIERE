# 3-motions · motions STLFLIX 9:16 (HyperFrames)

Transforma o `plano-de-cenas.md` do projeto em motions .mov transparentes (ProRes 4444, 1080×1920, 30 fps), já posicionados na faixa acima da cabeça do apresentador.

```
node 3-motions/motions.mjs validar --projeto projetos/<VSL> [--plano corpo]
node 3-motions/motions.mjs gerar   --projeto projetos/<VSL> [--plano corpo]     cria/atualiza a pasta de trabalho
node 3-motions/motions.mjs previa  --projeto projetos/<VSL> [--plano corpo]     abre o Studio do HyperFrames
node 3-motions/motions.mjs render  --projeto projetos/<VSL> [--plano corpo] [--so B05H,B05I] [--por-parte 30]
node 3-motions/motions.mjs migrar  --build <build.mjs antigo> --gatilhos <plano com frases> --saida <plano.md>
```

- `render` grava um .mov por cena em `<projeto>/05-motions` (com `LEIAME.txt`) e a prévia sobre o quadro de referência em `<projeto>/motions-hf/<plano>/renders/previa-cenas.mp4`.
- Use `--so` para testar poucas cenas antes do render completo: cada cena leva cerca de meio minuto.
- O render é feito em partes (30 cenas por vez), porque o HyperFrames guarda cada quadro em PNG e o reel inteiro não cabe no disco temporário.

A linguagem do plano está em `5-guias/plano-de-cenas.md`.

## Como funciona

```
plano-de-cenas.md ──dsl.mjs──▶ cenas ──modelos/<modelo>/motor.mjs──▶ compositions/*.html + index.html ──hyperframes render──▶ .mov
```

- **`motor/dsl.mjs`**: lê o plano (e escreve, na migração). Testado em ida e volta com as 205 cenas aprovadas das VSLs do Shark.
- **`modelos/<modelo>/motor.mjs`**: o visual. Hoje existe o **`shark-vsl`**, o motor das VSLs do Shark (HTML, CSS, animações GSAP), extraído **sem mudanças**. Gera composições idênticas byte a byte às originais, e o render sai idêntico pixel a pixel.
- **Pasta de trabalho** `<projeto>/motions-hf/<plano>/`: projeto HyperFrames criado sozinho, com junções para `2-design-system` (assets STLFLIX, GSAP, efeitos e o kit da campanha). Não edite à mão: é refeita a cada `gerar` ou `render`.

## Configuração (`config.json` do projeto)

```json
"motions": {
  "modelo": "shark-vsl",                                modelo visual (pasta em 3-motions/modelos/)
  "campanha": "bf26",                                   pasta em 2-design-system/campanhas/ (ícones e logo)
  "faixa": { "top": 130, "height": 430 },               onde os motions ficam no quadro (acima da cabeça)
  "referencia": "04-plano-de-cenas/referencia.png",     quadro do apresentador, só para a prévia
  "hyperframes": "0.8.176"                              versão fixa do HyperFrames
}
```

## Requisitos

Node.js 20+, ffmpeg no PATH e internet na primeira vez (o `npx` baixa o HyperFrames na versão fixa). A prévia usa a Arial Bold do Windows para as etiquetas.

## Novos modelos

Cada modelo visual é uma pasta em `modelos/`. Como criar um: `modelos/shark-vsl/README.md`.

## Novos tipos de peça ou efeitos

O motor é o mesmo para todas as VSLs. Mudanças visuais nele valem para todo o time: faça com cuidado, teste com `render --so` em duas ou três cenas e compare com um render anterior. Peças que o motor já desenha, mas que o plano ainda não tem sintaxe (linha, barras, pessoas, conta, pilha, pontos, 3D), entram por `json: {...}`.
