# Publicação no GitHub Pages

O site é estático e gerado localmente a partir do DuckDB da plataforma, então o deploy é: gerar e publicar a pasta `dist/` na branch `gh-pages`.

## Publicar

```bash
uv run nocargo                       # gera dist/ (com CNAME, robots.txt, sitemap.xml, llms.txt, 404.html)
git -C dist init -b gh-pages && git -C dist add -A && git -C dist commit -m "Publica o site"
git -C dist push -f https://github.com/codigo-publico-brasil/nocargo.git gh-pages
```

Para testar em outro endereço: `NOCARGO_URL=https://exemplo.org uv run nocargo`.

## Uma vez só

1. Repositório público (o GitHub Pages grátis exige) com licença definida (issues #32 e #33).
2. Settings, Pages: Source = branch `gh-pages`, domínio `nocargo.codigopublicobrasil.com.br`, Enforce HTTPS.
3. DNS: `CNAME nocargo → codigo-publico-brasil.github.io`.
4. Google Search Console e Bing Webmaster: verificar o domínio (registro TXT no DNS) e enviar `sitemap.xml`.

## Como o site é achado

- Buscadores: `<title>`, descrição, canônico, Open Graph, JSON-LD (WebSite, Person, BreadcrumbList), `sitemap.xml`.
- Agentes de IA: `robots.txt` aceita os rastreadores conhecidos (é um pedido, não uma trava); `llms.txt` resume o site; as páginas são HTML puro, legível sem JavaScript.

## Correções

Pelo formulário de issue (`.github/ISSUE_TEMPLATE/correcao.yml`); cada página traz um link que já preenche página e assunto.

## Acessos

O GitHub Pages não tem log de acesso. Hoje: Search Console (impressões, cliques, indexação), sem script no site. Contador de visitas exigiria um script de outro domínio, contra a regra de não coletar dado de quem visita; só com ADR.
