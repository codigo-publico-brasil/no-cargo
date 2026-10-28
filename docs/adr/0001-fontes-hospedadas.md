# 0001. Fontes e tokens do Código Público Brasil hospedados no próprio site

## Contexto
O guia de identidade da organização (https://codigo-publico-brasil.github.io/identidade/) define Fraunces (títulos), Inter (texto) e JetBrains Mono (dados), e recomenda que as aplicações hospedem as fontes junto do site. O No Cargo não carrega nada de outro domínio e não coleta dados de quem visita; o Google Fonts enviaria o IP de cada visitante a terceiros.

## Decisão
- Guardar em `src/no_cargo/static/fonts/` o subconjunto `latin` (woff2) das três fontes, todas sob a SIL Open Font License 1.1: Fraunces 600, Inter 400 a 600 e JetBrains Mono 400 a 600 (fontes variáveis). Declará-las com `@font-face` em `style.css`.
- Guardar em `static/tokens.css` uma cópia do `tokens.css` da organização (cores e tema claro/escuro) e em `static/no-cargo.svg` o símbolo do projeto, sem alterações.

## Consequências
- Cerca de 115 KB a mais por visitante novo, com cache do navegador. Sem dependência de pacote e sem requisição a terceiros.
- Quando o `tokens.css` ou o símbolo mudarem no site da organização, é preciso atualizar as cópias.
- O site não oferece tema escuro: todas as páginas levam `data-theme="light"` no `<html>`, o que desliga o bloco escuro do `tokens.css` sem alterar a cópia. O botão de tema (`theme.js`) do guia não é usado.
