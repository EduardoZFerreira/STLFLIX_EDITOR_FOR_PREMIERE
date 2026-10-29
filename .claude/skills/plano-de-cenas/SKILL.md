---
name: plano-de-cenas
description: Ajuda o editor a escrever e validar o plano-de-cenas.md (motions por bloco, frase-gatilho e descrição das peças no modelo Shark-VSL), incluindo fazer um rascunho de um bloco ou da VSL inteira a partir da transcrição e da copy. Use quando o editor estiver montando o plano de cenas, pedir rascunho ou sugestões de motions para um trecho, ou quiser conferir se o plano está no formato certo.
---

# Plano de cenas

O plano é **do editor**: ele decide o que entra. O Claude pode fazer um **rascunho**, mas o rascunho fica num arquivo separado e só vai para o plano o que o editor aprovar. Leia antes `5-guias/plano-de-cenas.md` (linguagem completa e boas práticas) e o exemplo em `04-plano-de-cenas/EXEMPLO-plano-de-cenas.md`.

## Formato em uma olhada

```
## Bloco 05 · Luan

- **B05H** · Quase R$ 5 mil — "Luan achou um produto com potencial de"
  duração: 7
  > 0.3 | kicker: O PRODUTO QUE O LUAN ACHOU | número: R$ 5 mil [verde, conta] | legenda: quase isso de lucro, com 1 impressora
```

- O **id** (`B05H`) é também o nome do `.mov`. Bloco + letra, sem repetir.
- A **frase-gatilho** entre aspas é copiada da transcrição: é onde o motion entra na timeline. Use 4 a 8 palavras distintas da fala; evite frases que se repetem no vídeo.
- As linhas de baixo descrevem o motion (modelo Shark-VSL: faixa de lettering acima da cabeça). Cada linha `>` é uma **batida**: as peças separadas por `|` aparecem juntas a partir daquele segundo, e a próxima linha `>` **substitui** a anterior. Não quebre uma batida em várias linhas `>`.

## Rascunho ("Faz um rascunho do plano do bloco 5", "…do plano de cenas da VSL-X")

1. **O que ler** (da pasta da VSL, `./stlflix.cmd vsls` mostra onde fica):
   - a transcrição da sequência, `06-transcricoes/<seq>.md`, no trecho do bloco pedido (é o que foi **falado**, com o tempo de cada frase);
   - o roteiro, `01-roteiro/teleprompter.txt`, no mesmo bloco (a intenção da copy: o que é promessa, número, prova, CTA);
   - o plano atual, se existir (para não repetir códigos nem ideias, e para seguir o estilo que o editor já usa);
   - o exemplo `04-plano-de-cenas/EXEMPLO-plano-de-cenas.md` e o guia `5-guias/plano-de-cenas.md`;
   - os ícones que existem na campanha da VSL: `2-design-system/campanhas/<campanha>/*.png` (o nome do arquivo sem `.png`). Não invente ícone.
   Se a transcrição não existe, ofereça transcrever antes (skill `transcrever`): sem ela não há frase-gatilho confiável.
2. **Como escolher as cenas** (padrão aprovado nas VSLs do Shark: ~5 motions por minuto de fala, 1 a cada 12 s em média):
   - motion onde a fala tem **número, nome, promessa, prova, lista, virada ou CTA**; frase de transição fica sem motion;
   - uma ideia por cena; 2 a 4 batidas, de 2,7 a 3,4 s entre elas; até 14 letras por linha de título, no máximo 2 linhas;
   - **verde só para resultado** (venda, lucro) e para o CTA; números que são o centro da cena com `conta`;
   - frase-gatilho **copiada letra por letra da transcrição**, no começo do que a tela mostra, 4 a 8 palavras que não se repetem no vídeo;
   - códigos `B<bloco><letra>` continuando depois das letras que o plano já usa naquele bloco.
3. **Onde gravar**: `04-plano-de-cenas/rascunho-<seq>.md` (crie, ou acrescente o bloco). **Nunca** escreva no `plano-de-cenas.md` nessa etapa. Primeira linha do arquivo: `# Rascunho do plano de cenas — <VSL> · <seq> (não aprovado)`.
4. **Conferir antes de mostrar** (corrija o que der erro):
   ```
   node 3-motions/motions.mjs validar --projeto <VSL> --arquivo 04-plano-de-cenas/rascunho-<seq>.md
   ./stlflix.cmd --projeto <VSL> gatilhos <seq> --plano 04-plano-de-cenas/rascunho-<seq>.md
   ```
   O `gatilhos` mostra o tempo em que cada frase é falada; `✗` é frase que não aparece na transcrição: copie de novo.
5. **Mostrar ao editor** como uma lista curta, uma linha por cena: código, tempo na timeline, frase-gatilho e o que aparece na tela (em palavras, não na linguagem do plano). Pergunte o que cortar, trocar ou juntar. Se ele quiser ver, renderize 2 ou 3 cenas do rascunho:
   `node 3-motions/motions.mjs render --projeto <VSL> --arquivo 04-plano-de-cenas/rascunho-<seq>.md --so B05A,B05B`
6. **Passar para o plano** só quando ele aprovar ("pode passar", "aprovo o bloco 5"): copie as cenas aprovadas para o `plano-de-cenas.md` (na ordem dos blocos, sem mexer no resto do arquivo), mostre o que entrou e tire essas cenas do rascunho. Depois, `validar` e `gatilhos` no plano.

## Sugestões avulsas

Se o editor pedir ideia para um trecho específico, proponha no chat para ele aprovar ou editar; só grave quando ele pedir, editando só as cenas combinadas.

## Conferir o plano

```
./stlflix.cmd --projeto <VSL> plano                        formato, ids e .mov que faltam
node 3-motions/motions.mjs validar --projeto <VSL>          linguagem das peças e ícones que não existem
./stlflix.cmd --projeto <VSL> gatilhos <seq>                se cada frase-gatilho aparece na transcrição (sem FilmCraft)
./stlflix.cmd --projeto <VSL> motions <seq>                 o encaixe completo, com os .mov (nota ≥ 0,75 encaixa)
```

Frase não encontrada: copie de novo da transcrição, com as palavras como foram ditas.
