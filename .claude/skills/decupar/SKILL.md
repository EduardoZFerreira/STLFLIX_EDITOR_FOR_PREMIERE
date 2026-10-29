---
name: decupar
description: Decupagem com o Claude - transcreve os takes brutos da câmera, cruza com a copy para escolher o que entra (melhor versão de cada frase, sem tropeços), mostra a decupagem para o editor aprovar e monta a sequência no FilmCraft no estilo do time. Use quando o editor pedir para transcrever os brutos, decupar, montar o corpo ou um lead a partir dos takes, ou refazer a decupagem de um trecho.
---

# Decupar com o Claude

O editor aprova a decupagem e revisa a timeline; o Claude faz o trabalho braçal. Nada é montado sem a aprovação dele.

## 1. Transcrever os brutos

- Os takes da câmera começam com `takes.prefixo` do config (ex.: `C23`). O jeito mais simples: o editor importa os brutos no projeto do FilmCraft e abre pelo kit (`abrir`).
- `./stlflix.cmd --projeto <VSL> transcrever-brutos` (rode em segundo plano; ~1 min por 10 min de bruto com GPU). Sem o FilmCraft aberto ele procura em `02-brutos`; ou passe `--pasta "<pasta dos brutos>"`. Só alguns takes: `--so C2347,C2348`. Takes já transcritos são pulados.
- Resultado: `06-transcricoes/brutos.md` (todos os takes, frase a frase, com o tempo no bruto, pausas longas e `⚠ esticada` onde o Whisper fundiu uma repetição) e `06-transcricoes/brutos/<take>.json|.wav`.

## 2. Escrever a decupagem

Leia `brutos.md` e o roteiro `01-roteiro/teleprompter.txt` (blocos `--- BLOCO 5 · Título ---`). Para cada bloco, na ordem do roteiro:

- ache cada frase da copy nos takes; quando foi gravada mais de uma vez, fique com a **última repetição limpa** (a que vai até o fim sem tropeço), a mais perto da copy;
- **descarte** tropeços, frases cortadas no meio, conversa de set, contagem e "deixa eu fazer de novo"; uma boa variação que não foi usada vira **alternativa** (fica marcada no bruto para o editor trocar se quiser);
- ad-lib que funciona (fala natural fora da copy) pode entrar: anote no comentário;
- onde a fala mudou o sentido da copy (número, nome, preço, promessa), escreva `conferir:`; onde cabe uma imagem de apoio, `tela:`;
- `⚠ esticada` no `brutos.md` costuma ser repetição escondida: prefira outra versão daquela frase ou corte antes;
- os tempos marcam o trecho com folga, nas pausas antes e depois da fala (o kit acha o ponto exato pela energia do áudio). Não precisa cortar pausas internas: o kit corta as de 0,3 s ou mais.

Grave em `06-transcricoes/decupagem-<seq>.md` (`<seq>` = chave do config, ex.: `corpo`). Formato (a ordem dos `usa` é a ordem na timeline):

```
# Decupagem — <VSL> · corpo

## Bloco 05 · Luan

- C2347 00:11.3-00:23.0 · usa · Expositor + lojas de lembrancinhas
- C2347 00:25.0-00:35.9 · usa · Petare (parte 1) — falou "participou do reality" (copy: "do reality show")
  conferir: ouvir se ele disse "margem"
  tela: Cotrim entregando os ímãs
- C2347 00:35.9-00:41.2 · descarta · "Em que a gente visita…" (2 tentativas)
- C2347 00:06.1-00:11.3 · alternativa · versão completa da frase
```

Tipos: `usa`, `alternativa`, `descarta`, `nota` (conversa ou recado que vale anotar no bruto). Texto depois de ` — ` vira comentário do marcador.

## 3. Mostrar e aprovar

1. `./stlflix.cmd --projeto <VSL> decupar <seq>` mostra os cortes calculados por bloco, os avisos e o total (minutos de fala, nº de clipes e de crossfades). Corrija os erros (trecho repetido, take não transcrito, trecho sem fala).
2. Mostre ao editor um resumo por bloco: que take e trecho entra, o que foi descartado e por quê, e os pontos de "conferir". Ajuste o arquivo com o que ele pedir.
3. Antes de montar, confirme: a sequência `sequencias.<seq>` do config existe no projeto (pode estar vazia ou com os brutos jogados nela). O kit **duplica a sequência** (backup), tira dela os clipes dos takes usados e monta a decupagem a partir do fim do que sobrar na V1.

## 4. Montar

Com o "pode montar" do editor: `./stlflix.cmd --projeto <VSL> decupar <seq> --aplicar`. O que ele faz:

- clipes na V1 + A1, no estilo de `5-guias/estilo-de-edicao.md`: cabeça 2 quadros antes da fala, cauda 5,5 depois (pela energia), pausas de 0,3 s ou mais cortadas, crossfade Constant Power de 3 quadros no meio da frase e 10 em fim de frase;
- marcadores na timeline: o título de cada bloco (azul), `Conferir` (laranja) e `TELA:` (lilás);
- no bruto (visualizador de origem): a transcrição e um marcador por trecho (verde usa, amarelo alternativa, rosa descarta, azul nota).

Depois: lembre o **Ctrl+S**, peça para o editor revisar e, quando ele aprovar a montagem, rode `checar <seq>` e `transcrever <seq>` (a transcrição da sequência montada é a base do plano de cenas e do encaixe dos motions).

## Refazer um trecho

Mude só as linhas do bloco no `decupagem-<seq>.md` e monte de novo: o backup é refeito, e a montagem anterior (com os ajustes do editor) fica na sequência duplicada. Se o editor já ajustou muita coisa à mão, prefira mostrar o trecho novo e deixar ele colar na timeline.
