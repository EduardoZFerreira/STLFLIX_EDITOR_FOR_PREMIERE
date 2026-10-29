# Comece aqui

Bem-vindo ao **STLFLIX_EDITOR**, o kit do time de edição para as VSLs verticais (9:16) da STLFLIX.

## O que é isso

Você continua editando no **FilmCraft**, como sempre. O kit coloca um assistente ao seu lado, o **Claude**, que faz as partes repetitivas:

- **Transcreve** a fala da sequência, com o minuto e o segundo de cada frase.
- **Cria os motions**: os letterings animados da STLFLIX (títulos, números, ícones), a partir do que você planejar.
- **Coloca cada motion** no segundo certo da timeline, na frase em que ele deve aparecer.
- **Confere** o projeto antes de exportar, procurando problemas que já aconteceram no time (vídeo preto, áudio de um lado só).

Você conversa com o Claude em português, como num chat. **Ele sempre mostra o que vai fazer e espera você aprovar** antes de mexer na sua timeline. Não precisa saber programar.

## Do que você precisa

- **Claude Code** instalado e com login feito. É o programa onde você conversa com o Claude. Se ainda não tem, peça ajuda a quem te passou este link.
- **Uma conta no GitHub** (gratuita, em https://github.com) **com o convite aceito** para o repositório do kit. O kit é privado: passe o seu nome de usuário do GitHub para quem te mandou o link, e aceite o convite que chega no seu e-mail.
- **FilmCraft 0.13 ou mais novo.** Ele é instalado pelo **ArtCraft Launcher**: baixe em https://getartcraft.com.
- **Google Drive para computador** conectado (normalmente aparece como unidade G:; o kit acha a letra sozinho), onde ficam os brutos e as entregas.
- Recomendado: computador com **placa de vídeo NVIDIA**. Sem ela tudo funciona, só a transcrição fica mais lenta.

O resto (Git, Node.js, Python, ffmpeg, as ferramentas de transcrição e de motion) o Claude instala para você.

## Instalar (uma vez só)

1. Abra o **Claude Code**.
2. Copie e cole esta mensagem:

   > Instale o kit STLFLIX_EDITOR deste repositório: `<link do repositório>`. Clone em `C:\STLFLIX_EDITOR` e siga as instruções de instalação do próprio kit.

3. Acompanhe. O Claude vai:
   - baixar o kit. Na primeira vez pode abrir uma **janela de login do GitHub**: entre com a sua conta (a mesma que recebeu o convite);
   - conferir o que já está instalado no computador e te mostrar o que falta;
   - pedir **permissão** para baixar e instalar. É normal: o Claude Code sempre pergunta antes de usar o computador. Se tiver dúvida sobre algum pedido, pergunte a ele o que aquilo faz;
   - talvez pedir para você **fechar e abrir o Claude Code** no meio do caminho, para o Windows enxergar o que acabou de ser instalado.

   Na primeira vez leva de 5 a 15 minutos.
4. No fim, ele abre o **painel do editor** no navegador e cria o atalho **Painel STLFLIX** na sua área de trabalho.

A partir daí, **sempre abra o Claude Code na pasta `C:\STLFLIX_EDITOR`**. É ali que ele encontra as instruções do kit e as suas VSLs.

## O painel do editor

É a sua página de apoio. Abra pelo atalho **Painel STLFLIX** da área de trabalho, ou peça **"Abre o painel"** ao Claude. Se tiver versão nova do kit, ele avisa no topo. Ele mostra:

- no topo, o **menu da VSL**: escolha em qual VSL vai trabalhar ou **crie uma nova**. O painel lembra a escolha neste computador;
- se o computador está pronto, e o botão **⬇ ArtCraft** para baixar o ArtCraft Launcher (que instala e atualiza o FilmCraft);
- o que já está feito na VSL escolhida e **o próximo passo**, com a frase pronta para copiar e mandar ao Claude;
- o passo a passo completo, o plano de cenas explicado com exemplo, as palavras novas e as dúvidas comuns.

Se ficar perdido, abra o painel.

## Uma VSL, do roteiro à entrega

| | Etapa | Quem faz | O que pedir ao Claude |
|---|---|---|---|
| 1 | **Criar a VSL**: uma pasta para o roteiro, o plano e tudo o que for gerado | juntos | "Cria uma VSL nova chamada VSL-Nome" |
| 2 | **Decupar** no FilmCraft | você | |
| 3 | **Transcrever** a sequência | Claude | "Abre o FilmCraft e transcreve o corpo" |
| 4 | **Escrever o plano de cenas**: onde entra cada motion e o que ele mostra | você | "Confere meu plano de cenas" |
| 5 | **Criar os motions**: primeiro 2 ou 3 para você ver, depois todos | Claude | "Cria os motions B05A e B05B para eu ver" |
| 6 | **Pôr na timeline**: ele mostra a lista, você aprova, revisa e salva (Ctrl+S) | Claude + você | "Coloca os motions no corpo" |
| 7 | **Conferir e entregar**: você exporta o vídeo, ele manda os XMLs para o Drive | juntos | "Confere tudo antes de exportar" |

Os pedidos são só exemplos: fale do seu jeito.

Para começar a primeira VSL, tenha em mãos o **roteiro do teleprompter** (.txt, com os blocos marcados assim: `--- BLOCO 5 · Título ---`) e o **projeto da VSL já salvo no FilmCraft**.

## O plano de cenas em um minuto

É a parte mais importante do seu trabalho no kit. É um arquivo de texto onde você lista os motions. Cada um tem três partes:

```
## Bloco 05 · Luan

- **B05H** · Quase R$ 5 mil — "Luan achou um produto com potencial de"
  duração: 7
  > 0.3 | kicker: O PRODUTO QUE O LUAN ACHOU | número: R$ 5 mil [verde, conta] | legenda: quase isso de lucro, com 1 impressora
```

1. **O código** (`B05H`): bloco 5, cena H. Vira o nome do arquivo do motion.
2. **A frase-gatilho**, entre aspas: as palavras que o apresentador fala no momento em que o motion deve aparecer. **Copie da transcrição**, do jeito que foi dito: é por ela que o Claude acha o lugar do motion na timeline.
3. **O que aparece na tela**: quantos segundos dura e, na linha com `>`, as peças separadas por `|`. Aqui: uma linha pequena em cima, um número verde que conta até R$ 5 mil e uma legenda embaixo.

Resultado: o motion aparece acima da cabeça do apresentador, no segundo em que ele fala a frase.

Cada VSL nova já vem com um plano de exemplo completo. O guia com todos os tipos de peça está em `5-guias/plano-de-cenas.md`, e o painel explica com imagem.

## Dicas para conversar com o Claude

- **Fale normal**: "transcreve o lead B", "o motion do bloco 5 entrou atrasado", "o áudio está estranho".
- **Ele pede antes de mexer.** Responda "pode colocar" para aprovar, ou diga o que mudar.
- **Para parar**, aperte **Esc** ou escreva "para".
- **Vai trabalhar em outro projeto no FilmCraft?** Avise: "calma, estou em outro projeto".
- **Salvar é com você**: depois de revisar a timeline, aperte **Ctrl+S** no FilmCraft.

## Se algo der errado

Conte ao Claude o que você viu, do seu jeito: "a exportação saiu preta", "o áudio está só de um lado", "os motions não aparecem". Os problemas que já aconteceram no time estão documentados no kit, e ele sabe como resolver.

## Atualizar o kit

Peça **"Atualiza o kit"**. O Claude baixa a versão nova e confere a instalação. Suas VSLs não são afetadas: elas ficam nas pastas que você escolheu, fora do kit.
