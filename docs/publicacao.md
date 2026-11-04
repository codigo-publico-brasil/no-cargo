# Publicação no Cloudflare Pages

O site é estático e gerado a partir do datalake público (ver [ADR 0002](adr/0002-dados-e-fotos-do-datalake.md)), então o deploy é: gerar `dist/` e enviar a pasta ao Cloudflare Pages por upload direto, com o `wrangler`.

## Publicar

Com internet, a `main` atualizada, Node (para o `npx`) e as variáveis `CF_PAGES_PROJETO`, `CLOUDFLARE_ACCOUNT_ID` e `CLOUDFLARE_API_TOKEN` no `.env` (modelo em `.env.example`):

```bash
scripts/publicar.sh              # gera dist/ e envia ao Cloudflare Pages
scripts/publicar.sh --sem-push   # só gera dist/, sem enviar
```

O script recusa publicar fora da `main`. O Cloudflare guarda o histórico de deploys e permite voltar a um anterior no painel.
Para testar em outro endereço: `NO_CARGO_URL=https://exemplo.org uv run no-cargo`.

## Uma vez só

1. **Projeto.** Com uma conta na Cloudflare, rode `npx wrangler login` e depois `npx wrangler pages project create <nome> --production-branch main`. O `<nome>` vira `CF_PAGES_PROJETO` e o endereço `<nome>.pages.dev`. (Pelo painel: Workers & Pages → Create → Pages → Upload assets.)
2. **ID da conta.** No painel, em Workers & Pages, lateral direita (Account ID). Vai em `CLOUDFLARE_ACCOUNT_ID`.
3. **Token.** My Profile → API Tokens → Create Token → Custom token, com a permissão Account → Cloudflare Pages → Edit, restrita à sua conta. Vai em `CLOUDFLARE_API_TOKEN`. Guarde só no `.env` (fora do git).
4. **Primeiro deploy.** Preencha o `.env`, rode `scripts/publicar.sh` e abra `<nome>.pages.dev` para conferir a página inicial, uma ficha e a 404.
5. **Domínio.** No projeto, Custom domains → Set up a domain → `nocargo.codigopublicobrasil.com.br`. No provedor de DNS, troque o `CNAME no_cargo` de `codigo-publico-brasil.github.io` para `<nome>.pages.dev` e espere o certificado ficar ativo.
6. **Desligar o antigo.** Só com o passo 5 funcionando: desative o GitHub Pages do repositório (Settings → Pages) e apague a branch `gh-pages`.
7. **Web Analytics.** Confira que está desligado no projeto (ele injeta script nas páginas).

Falta: Google Search Console e Bing Webmaster (verificar o domínio com um registro TXT no DNS e enviar `sitemap.xml`).

## Como o site é achado

- Buscadores: `<title>`, descrição, canônico, Open Graph, JSON-LD (WebSite, Person, BreadcrumbList), `sitemap.xml`.
- Agentes de IA: `robots.txt` aceita os rastreadores conhecidos (é um pedido, não uma trava); `llms.txt` resume o site; as páginas são HTML puro, legível sem JavaScript.

## Correções

Pelo formulário de issue (`.github/ISSUE_TEMPLATE/correcao.yml`); cada página traz um link que já preenche página e assunto.

## Acessos

Hoje: Search Console (impressões, cliques, indexação), sem script no site. Mantenha o Web Analytics da Cloudflare desligado no projeto: ele injeta um script nas páginas, contra a regra de não coletar dado de quem visita. Contador de visitas só com ADR.
