#!/usr/bin/env bash
# Gera o site e publica em gh-pages, em cima do histórico que já existe (sem push forçado).
# Uso: scripts/publicar.sh            gera, commita e envia
#      scripts/publicar.sh --sem-push gera e commita num clone temporário, sem enviar (para conferir)
set -euo pipefail

REPO="https://github.com/codigo-publico-brasil/no-cargo.git"
raiz="$(cd "$(dirname "$0")/.." && pwd)"
cd "$raiz"

branch="$(git rev-parse --abbrev-ref HEAD)"
if [ "$branch" != "main" ] && [ "${1:-}" != "--sem-push" ]; then
  echo "Publique a partir da main (agora: $branch). Use --sem-push só para conferir." >&2
  exit 1
fi
commit="$(git rev-parse --short HEAD)"

rm -rf dist                                       # sem páginas e fotos de builds anteriores
uv run no-cargo                                   # escreve dist/ a partir do warehouse
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
git clone --quiet --branch gh-pages --single-branch "$REPO" "$tmp/site"
find "$tmp/site" -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
(cd dist && tar --exclude=.git -cf - .) | tar -xf - -C "$tmp/site"  # sem o .git que o dist possa ter
cd "$tmp/site"
git add -A
if git diff --cached --quiet; then
  echo "Nada mudou: o site publicado já é este."
  exit 0
fi
git commit --quiet -m "Publica o site" -m "Gerado com uv run no-cargo a partir da $branch ($commit)."
if [ "${1:-}" = "--sem-push" ]; then
  echo "Commit pronto em $tmp/site (não enviado)."
  git --no-pager log --stat --oneline -1 | tail -3
  exit 0
fi
git push --quiet origin gh-pages
echo "Publicado: https://nocargo.codigopublicobrasil.com.br ($commit)"
