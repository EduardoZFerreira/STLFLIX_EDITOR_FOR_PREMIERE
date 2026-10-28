# Assets STLFLIX

Biblioteca de assets compartilhada por todos os projetos HyperFrames da STLFLIX.

Design system oficial desde 2026-10-14: o do repositório github.com/sherecks/stlflix-design-system (projeto STLFLIX × Thales Brandão). Ele usa Sora + Inter, fundo `#0D0E14`, destaque `#5665F0`, painéis arredondados e gradiente em 1 palavra-chave.

| Arquivo / pasta | O que é |
| --- | --- |
| `frame.md` | **Spec da marca** no formato HyperFrames (cores, fontes, componentes, movimento, regras). Comece por aqui. |
| `design.md` | Documento de origem do design system, com a procedência de cada token (exato × estimado). |
| `tokens.css` | Tokens prontos (cores, fontes, escala, raio, sombra) e classes `.hf-*` (painel, barra, chip, palavra em gradiente). |
| `componentes/` | 21 sub-composições animadas prontas (lower third, capítulo, frase de impacto, CTA…). Catálogo em `componentes/README.md`. |
| `stlflix.svg` | Logo oficial (símbolo em gradiente + wordmark claro, só sobre fundo escuro). Fica na raiz, como no repositório original. |
| `logos/png/` | Variantes PNG do logo (branco, preto, símbolo). `Bambu Lab.png` é de parceiro. |
| `fonts/` | Fontes. Oficiais: `sora-*.woff2` e `inter-*.woff2` (na raiz de `fonts/`, como o `tokens.css` espera). As pastas são de versões anteriores (ver `fonts/README.md`). |
| `images/produtos/` | Fotos de impressoras e produtos (X1 Carbon, P1S, P1P, Neptune 3, Ender 3 V3, A1, K1…). |
| `images/renders-3d/`, `images/backgrounds/`, `images/screenshots/` | Renders de STL, fundos e capturas da plataforma. |
| `icons/`, `lottie/`, `luts/`, `modelos-3d/` | Ícones, animações Bodymovin, LUTs `.cube`, modelos 3D. |
| `video/footage/`, `video/b-roll/` | Gravações próprias e imagens de apoio. |
| `_arquivo/` | Specs anteriores (azul-noite + Montserrat/Lexend), guardadas só para consulta. |

## Usando em um projeto

1. Ligue a biblioteca ao projeto por junção, sem copiar nada:
   ```powershell
   New-Item -ItemType Junction -Path "<projeto>\assets" -Target "<workspace>\assets\STLFLIX"
   ```
2. Copie para o `compositions/` do projeto (pasta real, **não** junção) só os componentes que for usar, e ajuste os textos e as variáveis.
3. Nas composições, use caminhos **relativos**, iguais aos do repositório original: `<link rel="stylesheet" href="assets/tokens.css" />` e `assets/stlflix.svg`. Caminho a partir da raiz (`/assets/...`) quebra no Studio, e `compositions/` como junção quebra a resolução relativa.

A estrutura desta pasta (`tokens.css`, `fonts/*.woff2`, `stlflix.svg`) espelha a pasta `assets/` do repositório, e os componentes são idênticos aos de lá. **Não edite os arquivos de `componentes/`**: edite as cópias no projeto.

Exemplo funcionando: `testes/stlflix-vitrine` (todos os componentes em sequência).

Sem áudio: os projetos são motions e letterings sem som.

## Exportação (.MOV)

Os entregáveis são `.mov` com fundo transparente, para usar como overlay no editor:

```bash
npx hyperframes render --format mov --quality delivery -o renders/nome-do-motion.mov
npx hyperframes render -c compositions/lower-third.html --format mov -o renders/lower-third.mov   # um componente só
```

- O fundo da composição precisa ficar transparente: sem cor no `body` nem na raiz. Cenas cheias usam `.hf-fill` num filho.
- `--resolution 4k` não funciona com `mov`, porque o modo 4k não tem canal alfa. Para 4k, monte a composição já em 3840×2160.
- Para After Effects/Nuke, também existe `--format png-sequence` (frames RGBA).

Use nomes de arquivo em minúsculas, sem espaços nem acentos (ex.: `timelapse-dragao-01.mp4`).
