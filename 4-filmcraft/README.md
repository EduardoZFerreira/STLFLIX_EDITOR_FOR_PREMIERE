# 4-filmcraft · ferramentas de edição

`stlflix` é a linha de comando que opera o FilmCraft nas VSLs. Todos os comandos recebem a pasta do projeto, que tem o `config.json`:

```
./stlflix.cmd --projeto projetos/<VSL> <comando>        (na raiz do kit)
```

`stlflix.cmd` chama o Python criado pelo instalador em `%LOCALAPPDATA%\STLFLIX_EDITOR\venv`, onde o pacote está instalado em modo editável (`pip install -e 4-filmcraft[gpu]`, ver `pyproject.toml`): mudanças em `stlflix/` valem na hora.

## Comandos

| Comando | O que faz | Muda o projeto? |
|---|---|---|
| `painel` | Página local (`painel/index.html`) com as ferramentas e o que falta em cada VSL; não precisa de `--projeto` | não |
| `nova [--nome X]` | Cria a pasta `--projeto` a partir de `projetos/_MODELO-VSL` (o exemplo do plano vira `EXEMPLO-plano-de-cenas.md`) | não |
| `abrir` | Abre o FilmCraft com o controle ligado (cria o token na primeira vez) e o `.fcproj` do config | não |
| `status` | Mostra o que já está preenchido: roteiro, plano de cenas, motions, transcrições, sequências | não |
| `transcrever <seq>` | Exporta o áudio da sequência, transcreve com Whisper e gera o documento por blocos do roteiro. Avisa trechos mudos e possíveis tropeços | não |
| `blocos <seq>` | Refaz só o documento por blocos (depois de mudar âncoras ou grafias no config) | não |
| `plano` | Valida o `plano-de-cenas.md` e lista as cenas que ainda não têm `.mov` | não |
| `motions <seq>` | Mostra onde cada motion vai entrar e quais ficam de fora | não |
| `motions <seq> --aplicar` | Coloca os motions na trilha (V2, escala 200) e liga a trilha | **sim** |
| `enquadrar [seqs]` | Mostra quantos takes estão fora do enquadramento padrão | não |
| `enquadrar [seqs] --aplicar` | Aplica a escala e a âncora do config nos takes, inclusive dentro de sequências aninhadas | **sim** |
| `checar [seqs]` | Checagens antes de exportar: quadro preto (mídia do Drive), trilha desligada, áudio de um lado só, áudio dobrado, áudio faltando, mídia offline | não |
| `reconectar` | Reconecta a mídia do Drive (G:) no mesmo caminho e resolve o "MEDIA UNREADABLE" | sim (só os links) |
| `exportar-xml [seqs]` | Exporta XML (FCP7) para `drive.entrega_xml`; a versão anterior vai para `_XML anteriores (data)` | não |

`<seq>` é a chave do config (`corpo`, `lead-a`…) ou o nome da sequência no FilmCraft. Sem `seqs`, vale para todas as do config.

Depois de qualquer `--aplicar`, revise na timeline e salve com **Ctrl+S**.

## Fluxo típico de uma VSL

```
abrir                       → FilmCraft com controle
transcrever corpo           → 06-transcricoes/corpo.md   (o editor lê e escreve o plano de cenas)
plano                       → confere o formato do plano
(renderizar os motions no HyperFrames → 05-motions)
motions corpo               → confere o encaixe
motions corpo --aplicar
enquadrar --aplicar
checar                      → zero erros antes de exportar
exportar-xml
```

## Requisitos

- FilmCraft 0.13+ aberto **pelo comando `abrir`**: sem o token, o controle não liga.
- Python 3.12 com o pacote instalado pelo `1-instalacao/instalar.ps1` (o `transcrever` precisa do faster-whisper; os outros comandos só da biblioteca padrão e do numpy).
- ffmpeg no PATH.

## `_legado/`

Os scripts que rodaram nas VSLs do Hugo e do Shark, guardados como referência. Têm caminhos e nomes fixos e **não** devem ser usados direto. O que valia deles está no `stlflix/`, e o que ainda falta portar está no `PLANO.md`: B-roll 9:16 por keyframes, peças 3D, bake de LUT, reconstrução de áudio de XML e decupagem automática.
