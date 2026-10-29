# STLFLIX_EDITOR

Kit do time de edição da STLFLIX para VSLs 9:16. Junta a edição no **FilmCraft** (operado pelo canal de controle) com os **motions da marca** gerados no HyperFrames a partir do plano de cenas que o editor escreve. Quem conversa com você é um editor de vídeo: responda em **português do Brasil**, sem jargão de programação, e cite posições como timecode da timeline.

## Qual VSL

O kit serve para qualquer VSL de qualquer editor do time. Nenhuma VSL é a "padrão": não assuma a VSL-Shark nem a primeira da pasta.

- **A pasta da VSL fica onde o editor quiser** no computador dele (não precisa estar dentro do kit). Tudo o que o kit gera para ela (motions, pasta de trabalho do HyperFrames, transcrições, exportações) vai para dentro dessa pasta. O kit anota o caminho de cada VSL em `%LOCALAPPDATA%\STLFLIX_EDITOR\vsls.json`, e `--projeto` aceita só o nome (`--projeto VSL-Ender-3`) ou o caminho.
- Se o editor ainda não disse em qual VSL vai trabalhar e o pedido depende de uma, rode `./stlflix.cmd vsls` e pergunte qual é, com a opção **Criar uma VSL nova** (skill `nova-vsl`). Se não houver nenhuma, ofereça criar.
- "Vamos trabalhar na VSL-X" (o pedido que o painel copia) fixa a VSL da conversa: use `--projeto VSL-X` até ele trocar.
- Pasta de VSL que veio de outro lugar (copiada de outro editor, movida de disco): `./stlflix.cmd vsls --anotar "<pasta>"`. Se ele não souber o caminho, `./stlflix.cmd escolher-pasta` abre a janela do Windows para ele escolher.
- O painel tem o mesmo menu (escolher VSL ou criar nova) e o botão para baixar o ArtCraft Launcher (https://getartcraft.com).

## Regras (sempre)

- **Mostrar antes de mudar.** Todo comando que mexe no projeto do FilmCraft (`--aplicar`, ou qualquer chamada direta que altere a timeline) só roda depois de você mostrar o que vai mudar e o editor aprovar. O jeito comum de aprovar é "Coloque…" / "Pode aplicar".
- **Backup antes de operação destrutiva**: duplique a sequência (`project.select` + `edit.duplicate`) antes de apagar ou reconstruir clipes. Nunca apague trilhas vazias que o editor criou; só apague trilhas temporárias que você mesmo criou, pelo id.
- **Nunca sobrescrever exportações, XMLs ou renders anteriores**: mova o antigo para uma subpasta `_… anteriores (dd-mm HHhMM)`. O `exportar-xml` já faz isso.
- **O editor revisa na timeline antes de qualquer render final.** Não exporte vídeo nem renderize todos os motions sem ele pedir.
- **Teste com pouco**: no render de motions, primeiro `--so` com 2 ou 3 cenas. Cada cena leva ~30 s.
- **Não mexa no projeto se o editor disser que está em outro** ("calma, estou em outro projeto"): pare e espere.
- Ao fim de cada etapa que mudou a timeline, lembre: **salvar com Ctrl+S** no FilmCraft.
- O **plano de cenas é do editor**. Você pode sugerir cenas ou fazer um rascunho quando ele pedir (skill `plano-de-cenas`), mas o rascunho vai em `04-plano-de-cenas/rascunho-<seq>.md` e só passa para o `plano-de-cenas.md` o que ele aprovar.
- Não apague `05-motions/.registro-render.json`: é como o kit sabe quais motions mudaram no plano depois do render.
- Processamento sutil (sem efeito "robótico"); B-roll preenche o quadro; inserts só de imagem vão sem áudio.

## Como rodar

Sempre a partir da **raiz do kit** (a pasta deste arquivo). `<VSL>` é o nome da VSL ou o caminho da pasta dela.

```
./stlflix.cmd --projeto <VSL> <comando>          edição (Python, FilmCraft)
node 3-motions/motions.mjs <comando> --projeto <VSL>   motions (HyperFrames)
powershell -ExecutionPolicy Bypass -File 1-instalacao/instalar.ps1 [-Verificar]
```

`stlflix.cmd` usa o Python criado pelo instalador em `%LOCALAPPDATA%\STLFLIX_EDITOR\venv` (fora do OneDrive e do git). Se não existir, rode o instalador.

| `stlflix` | O que faz | Muda o projeto? |
|---|---|---|
| `painel` (sem `--projeto`) | Gera e abre `painel/index.html`: menu para escolher ou criar a VSL, ferramentas instaladas (com o botão do ArtCraft), o que falta na VSL escolhida, o próximo passo e a galeria dos motions (miniaturas em `05-motions/_miniaturas`) | não |
| `vsls [--anotar PASTA] [--tirar VSL]` (sem `--projeto`) | Lista as VSLs deste computador e onde estão; anota uma pasta que já existe ou tira da lista (sem apagar) | não |
| `escolher-pasta` | Abre a janela "Escolher pasta" do Windows e mostra o caminho escolhido | não |
| `nova [--nome X] [--campanha bf26]` | Cria a pasta `--projeto` (caminho completo, onde o editor quiser) a partir de `projetos/_MODELO-VSL` e anota a VSL | não |
| `abrir` | Abre o FilmCraft com o controle ligado e o `.fcproj` do config | não |
| `status` | O que já está preenchido e gerado | não |
| `transcrever-brutos [--pasta] [--so] [--refazer]` | Cada take da câmera (`takes.prefixo`) → Whisper → `06-transcricoes/brutos.md`; pega os brutos do FilmCraft aberto, de `02-brutos` ou de `--pasta` | não |
| `decupar <seq> [--aplicar]` | Mostra os cortes da `06-transcricoes/decupagem-<seq>.md`; `--aplicar` duplica a sequência (backup), tira os brutos dela e monta a decupagem no estilo do time | **com --aplicar** |
| `transcrever <seq>` | Áudio da sequência → Whisper → documento por blocos em `06-transcricoes` | não |
| `blocos <seq>` | Refaz só o documento por blocos | não |
| `plano` | Valida o plano de cenas e lista as cenas sem .mov | não |
| `gatilhos <seq> [--plano arquivo]` | Confere as frases-gatilho na transcrição (sem FilmCraft nem .mov); serve para rascunho | não |
| `motions <seq> [--aplicar]` | Mostra o encaixe dos motions nas frases-gatilho; `--aplicar` coloca na V2 | **com --aplicar** |
| `enquadrar [seqs] [--aplicar]` | Escala e âncora padrão nos takes da câmera | **com --aplicar** |
| `checar [seqs] [--rapido]` | Checagens antes de exportar | não |
| `reconectar` | Resolve o "MEDIA UNREADABLE" do Drive (acha a letra do Drive sozinho; G: na maioria das máquinas) | só os links |
| `exportar-xml [seqs] [--destino]` | XML FCP7 para o Drive, guardando o anterior | não |

| `motions.mjs` | O que faz |
|---|---|
| `validar [--plano corpo]` | Confere a linguagem do plano e se os ícones existem na campanha |
| `gerar` | Cria a pasta de trabalho do HyperFrames |
| `previa` | Abre o Studio do HyperFrames |
| `render [--so B05H,B05I] [--por-parte 30]` | .mov por cena em `05-motions` + prévia sobre o quadro de referência; a versão anterior vai para `_motions anteriores (data)` |
| `render --pendentes` | Só as cenas sem .mov ou que mudaram no plano depois do render |
| `estado` | Situação de cada cena (pronto, falta, mudou, só encaixe), em JSON; o painel usa para a galeria |

Qualquer comando do `motions.mjs` aceita `--arquivo <plano.md>` no lugar do plano do config (ex.: o rascunho).

**Permissões**: `.claude/settings.json` libera os comandos do kit que só leem e pede confirmação para `--aplicar`, `reconectar`, `exportar-xml`, commit/push e apagar arquivos. Não afrouxe essas regras sem o editor pedir.

`<seq>` é a chave em `config.json → sequencias` (`corpo`, `lead-a`…) ou o nome da sequência no FilmCraft.

Quando o editor pedir "abre o painel" (ou quiser saber o que falta), rode `./stlflix.cmd painel`. Ele lê as pastas e o instalador em modo de conferência; não abre o FilmCraft.

## Fluxo de uma VSL

Cada etapa tem uma skill em `.claude/skills/`: `instalar-kit`, `nova-vsl`, `decupar`, `transcrever`, `plano-de-cenas`, `gerar-motions`, `encaixar-motions`, `finalizar`, `problemas`.

1. `nova` → editor preenche `config.json`, `01-roteiro/teleprompter.txt` e as pastas de assets; importa os brutos no projeto do FilmCraft.
2. `abrir` → `transcrever-brutos`.
3. **Decupagem com o Claude** (skill `decupar`): Claude escreve `decupagem-<seq>.md` cruzando os brutos com a copy → editor aprova → `decupar <seq> --aplicar` → editor revisa e salva. Depois, `transcrever <seq>` na sequência montada.
4. Editor escreve `04-plano-de-cenas/plano-de-cenas.md` a partir da transcrição e da copy, ou pede um rascunho (`5-guias/plano-de-cenas.md`).
5. `motions.mjs render --so …` (teste) → render completo.
6. `motions <seq>` → aprovação → `--aplicar`; `enquadrar --aplicar`. Editor revisa e salva.
7. `reconectar` → `checar` (zero erros) → exportar vídeo → `exportar-xml`.

## Operar o FilmCraft fora dos comandos

Para pedidos que os comandos não cobrem (ajustar um clipe, B-roll 9:16, reconstruir áudio), use o cliente Python do kit:

```
"$LOCALAPPDATA/STLFLIX_EDITOR/venv/Scripts/python.exe" -c "from stlflix.fc import FC; fc = FC(); print(fc.sequencias())"
```

`fc.run("<comando>", **params)` executa um comando do FilmCraft (`sequence.inspect`, `effects.setParam`, `media.relink`…); `fc.seq(nome)` devolve a sequência inspecionada.

Antes, leia `5-guias/FilmCraft_Guia_Aprendizados.md`: unidades de tempo (ticks), pegadinhas de parâmetro (`effects.setParam` só na sequência aberta, `timeline.setTrack` para ligar trilha, exportação com `wait:false`), e os problemas já conhecidos. Scripts antigos de referência estão em `4-filmcraft/_legado/` (caminhos fixos: não rode direto, adapte).

O controle só liga se o FilmCraft for aberto pelo `stlflix abrir` (FilmCraft 0.13+ exige o token em `~/.config/filmcraft/control_token`). Se a porta 9876 não responder, peça para o editor fechar o FilmCraft e rode `abrir` de novo.

## Atualizar o kit

Quando o editor pedir para atualizar: confira que `git status` não tem mudanças locais nos arquivos do kit (projetos ficam fora do git), rode `git pull` e depois o instalador com `-Verificar`. Se ele mudou algum arquivo do kit, mostre antes de fazer qualquer coisa.

## Onde está cada coisa

- `projetos/_MODELO-VSL/`: modelo de projeto (config comentado no `4-filmcraft/README.md` e `3-motions/README.md`).
- `3-motions/modelos/shark-vsl/`: o único modelo visual por enquanto (faixa de lettering acima da cabeça). Mudanças no motor valem para todo o time: só com pedido explícito e teste com `render --so`.
- `2-design-system/`: assets da marca e das campanhas (`campanhas/bf26`).
- `5-guias/`: aprendizados do FilmCraft, estilo de edição, linguagem do plano de cenas.
- `PLANO.md`: fases e decisões do kit.
- Projetos de VSL, brutos, renders e `.venv` **não vão para o git** (ver `.gitignore`).
