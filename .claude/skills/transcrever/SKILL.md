---
name: transcrever
description: Transcreve uma sequência do FilmCraft com Whisper e gera o documento dividido pelos blocos do roteiro, com timecodes da timeline. Use quando o editor pedir a transcrição de uma sequência (corpo, leads) para escrever o plano de cenas ou conferir a decupagem.
---

# Transcrever uma sequência

1. O FilmCraft precisa estar aberto pelo kit: `./stlflix.cmd --projeto <VSL> abrir` (se já está aberto sem o controle, peça para fechar antes).
2. Confirme qual sequência: chave do `config.json` ou nome no FilmCraft. Para várias (leads A–G), rode uma por vez.
3. `./stlflix.cmd --projeto <VSL> transcrever <seq>` (rode em segundo plano; ~1 min por 10 min de vídeo com GPU).
   O comando exporta o áudio da sequência pelo próprio FilmCraft, então a transcrição já sai no tempo da timeline.
4. Leia a saída e repasse ao editor:
   - **trecho MUDO**: áudio faltando na timeline (comum depois de importar XML). Veja a skill `problemas`.
   - **palavra esticada**: possível tropeço repetido que ficou na decupagem.
   - **blocos não encontrados**: o bloco não está nesta sequência ou a fala mudou muito do roteiro. Se um bloco caiu no lugar errado, ajuste `blocos.ancoras` no config (`{"7": "frase do início do bloco"}`) e rode `blocos <seq>`.
5. Resultado: `<pasta da VSL>/06-transcricoes/<seq>.md` (para o editor ler) e `<seq>.json` (palavras com tempo, usado pelo encaixe dos motions). Mostre o caminho do `.md`.

Nomes de produto errados: acrescente em `transcricao.grafias` (regex → grafia certa) e rode `blocos <seq>`, sem transcrever de novo.
