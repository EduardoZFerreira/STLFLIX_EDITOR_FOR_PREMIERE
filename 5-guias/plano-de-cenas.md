# Como escrever o plano de cenas

O plano de cenas (`<pasta da VSL>/04-plano-de-cenas/plano-de-cenas.md`) é **um arquivo só para duas coisas**:

1. **Encaixar** cada motion na timeline, pela frase-gatilho.
2. **Gerar** o motion (o .mov transparente), pela descrição embaixo da cena.

Você escreve a partir da transcrição (`06-transcricoes/<sequência>.md`) e da copy. Uma cena por ideia.

## Formato

```
## Bloco 05 · Luan

- **B05H** · Quase R$ 5 mil com 1 impressora — "o Luan achou um produto com potencial"
  duração: 7 · poeira: 0-7
  > 0.3 | kicker: O PRODUTO QUE O LUAN ACHOU | número: R$ 5 mil [verde, conta] | legenda: quase isso de lucro, com 1 impressora
```

| Parte | O que é |
|---|---|
| `## Bloco 05 · Luan` | Agrupa as cenas pelo bloco do roteiro. Ajuda a achar a frase certa quando ela se repete no vídeo. |
| `**B05H**` | Código da cena: **B + número do bloco + letra**. É o nome do .mov (`B05H-quase-r-5-mil….mov`). |
| `Quase R$ 5 mil…` | Nome da cena (aparece no LEIAME e na prévia). |
| `"o Luan achou…"` | **Frase-gatilho**: 4 a 8 palavras faladas no momento em que o motion entra. **Copie da transcrição.** |
| `duração: 7` | Segundos do motion. Opcional: `poeira: 0-7` (partículas subindo), `barra: não`, `fx: não`. |
| `topo: TEXTO` | Título fixo no alto durante a cena toda. As batidas viram frases de impacto, com a palavra-chave circulada. |
| `> 0.3 \| peça \| peça` | Uma **batida**: o que aparece junto, a partir do segundo 0.3. Cada batida substitui a anterior. |

Sem o segundo (`> | peça`), as batidas se distribuem sozinhas pela duração. Use `> 3.8 lenta | …` para uma entrada mais lenta.

Linhas recuadas que não começam com `duração:`, `topo:` ou `>` são **notas** (ex.: `tela: mostrar o print do painel`) e não entram no motion.

Uma cena **só com a frase-gatilho**, sem descrição, também vale: o motion pode ter sido feito à mão. Ela é encaixada, mas não é gerada.

## Peças

`**palavra**` em qualquer texto = destaque em gradiente verde-azul.

| Peça | Uso | Opções |
|---|---|---|
| `kicker: TEXTO` | Rótulo pequeno em caixa alta, acima do título | `atraso=0.4` |
| `título: Texto **chave**` | Título. O tamanho se ajusta: até 13 letras fica grande | `tamanho=grande\|médio\|pequeno`, `largo`, `risca=1.4` (risca o texto no segundo 1.4) |
| `frase: Texto **chave**` | Frase-tese com peso variável (a letra "engorda") | `px=110` |
| `número: R$ 5 mil` | Número grande | `verde` (resultado), `negativo`, `gradiente`, `tamanho=…`, `conta` (anima a contagem de 0 até o valor) |
| `legenda: texto` | Linha de apoio embaixo do título ou do número | `atraso=…` |
| `ícone: nome` | Ícone do kit da campanha (`2-design-system/campanhas/<campanha>/`). O painel mostra os ícones da campanha da VSL com o nome de cada um (clique para copiar) | `altura=150` |
| `ícones: nome, nome, nome` | Fileira de ícones | `altura=120`, `passo=0.25` |
| `logo` | Logo do key visual da campanha | `largura=940` |
| `cta: QUERO O VITALÍCIO` | Botão de chamada com seta | |
| `chips: item; item; item` | Pílulas em sequência | `check`, `setas`, `colunas=2`, `passo=0.8`, `risca=…`, `apagado` |

A `conta` descobre sozinha prefixo e sufixo: `R$ 5 mil` conta de R$ 0 mil a R$ 5 mil. Quando precisar mudar, use `conta=5, antes="R$ ", depois=" mil", dec=1`.

## Boas práticas (o padrão aprovado nas VSLs)

- **Uma ideia por batida.** Duas a quatro batidas por cena; de 2,7 a 3,4 s entre elas.
- **Frase de impacto curta**: até 14 letras por linha, no máximo 2 linhas. A palavra-chave entre `**`.
- **Verde só para resultado** (números de venda e lucro) e para o CTA.
- **Números com `conta`** quando forem o centro da cena.
- **O motion acompanha a fala**: confira se a frase-gatilho está no começo do que a tela mostra.
- **Cada sequência tem o seu plano** (corpo, corpo curto, leads), porque versões curtas usam outras falas.

## Conferir

```
node 3-motions/motions.mjs validar --projeto <VSL>
node 3-motions/motions.mjs render  --projeto <VSL> --so B05H,B05I     ← só algumas cenas, para testar
```
