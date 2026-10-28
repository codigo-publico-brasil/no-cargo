# Publicação no GitHub Pages

O site é estático e gerado localmente a partir do DuckDB da plataforma, então o deploy é: gerar e publicar a pasta `dist/` na branch `gh-pages`.

## Publicar

Com o warehouse da plataforma parado (o DuckDB aceita um escritor por vez) e a `main` atualizada:

```bash
scripts/publicar.sh              # gera dist/, commita em cima do gh-pages e envia (sem push forçado)
scripts/publicar.sh --sem-push   # só confere: gera e commita num clone temporário, sem enviar
```

O script recusa publicar fora da `main`. O histórico do `gh-pages` é mantido; cada publicação é um commit.
Para testar em outro endereço: `NO_CARGO_URL=https://exemplo.org uv run no-cargo`.

## Uma vez só

Feito em 27 e 28/10/2026: repositório público com licença AGPL-3.0, Pages na branch `gh-pages`, domínio `nocargo.codigopublicobrasil.com.br`, `CNAME no_cargo → codigo-publico-brasil.github.io` no DNS e Enforce HTTPS.

Falta: Google Search Console e Bing Webmaster (verificar o domínio com um registro TXT no DNS e enviar `sitemap.xml`).

## Como o site é achado

- Buscadores: `<title>`, descrição, canônico, Open Graph, JSON-LD (WebSite, Person, BreadcrumbList), `sitemap.xml`.
- Agentes de IA: `robots.txt` aceita os rastreadores conhecidos (é um pedido, não uma trava); `llms.txt` resume o site; as páginas são HTML puro, legível sem JavaScript.

## Correções

Pelo formulário de issue (`.github/ISSUE_TEMPLATE/correcao.yml`); cada página traz um link que já preenche página e assunto.

## Acessos

O GitHub Pages não tem log de acesso. Hoje: Search Console (impressões, cliques, indexação), sem script no site. Contador de visitas exigiria um script de outro domínio, contra a regra de não coletar dado de quem visita; só com ADR.
