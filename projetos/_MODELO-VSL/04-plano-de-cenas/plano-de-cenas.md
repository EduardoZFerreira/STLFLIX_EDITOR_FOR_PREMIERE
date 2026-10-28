# Plano de cenas — VSL-EXEMPLO · corpo

Como preencher (guia completo: `5-guias/plano-de-cenas.md`):

1. Rode `transcrever corpo` e abra `06-transcricoes/corpo.md`.
2. Com a transcrição e a copy lado a lado, decida onde entra cada motion: uma ideia por cena.
3. Para cada cena escreva o cabeçalho com a **frase-gatilho copiada da transcrição** e, embaixo, a descrição do motion.
4. Valide com `node 3-motions/motions.mjs validar --projeto projetos/<VSL>`, renderize com `render` e encaixe com `python -m stlflix ... motions corpo --aplicar`.

Exemplo real (VSL-Shark, corpo):

## Bloco 02 · Apresentação

- **B02A** · Lincoln Almeida — "Lincoln Almeida e eu sou um dos"
  duração: 6
  > 0.3 | título: Lincoln Almeida [tamanho=médio] | legenda: um dos fundadores da STLFLIX

- **B02B** · STLFLIX em números — "47.500 assinantes e mais de 100"
  duração: 11
  > 0.3 | número: 47.500 [conta] | legenda: assinantes
  > 3.4 | número: +100 [tamanho=médio] | legenda: pessoas trabalhando
  > 6.4 | kicker: POR UM ÚNICO OBJETIVO | frase: Fazer você **viver de impressão 3D**

- **B02C** · O valor volta inteiro em cupons — "nessa Black Friday, o valor da oferta"
  duração: 8
  topo: NESSA BLACK FRIDAY
  > 0.6 | ícone: pilha-moedas [altura=150] | título: Volta **inteiro** | legenda: em cupons de filamento

## Bloco 05 · Luan

- **B05A** · Caminho 1 · Marketplace — "o primeiro caminho é o marketplace"
  duração: 6
  > 0.3 | kicker: CAMINHO 1 DE 4 | ícone: casa-marketplace [altura=190, atraso=0.4] | título: Marketplace [tamanho=médio, atraso=0.9]

- **B05H** · Quase R$ 5 mil com 1 impressora — "o Luan achou um produto com potencial de lucro"
  duração: 7 · poeira: 0-7
  > 0.3 | kicker: O PRODUTO QUE O LUAN ACHOU | número: R$ 5 mil [verde, conta] | legenda: quase isso de lucro, com 1 impressora

- **B05O** · Kit do Leão: R$ 24,50 → R$ 39,90 — "o kit do leão começou por R$ 24,50"
  duração: 7 · poeira: 2.5-7
  > 0.3 | kicker: KIT DO LEÃO | título: R$ 24,50 [tamanho=pequeno, risca=1.4] | número: R$ 39,90 [tamanho=médio, verde, atraso=2.2]
  tela: o preço antigo é riscado e o novo entra em verde
