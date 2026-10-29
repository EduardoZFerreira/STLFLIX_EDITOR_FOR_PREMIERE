---
name: problemas
description: Diagnóstico dos problemas conhecidos do FilmCraft e do kit (controle não conecta, MEDIA UNREADABLE, exportação preta, áudio de um lado só, áudio sumido após XML, motions que não aparecem, render lento, transcrição sem GPU). Use quando algo der errado na edição, no render ou num comando do kit.
---

# Problemas conhecidos

Detalhes e histórico em `5-guias/FilmCraft_Guia_Aprendizados.md` (seção 6).

| Sintoma | Causa | O que fazer |
|---|---|---|
| Comando diz que o FilmCraft não responde / "control authentication failed" | FilmCraft aberto sem o token (0.13+ exige) | Editor fecha o FilmCraft; rode `stlflix ... abrir`. Se houver janela de diálogo aberta no app, o controle espera. |
| "MEDIA UNREADABLE", B-roll some do monitor, exportação/quadros pretos | FilmCraft perdeu a leitura do Drive | `stlflix ... reconectar`, depois `checar`. Pastas do Drive como "disponível off-line" ajudam. |
| Áudio só no lado esquerdo | Clipes com pan −100 numa trilha só | `checar` acusa. Corrigir com `effects.setParam` balance 0 (abra a sequência antes: `sequence.open`). Backup e ok do editor. |
| Áudio alto demais numa sequência aninhada | Aninhada com pan 0 em A1 e A2 (dobra ~+5 dB) | A1 = −100, A2 = +100. |
| Trecho mudo após importar XML | Import FCP7 descarta cortes de áudio encostados em crossfade | Compare a contagem de clipes com o XML. Reconstrução: um corte de áudio por corte de vídeo + `sequence.applyAudioTransition` (referência em `4-filmcraft/_legado/vsl-shark/reconstruir_extras.py`). Sempre com backup da sequência. |
| Motions na timeline mas não no render | V2 desligada (comum após XML) | `timeline.setTrack {track:<id>, enabled:true}` com a sequência aberta, ou `motions <seq> --aplicar` de novo. |
| Motion no lugar errado | Frase-gatilho repetida na montagem | Frase mais específica no plano de cenas. |
| Exportação lenta | Gargalo de CPU (~3 quadros/s em 4K vertical) | Normal. Meia resolução e NVENC não aceleram. Use `wait:false`. |
| Transcrição lenta / "device cpu" | Sem placa NVIDIA ou bibliotecas CUDA | Com NVIDIA: rode o instalador de novo (instala o extra `[gpu]`). |
| Render de motions para no meio | Disco temporário cheio | Libere espaço em C: ou use `--por-parte 15`. |
| `stlflix.cmd` não acha o Python | Instalador não rodou | Skill `instalar-kit`. |
| Comando do Git/Node/ffmpeg "não encontrado" logo após instalar | PATH do terminal antigo | Fechar e abrir o Claude Code. |

Se o problema for novo: investigue com o editor, resolva com backup, e no fim proponha acrescentar uma linha nesta tabela e no guia.
