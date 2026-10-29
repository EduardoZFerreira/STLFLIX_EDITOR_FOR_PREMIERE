# Campanhas dos motions

Cada pasta é uma campanha visual dos motions das VSLs (`bf26` = Black November 2026). A VSL escolhe a campanha em `config.json → motions.campanha`.

## O que a campanha muda

| Arquivo | O que é |
|---|---|
| `campanha.json` | Nome, texto do logo e as cores: `degrade` (títulos, palavra-chave e botão de CTA), `barra` (barrinha acima do título) e `brilho` (embaixo dos ícones). Opcional: `resultado`, o degradê dos números de resultado (`número: … [verde]`); sem ele, fica o verde → azul da marca |
| `<nome>.png` | Ícones 3D usados no plano de cenas (`ícone: pilha-moedas`). PNG com fundo transparente, 520 px de altura, nome sem espaço, acento ou maiúscula |
| `logo-kv.png` | Logo do key visual (peça `logo` no plano). PNG transparente, até 1680 px de largura |

A marca STLFLIX (fontes, branco e o verde-limão de resultado e de CTA) é a mesma em todas as campanhas.

```json
{
  "nome": "Black November 2026",
  "logo": { "arquivo": "logo-kv.png", "texto": "Black November · Infinitas possibilidades para viver de impressão 3D" },
  "cores": { "degrade": ["#8DFB5E", "#2EE6A6", "#22C7F0", "#2F7BFF"], "barra": "#2F7BFF", "brilho": "#07EF2D" }
}
```

## Para o design: o que mandar

- Os **ícones** em PNG com **fundo transparente**, grandes (pelo menos 520 px de altura), um por arquivo, com um nome que diga o que é ("Pilha de moedas.png").
- O **logo** do key visual em PNG transparente, com "logo" no nome do arquivo.
- As **cores** do degradê principal da campanha em hexadecimal (3 ou 4, na ordem), e a cor de destaque se houver.

Não precisa recortar nem redimensionar: o kit faz isso.

## Criar e conferir (com o Claude: "Cria a campanha de Natal com os arquivos desta pasta")

```
./stlflix.cmd campanha nova natal26 --nome "Natal 2026" --de "<pasta do design>" --cores "#..,#..,#..,#.."
./stlflix.cmd campanha importar natal26 --de "<pasta>"     ícones ou logo novos
./stlflix.cmd campanha conferir natal26
./stlflix.cmd campanha listar
node 3-motions/motions.mjs amostra --campanha natal26      prévia renderizada em natal26/_amostra (fora do git)
```

Pastas que começam com `_` são de teste e não aparecem na lista.
