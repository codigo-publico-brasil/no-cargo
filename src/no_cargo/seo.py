"""O que faz o site ser achado: endereço canônico, cartões de compartilhamento, dados estruturados, robots.txt,
sitemap.xml e llms.txt. Nada aqui carrega recurso de outro site nem coleta dado de quem visita."""

import json
import os
from datetime import date
from html import escape
from urllib.parse import quote

SITE = os.environ.get("NO_CARGO_URL", "https://nocargo.codigopublicobrasil.com.br").rstrip("/")
SITE_MAE = "https://codigo-publico-brasil.github.io"
REPO = "https://github.com/codigo-publico-brasil/no-cargo"
NOME = "No Cargo"

# Rastreadores de IA que o site aceita de propósito. O robots.txt é um pedido, não uma trava.
AGENTES_DE_IA = (
    "GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "Claude-User", "PerplexityBot",
    "Perplexity-User", "Google-Extended", "Applebot-Extended", "CCBot", "Amazonbot", "Meta-ExternalAgent",
)  # fmt: skip


def url(caminho: str) -> str:
    """Endereço completo de uma página; a inicial é a raiz do domínio."""
    return f"{SITE}/" + ("" if caminho in ("", "index.html") else caminho)


def link_de_correcao(titulo: str, caminho: str) -> str:
    """Abre uma issue de correção já com a página e o assunto preenchidos (o canal de correção do site)."""
    return f"{REPO}/issues/new?template=correcao.yml&title={quote('Correção: ' + titulo)}&pagina={quote(url(caminho), safe='')}"


def _json(dado: object) -> str:
    return json.dumps(dado, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def cabecalho(
    titulo: str, descricao: str, caminho: str, schema: list[dict[str, object]] | None = None
) -> str:
    """Tags do <head> que ajudam buscadores e agentes: canônico, Open Graph, Twitter e dados estruturados."""
    pagina = url(caminho)
    completo = f"{titulo} | {NOME}"
    tags = [
        f'<link rel="canonical" href="{escape(pagina)}">',
        '<meta name="robots" content="index, follow, max-image-preview:large">',
        '<meta property="og:type" content="website"><meta property="og:locale" content="pt_BR">',
        f'<meta property="og:site_name" content="{NOME}">',
        f'<meta property="og:title" content="{escape(completo)}">',
        f'<meta property="og:description" content="{escape(descricao)}">',
        f'<meta property="og:url" content="{escape(pagina)}">',
        f'<meta property="og:image" content="{SITE}/og.png"><meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        f'<meta property="og:image:alt" content="{NOME}: quem ocupa o poder no Brasil, com a fonte oficial ao lado">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{escape(completo)}">',
        f'<meta name="twitter:description" content="{escape(descricao)}">',
        f'<meta name="twitter:image" content="{SITE}/og.png">',
    ]
    if schema:
        tags.append(
            f'<script type="application/ld+json">{_json({"@context": "https://schema.org", "@graph": schema})}</script>'
        )
    return "\n".join(tags) + "\n"


def site_schema() -> dict[str, object]:
    return {
        "@type": "WebSite",
        "@id": f"{SITE}/#site",
        "name": NOME,
        "url": SITE + "/",
        "inLanguage": "pt-BR",
        "description": "Quem ocupa o poder no Brasil, pelos três poderes, com a fonte oficial ao lado.",
        "publisher": {"@type": "Organization", "name": "Código Público Brasil", "url": SITE_MAE},
    }


def migalhas(itens: list[tuple[str, str]]) -> dict[str, object]:
    """Trilha de navegação (Brasil, estado, pessoa); cada item é (nome, caminho)."""
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i, "name": nome, "item": url(caminho)}
            for i, (nome, caminho) in enumerate(itens, 1)
        ],
    }


def pessoa_schema(
    nome: str,
    cargo: str,
    partido: str | None,
    estado: str,
    caminho: str,
    fonte_url: str,
    atualizado: date | None,
) -> dict[str, object]:
    """Só o que a ficha mostra e a fonte publica: nome, cargo, partido e estado. Nada de data de nascimento ou contato."""
    dado: dict[str, object] = {
        "@type": "Person",
        "@id": url(caminho) + "#pessoa",
        "name": nome,
        "jobTitle": cargo,
        "workLocation": {"@type": "AdministrativeArea", "name": estado},
        "url": url(caminho),
        "subjectOf": {"@type": "WebPage", "url": fonte_url, "name": "TSE, candidaturas"},
    }
    if partido:
        dado["memberOf"] = {"@type": "Organization", "name": partido}
    if atualizado:
        dado["dateModified"] = atualizado.isoformat()
    return dado


def robots() -> str:
    linhas = [
        "# Todos os rastreadores são bem-vindos: o site é público e feito para ser achado, inclusive por agentes de IA."
    ]
    linhas += ["User-agent: *", "Allow: /", ""]
    linhas += [f"User-agent: {a}\nAllow: /\n" for a in AGENTES_DE_IA]
    linhas += [f"Sitemap: {SITE}/sitemap.xml", ""]
    return "\n".join(linhas)


def sitemap(paginas: list[tuple[str, date | None]]) -> str:
    itens = "".join(
        f"<url><loc>{escape(url(caminho))}</loc>"
        + (f"<lastmod>{ultima.isoformat()}</lastmod>" if ultima else "")
        + "</url>"
        for caminho, ultima in paginas
    )
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{itens}</urlset>\n'


def llms(ano: int, atualizado: date | None, quantas: dict[str, int]) -> str:
    """Resumo em texto simples para agentes de IA (convenção llms.txt): o que o site é, onde está cada coisa e de onde vêm os dados."""
    total = sum(quantas.values())
    detalhe = ", ".join(f"{n} {cargo.lower()}" for cargo, n in quantas.items())
    return f"""# {NOME}

> {NOME} mostra quem ocupa o poder no Brasil, pelos três poderes (Executivo, Legislativo e Judiciário) e pelas esferas federal, estadual e municipal, com a fonte oficial e a data de captura ao lado de cada dado. Hoje cobre as {total} pessoas eleitas nas eleições gerais de {ano} ({detalhe}). Prefeitos, vereadores e o Judiciário estão em construção.

Dados atualizados em {atualizado.strftime("%d/%m/%Y") if atualizado else "data não informada"}. O resultado de {ano} é provisório até a diplomação. Não há ranking, nota nem recomendação de voto; todas as pessoas seguem o mesmo modelo de página.

## Onde está cada coisa
- [Início]({SITE}/): composição de cada casa por partido (Câmara, Senado, Assembleias, governos).
- [Todas as pessoas]({SITE}/pessoas.html): lista de todos os eleitos, com busca e filtros.
- [Entenda os cargos]({SITE}/cargos.html): o que cada cargo faz, em palavras simples.
- [Como calculamos]({SITE}/como-calculamos.html): de onde vêm os dados, como as pessoas são ligadas entre eleições e o que não sabemos.
- Páginas por estado: `{SITE}/estado/SP.html` (sigla da UF).
- Páginas por pessoa: `{SITE}/pessoa/<nome>-<ano>-<uf>-<sequencial>.html`, listadas em [sitemap.xml]({SITE}/sitemap.xml).

## Fontes oficiais
- Tribunal Superior Eleitoral (TSE), dados abertos: candidaturas, resultados, bens e prestação de contas.
- Câmara dos Deputados e Senado Federal, dados abertos: mandatos, votações e fotos.

## Como citar
Cite a página e a data de captura. Cada página tem endereço permanente e o texto "Fonte" com o link oficial. Para corrigir um dado, abra uma issue: {REPO}/issues/new?template=correcao.yml

Código e dados curados: {REPO}. Um projeto do Código Público Brasil: {SITE_MAE}
"""
