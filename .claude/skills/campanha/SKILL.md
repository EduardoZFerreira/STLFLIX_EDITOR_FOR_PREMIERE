---
name: campanha
description: Cria ou atualiza uma campanha visual dos motions (cores do degradê, barrinha, brilho, ícones e logo) a partir dos arquivos do design, confere e renderiza uma amostra para aprovação; também troca a campanha de uma VSL. Use quando o editor falar em campanha nova (Natal, Carnaval, Dia das Mães…), mandar ícones ou logo novos, ou quiser mudar as cores dos motions.
---

# Campanha visual dos motions

Cada campanha é uma pasta em `2-design-system/campanhas/<código>/` (ex.: `bf26`, `natal26`) com:

- `campanha.json`: nome, texto do logo e as **cores** (`degrade` dos títulos, da palavra-chave e do botão de CTA; `barra`; `brilho` embaixo dos ícones). Os números de resultado (`[verde]` no plano) ficam no verde → azul da marca; só mudam se a campanha tiver `resultado` (não sugira isso sem o editor pedir);
- os **ícones** em PNG transparente, 520 px de altura, nome sem espaço e sem acento (`pilha-moedas.png`);
- o **logo** `logo-kv.png`.

A marca STLFLIX (fontes, branco, o verde-limão de resultado e de CTA) não muda com a campanha. Sem `campanha.json`, o motor usa as cores da BF26.

## Criar uma campanha

1. Pergunte: o **nome** ("Natal 2026"), um **código** curto (`natal26`), a **pasta** com os arquivos do design (PNGs dos ícones e do logo; `./stlflix.cmd escolher-pasta` se ele não souber o caminho) e as **cores**. Cores: peça os hexadecimais ao design (3 ou 4 cores do degradê, do claro para o escuro, na ordem em que aparecem no key visual). Se ele não tiver, sugira a partir do logo e deixe claro que é sugestão.
2. Crie: `./stlflix.cmd campanha nova natal26 --nome "Natal 2026" --de "<pasta>" --cores "#..,#..,#..,#.." [--barra #..] [--brilho #..]`
   - recorta a borda transparente de cada imagem, padroniza os ícones em 520 px de altura e o logo em até 1680 px de largura;
   - arquivo com "logo" ou "kv" no nome vira o `logo-kv.png`; os outros viram ícones com o nome corrigido;
   - imagem **sem fundo transparente** não entra (peça o PNG certo ao design); ícone pequeno entra com aviso de que pode borrar.
3. Mostre ao editor o que entrou, os avisos e os nomes finais dos ícones.
4. **Amostra** (~45 s): `node 3-motions/motions.mjs amostra --campanha natal26` (opcional `--referencia <png do apresentador>`). Gera `2-design-system/campanhas/natal26/_amostra/previa.mp4` e um quadro de cada batida (`A01A-1.jpg`…): palavra-chave no degradê, barra e título do topo, número verde, ícones, logo e CTA. Mostre e espere o ok; ajuste as cores no `campanha.json` e gere de novo se ele pedir.
5. A campanha é parte do kit: para o time receber, ela precisa ir para o GitHub. Pergunte se pode subir (os arquivos `_amostra` ficam de fora).

## Atualizar ícones ou logo

`./stlflix.cmd campanha importar natal26 --de "<pasta>"` (substitui os de mesmo nome) → `campanha conferir natal26` → amostra se mudou algo visível. Cores: edite o `campanha.json`.

## Trocar a campanha de uma VSL

Mude `motions.campanha` no `config.json` da VSL. Todos os motions já criados passam a aparecer como **"mudou"** na galeria do painel: refaça com `render --pendentes` (teste antes com `--so` em 2 ou 3 cenas). Confira se os ícones usados no plano existem na campanha nova (`motions.mjs validar` aponta os que faltam e lista os que existem).

## Conferir

```
./stlflix.cmd campanha listar               campanhas do kit, ícones de cada uma
./stlflix.cmd campanha conferir <código>    cores válidas, logo, ícones transparentes em 520 px, nomes
```

O painel mostra, para a VSL escolhida, o catálogo de ícones da campanha dela (clicar copia `ícone: nome` para o plano).
