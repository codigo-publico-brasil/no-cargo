# 0002. Cartões de compartilhamento por página, gerados com Pillow

## Contexto
Ao compartilhar o link de uma pessoa ou de um estado, a prévia mostrava sempre o cartão da marca (`og.png`). O guia de identidade pede imagem Open Graph de 1200 × 630 px em toda página. Pessoa e estado precisam de cartão próprio: nome, cargo, partido e, para a pessoa, a foto oficial que o site já serve.

O build não pode depender de rede nem de navegador, e gera mais de 2.300 imagens.

## Decisão
- Adicionar a dependência `pillow` para desenhar os cartões (JPEG, qualidade 72, cerca de 25 a 45 KB cada) em `og/pessoa/` e `og/estado/`.
- Guardar em `src/no_cargo/cartoes/fontes/` as fontes Fraunces e Inter em TrueType (SIL Open Font License 1.1, publicadas no Google Fonts), porque o Pillow não lê woff2. São as mesmas famílias que o site já usa; o `static/fonts/` continua só com os woff2 servidos aos visitantes.
- As cores são as de `tokens.css`; o símbolo sai do `og.png`. Foto ausente ou ilegível gera o cartão sem foto, sem quebrar o build.
- Páginas que não são de pessoa nem de estado continuam com o `og.png` da marca.

## Consequências
- Cerca de 80 MB a mais no site publicado na primeira vez; depois, só mudam os cartões cujos dados mudarem (a geração é determinística).
- O build leva cerca de um minuto a mais.
- As fontes TrueType (1,2 MB) entram no pacote, mas não são servidas.
