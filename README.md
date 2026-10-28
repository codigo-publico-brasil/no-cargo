# No Cargo

**Quem ocupa o poder no Brasil, pelos três poderes, com a fonte oficial ao lado.**

Aplicação do projeto [Código Público Brasil](https://github.com/codigo-publico-brasil). Gera um **site estático** a partir do esquema `marts` da [plataforma de dados](https://github.com/codigo-publico-brasil/dado-publico-brasil), sem servidor próprio, para publicar em qualquer hospedagem de arquivos (GitHub Pages, Cloudflare Pages ou um servidor comum).

## O que mostra hoje

- **Brasil:** os três poderes (Executivo, Legislativo e Judiciário), cada um em federal, estadual e municipal, com a composição por partido de cada casa em uma barra de 100%.
- **Estado:** os mesmos três poderes dentro de um estado, com lista de deputados que filtra, ordena e busca.
- **Ficha** de cada eleito: tempo no cargo, linha do tempo de mandatos e candidaturas, e totais da campanha, com selo de novato, reeleito ou retorno.
- **Entenda os cargos** e **Como calculamos**.
- Prefeitos, vereadores e Judiciário aparecem como **Em construção** (ver issues).

## Linhas vermelhas (valem em todas as fases)

1. **Sem ranking, nota ou lista ordenada de políticos** por medida avaliativa. A barra de partidos vai do maior para o menor número de cadeiras porque é a concentração, e as cores só separam os grupos.
2. **Sem recomendação de voto.**
3. **Sem adjetivos.** O texto descreve o que a fonte oficial registra.
4. **Mesmo modelo de página para todos os partidos.**
5. **Sem páginas sobre pessoas privadas.**
6. Todo dado exibido mostra fonte oficial e data de captura. Faltou: `Sem dado`, nunca zero.

## Como executar

Requisitos: Python 3.13 e [uv](https://docs.astral.sh/uv/). Com os dados já carregados pela plataforma (e a plataforma parada, porque o DuckDB aceita um escritor por vez):

```bash
uv sync
uv run no-cargo            # escreve o site em dist/
```

O arquivo do warehouse vem de `NO_CARGO_WAREHOUSE` (padrão: `../dado-publico-brasil/data_store/warehouse.duckdb`; modelo em `.env.example`). Abra `dist/index.html` no navegador.

As fotos oficiais do TSE vêm de `NO_CARGO_FOTOS` (padrão: `../dado-publico-brasil/data_store/fotos`, no formato `<ano>/<UF>/<sequencial>.jpg`). O site copia para `dist/fotos/` só a foto de cada eleito do ano e serve do próprio domínio; sem a pasta, gera sem elas.

Antes de abrir um PR:

```bash
uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest
```

## Publicar

Ver [docs/publicacao.md](docs/publicacao.md).

## Como é feito

- `src/no_cargo/dados.py`: consultas ao esquema `marts` (somente leitura).
- `src/no_cargo/paginas.py` e `textos.py`: as páginas, como texto HTML, sem motor de templates.
- `src/no_cargo/seo.py`: canônico, compartilhamento, dados estruturados, robots, sitemap e llms.txt.
- `src/no_cargo/static/`: `style.css` (mobile primeiro) e `app.js` (filtro e ordem das listas).
- `tests/`: um warehouse pequeno, inventado, com o esquema `marts`.

## Licenças

- **Código:** AGPL-3.0 (arquivo `LICENSE`).
- **Dados curados que o site mostra:** CC BY 4.0. Cada dado vem de uma fonte oficial (TSE, Câmara dos Deputados, Senado Federal), que mantém as próprias condições de uso; o site sempre mostra a origem e a data de captura. Cite a fonte ao reutilizar.
- **Fontes tipográficas** em `src/no_cargo/static/fonts/`: SIL Open Font License 1.1, com os avisos em `LICENSES.md` na mesma pasta.
