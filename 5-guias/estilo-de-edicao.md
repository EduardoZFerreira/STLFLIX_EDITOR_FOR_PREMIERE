# Estilo de edição STLFLIX (decupagem, crossfades e B-roll)

Estes valores foram medidos nos ajustes finos que o editor fez à mão nas montagens da VSL do Hugo (outubro de 2026). São o padrão de toda decupagem nova: quem monta já entrega nesse ponto, e a revisão fica só para o que é decisão de edição.

## Cortes na fala

- **Cabeça:** comece cerca de **2 quadros antes** da fala ficar audível (mediana medida: 2,1 quadros). Ache o início pela **energia do áudio**, não pelo início de palavra do Whisper: ele adianta 0,3 a 0,5 s, e cortes baseados nele foram aparados em 8 a 15 quadros em quase todos os takes.
- **Cauda:** termine **5 a 6 quadros depois** que a fala acaba (mediana: 5,5 quadros).
- **Pausas e respirações dentro do take:** corte tudo que passar de **cerca de 0,3 s**, dividindo o take em vários clipes.
- **Tropeços escondidos:** o Whisper funde frases repetidas numa palavra só, esticada (ex.: "ou seja 3… ou seja 13"). Desconfie de palavras com mais de 0,8 s ou de trechos longos demais para o texto (o `transcrever` avisa). Retranscreva só aquele trecho e fique com a **última repetição limpa**.

## Crossfade de áudio

Use **Constant Power, centrado no corte**:

- **3 quadros** em cortes no meio da frase e em consertos de tropeço;
- **9 a 12 quadros** em fim de frase ou parágrafo, mudança de assunto e entrada no CTA.

## B-roll 16:9 em vídeo 9:16

- Reenquadre com **keyframes de Movimento nos clipes da timeline** (escala de preenchimento ~355,6% para fonte 1920×1080, com keyframes de posição). **Nunca** renderize antes: o reenquadramento é revisado na timeline, e só depois de aprovado o vídeo é exportado.
- **Sem faixa preta, nunca.** Sempre preencha o quadro (~356 a 366%). Encaixe "inteiro" com barras (112,5%) foi trocado à mão em todos os casos.
- Tire do material de B-roll as aberturas de episódio e as cartelas gráficas ("3 empreendedores", "No episódio anterior").
- Insertos que são só imagem entram **sem áudio**.

## Revisão

O editor revisa, ajusta e salva (**Ctrl+S**). A automação mostra o que fez e onde; nada é renderizado ou exportado sem a revisão na timeline.

Fluxo técnico, problemas conhecidos e correções: `FilmCraft_Guia_Aprendizados.md`.
