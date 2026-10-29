---
name: finalizar
description: Checagens antes de exportar (mídia do Drive, trilhas desligadas, pan e áudio faltando), exportação do vídeo e entrega dos XMLs no Drive. Use quando o editor disser que vai exportar, pedir para checar a sequência ou mandar os XMLs para o Drive.
---

# Finalizar e entregar

1. **Reconectar a mídia do Drive** (a exportação sai preta sem aviso quando o FilmCraft perde a leitura do Drive):
   `./stlflix.cmd --projeto <VSL> reconectar`
2. **Checar**: `./stlflix.cmd --projeto <VSL> checar [seqs]`
   Acusa quadro preto em mídia do Drive, trilha desligada com clipes, áudio só de um lado, áudio dobrado em aninhada, cobertura de áudio baixa e mídia offline. `--rapido` pula o teste de quadros pretos.
   Só siga com **zero erros**. Para cada erro, proponha a correção (skill `problemas`) e aplique com o ok do editor.
3. **Exportar o vídeo**: pelo FilmCraft, com o editor (ele escolhe In/Out, resolução e preset). Se ele pedir para você exportar, use `file.exportMedia` com `wait:false` e acompanhe com `jobs.list`; nunca `wait:true` (trava o controle). Conte ~2,7–3 quadros/s em 2160×3840: 19 min levam ~2h15. Durante o render, confira quadros de take e de B-roll do Drive a cada 5 min.
   Não sobrescreva exportações anteriores: mova para `07-exports/_anteriores (data)`.
4. **XMLs para o Drive** (depois que o editor salvou):
   `./stlflix.cmd --projeto <VSL> exportar-xml [seqs] [--destino <pasta>]`
   Vai para `drive.entrega_xml`; a versão anterior fica em `_XML anteriores (dd-mm HHhMM)`.

Avise ao editor: ao importar esses XMLs em outra máquina, o FilmCraft pode perder cortes de áudio encostados em crossfade e trazer a V2 desligada. Depois de importar, rode `checar` lá também.
