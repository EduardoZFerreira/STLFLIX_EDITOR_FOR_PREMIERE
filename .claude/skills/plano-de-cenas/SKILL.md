---
name: plano-de-cenas
description: Ajuda o editor a escrever e validar o plano-de-cenas.md (motions por bloco, frase-gatilho e descrição das peças no modelo Shark-VSL). Use quando o editor estiver montando o plano de cenas, pedir sugestões de motions para um trecho, ou quiser conferir se o plano está no formato certo.
---

# Plano de cenas

O plano é **do editor**: ele escreve a partir da transcrição (`06-transcricoes/<seq>.md`) e da copy. Leia antes `5-guias/plano-de-cenas.md` (linguagem completa) e o exemplo em `04-plano-de-cenas/EXEMPLO-plano-de-cenas.md`.

## Formato em uma olhada

```
## Bloco 05 · Luan

- **B05H** · Quase R$ 5 mil — "Luan achou um produto com potencial de"
  duração: 7
  > 0.3 | kicker: O PRODUTO QUE O LUAN ACHOU | número: R$ 5 mil [verde, conta] | legenda: quase isso de lucro, com 1 impressora
```

- O **id** (`B05H`) é também o nome do `.mov`. Bloco + letra, sem repetir.
- A **frase-gatilho** entre aspas é copiada da transcrição: é onde o motion entra na timeline. Use 4 a 10 palavras distintas da fala; evite frases que se repetem no vídeo.
- As linhas de baixo descrevem o motion (modelo Shark-VSL: faixa de lettering acima da cabeça). Cada linha `>` é uma **batida**: as peças separadas por `|` aparecem juntas a partir daquele segundo, e a próxima linha `>` **substitui** a anterior. Não quebre uma batida em várias linhas `>`.

## Como ajudar

- Se o editor pedir sugestões, proponha cenas para os trechos que ele indicar (números, nomes, promessas, CTA), seguindo as boas práticas do guia. Mostre como texto para ele aprovar ou editar; só grave no arquivo quando ele pedir.
- Ao gravar, edite só as cenas combinadas e preserve o resto do arquivo.

## Conferir

```
./stlflix.cmd --projeto projetos/<VSL> plano                       formato, ids e .mov que faltam
node 3-motions/motions.mjs validar --projeto projetos/<VSL>         linguagem das peças
./stlflix.cmd --projeto projetos/<VSL> motions <seq>                se cada frase-gatilho é encontrada na sequência
```

O último mostra a nota de cada frase (≥ 0,75 encaixa). Frase não encontrada: copie de novo da transcrição, com as palavras como foram ditas.
