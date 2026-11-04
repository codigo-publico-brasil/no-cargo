#!/usr/bin/env bash
# Gera o site e publica no Cloudflare Pages por upload direto (wrangler).
# Uso: scripts/publicar.sh            gera e envia
#      scripts/publicar.sh --sem-push só gera dist/, sem enviar (para conferir)
# Lê CF_PAGES_PROJETO, CLOUDFLARE_ACCOUNT_ID e CLOUDFLARE_API_TOKEN do .env (modelo em .env.example).
set -euo pipefail

raiz="$(cd "$(dirname "$0")/.." && pwd)"
cd "$raiz"

branch="$(git rev-parse --abbrev-ref HEAD)"
if [ "$branch" != "main" ] && [ "${1:-}" != "--sem-push" ]; then
  echo "Publique a partir da main (agora: $branch). Use --sem-push só para conferir." >&2
  exit 1
fi
commit="$(git rev-parse --short HEAD)"

rm -rf dist                                       # sem páginas e fotos de builds anteriores
uv run no-cargo                                   # escreve dist/ a partir do datalake
if [ "${1:-}" = "--sem-push" ]; then
  echo "Site gerado em dist/ (não enviado)."
  exit 0
fi

if [ -f .env ]; then
  set -a
  . ./.env
  set +a
fi
: "${CF_PAGES_PROJETO:?Defina CF_PAGES_PROJETO no .env}"
: "${CLOUDFLARE_ACCOUNT_ID:?Defina CLOUDFLARE_ACCOUNT_ID no .env}"
: "${CLOUDFLARE_API_TOKEN:?Defina CLOUDFLARE_API_TOKEN no .env}"
export CLOUDFLARE_ACCOUNT_ID CLOUDFLARE_API_TOKEN

npx --yes wrangler pages deploy dist --project-name "$CF_PAGES_PROJETO" --branch main \
  --commit-hash "$(git rev-parse HEAD)" --commit-message "Publica o site ($branch $commit)"
echo "Publicado: https://nocargo.codigopublicobrasil.com.br ($commit)"
