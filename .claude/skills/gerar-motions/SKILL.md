---
name: gerar-motions
description: Renderiza os motions do plano de cenas no HyperFrames (modelo Shark-VSL) como .mov transparentes em 05-motions, testando primeiro com poucas cenas. Use quando o editor pedir para gerar, renderizar ou prever os motions, ou refazer cenas que mudaram no plano.
---

# Gerar os motions

1. Valide: `node 3-motions/motions.mjs validar --projeto projetos/<VSL> [--plano <seq>]`. Corrija erros com o editor antes de renderizar.
2. **Teste com 2 ou 3 cenas** (cada uma leva ~30 s):
   `node 3-motions/motions.mjs render --projeto projetos/<VSL> --so B05A,B05B`
   Mostre a prévia `projetos/<VSL>/motions-hf/<plano>/renders/previa-cenas.mp4` (motion sobre o quadro de referência) e espere o ok.
3. Para olhar e ajustar ao vivo: `node 3-motions/motions.mjs previa --projeto projetos/<VSL>` abre o Studio do HyperFrames.
4. Render completo só com o pedido do editor. Avise o tempo estimado (nº de cenas × ~30 s) e rode em segundo plano:
   `node 3-motions/motions.mjs render --projeto projetos/<VSL>`
   Para refazer só as cenas que mudaram, use `--so` com os ids.
5. Os `.mov` (ProRes 4444, 1080×1920, 30 fps, com transparência) vão para `05-motions` com um `LEIAME.txt`. Antes de regravar, confira se não há `.mov` aprovados que o editor quer guardar; se houver, mova para `05-motions/_anteriores (data)`.

## Cuidados

- A pasta `motions-hf/` é refeita a cada `gerar`/`render`: não edite à mão.
- O render guarda cada quadro em PNG no disco temporário; por isso vai em partes de 30 cenas (`--por-parte`). Falta de espaço em C: derruba o render.
- Mudanças no visual (motor em `3-motions/modelos/shark-vsl/`) valem para todo o time: só com pedido explícito, e teste com `--so` comparando com um render anterior.
- Peças que o plano não tem sintaxe (linha, barras, pessoas, 3D) entram por `json: {...}`; veja `5-guias/plano-de-cenas.md`.

Próximo passo: skill `encaixar-motions`.
