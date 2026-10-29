---
name: gerar-motions
description: Renderiza os motions do plano de cenas no HyperFrames (modelo Shark-VSL) como .mov transparentes em 05-motions, testando primeiro com poucas cenas. Use quando o editor pedir para gerar, renderizar ou prever os motions, ou refazer cenas que mudaram no plano.
---

# Gerar os motions

1. Valide: `node 3-motions/motions.mjs validar --projeto <VSL> [--plano <seq>]`. Corrija erros com o editor antes de renderizar.
2. **Teste com 2 ou 3 cenas** (cada uma leva ~30 s):
   `node 3-motions/motions.mjs render --projeto <VSL> --so B05A,B05B`
   Mostre a prévia `<pasta da VSL>/motions-hf/<plano>/renders/previa-cenas.mp4` (motion sobre o quadro de referência) e espere o ok.
3. Para olhar e ajustar ao vivo: `node 3-motions/motions.mjs previa --projeto <VSL>` abre o Studio do HyperFrames.
4. Render completo só com o pedido do editor. Avise o tempo estimado (nº de cenas × ~30 s) e rode em segundo plano:
   `node 3-motions/motions.mjs render --projeto <VSL>`
5. **Pendentes** ("cria os motions pendentes", "refaz os que mudaram"): `render --pendentes` faz só as cenas que ainda não têm `.mov` ou cuja descrição mudou no plano depois do render. Antes, mostre a lista: `node 3-motions/motions.mjs estado --projeto <VSL>` (cada cena com `pronto`, `falta`, `mudou` ou `so-encaixe`). Mais de 3 cenas pendentes e o editor ainda não viu nenhuma? Teste primeiro com `--so`.
6. Os `.mov` (ProRes 4444, 1080×1920, 30 fps, com transparência) vão para `05-motions` com um `LEIAME.txt`. A versão anterior de uma cena refeita não é sobrescrita: vai sozinha para `05-motions/_motions anteriores (dd-mm HHhMM)`. O `05-motions/.registro-render.json` guarda a impressão de cada cena renderizada (é como o kit sabe o que "mudou"): não apague.
7. Ao terminar, lembre que o painel (atalho "Painel STLFLIX" ou `./stlflix.cmd painel`) mostra a **galeria** dos motions, com uma imagem de cada um e o que ainda falta.

## Cuidados

- A pasta `motions-hf/` é refeita a cada `gerar`/`render`: não edite à mão.
- O render guarda cada quadro em PNG no disco temporário; por isso vai em partes de 30 cenas (`--por-parte`). Falta de espaço em C: derruba o render.
- Mudanças no visual (motor em `3-motions/modelos/shark-vsl/`) valem para todo o time: só com pedido explícito, e teste com `--so` comparando com um render anterior.
- Peças que o plano não tem sintaxe (linha, barras, pessoas, 3D) entram por `json: {...}`; veja `5-guias/plano-de-cenas.md`.

Próximo passo: skill `encaixar-motions`.
