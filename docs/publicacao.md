# Publicação na Cloudflare

O site é estático e gerado a partir do datalake público (ver [ADR 0002](adr/0002-dados-e-fotos-do-datalake.md)), então o deploy é: gerar `dist/` e enviá-lo à Cloudflare por upload direto, com o `wrangler`. Ele vai como um Worker só com assets estáticos (`wrangler.jsonc`), que é o caminho atual da Cloudflare para sites estáticos; o Pages legado não é usado.

## Publicar

Com internet, a `main` atualizada, Node (para o `npx`) e as variáveis `CLOUDFLARE_ACCOUNT_ID` e `CLOUDFLARE_API_TOKEN` no `.env` (modelo em `.env.example`):

```bash
scripts/publicar.sh              # gera dist/ e envia
scripts/publicar.sh --sem-push   # só gera dist/, sem enviar
```

O script recusa publicar fora da `main`. A Cloudflare guarda as versões e permite voltar a uma anterior no painel. Para conferir antes de publicar: gere `dist/` e rode `npx wrangler versions upload`, que dá um endereço de prévia sem alterar a produção.
Para testar em outro endereço: `NO_CARGO_URL=https://exemplo.org uv run no-cargo`.

## Uma vez só

1. **ID da conta.** No painel, em Workers & Pages, lateral direita (Account ID). Vai em `CLOUDFLARE_ACCOUNT_ID`.
2. **Token.** Profile → API Tokens → Create Token → Custom token, com a permissão Account → Workers Scripts → Edit, restrita à sua conta. Vai em `CLOUDFLARE_API_TOKEN`. Guarde só no `.env` (fora do git).
3. **Primeiro deploy.** Preencha o `.env` e rode `scripts/publicar.sh`. O Worker se chama `nocargo` (campo `name` do `wrangler.jsonc`); abra o endereço `nocargo.<sua-conta>.workers.dev` para conferir a página inicial, uma ficha e a 404.
4. **Domínio.** No Worker, Settings → Domains & Routes → Add → Custom domain → `nocargo.codigopublicobrasil.com.br`. No provedor de DNS, troque o `CNAME no_cargo` de `codigo-publico-brasil.github.io` pelo que a Cloudflare indicar (ou deixe a Cloudflare criar o registro, se o DNS estiver nela) e espere o certificado.
5. **Desligar o antigo.** Só com o passo 4 funcionando: desative o GitHub Pages do repositório (Settings → Pages) e apague a branch `gh-pages`.
6. **Sem registro de acessos.** O `wrangler.jsonc` já desliga a observabilidade do Worker. Confira no painel que Web Analytics e Logs estão desligados (eles registram visitas ou injetam script).

Falta: Google Search Console e Bing Webmaster (verificar o domínio com um registro TXT no DNS e enviar `sitemap.xml`).

## Como o site é achado

- Buscadores: `<title>`, descrição, canônico, Open Graph, JSON-LD (WebSite, Person, BreadcrumbList), `sitemap.xml`.
- Agentes de IA: `robots.txt` aceita os rastreadores conhecidos (é um pedido, não uma trava); `llms.txt` resume o site; as páginas são HTML puro, legível sem JavaScript.

## Correções

Pelo formulário de issue (`.github/ISSUE_TEMPLATE/correcao.yml`); cada página traz um link que já preenche página e assunto.

## Acessos

Hoje: Search Console (impressões, cliques, indexação), sem script no site. Mantenha o Web Analytics e os logs da Cloudflare desligados no Worker: ele injeta um script nas páginas, contra a regra de não coletar dado de quem visita. Contador de visitas só com ADR.
