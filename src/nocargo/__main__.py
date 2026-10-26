"""Gera o site estático.

Uso (depois de rodar a plataforma de dados):
    uv run nocargo                                   # escreve em dist/
    uv run nocargo --warehouse caminho/warehouse.duckdb --saida dist

O warehouse é aberto em modo somente leitura. Um arquivo DuckDB aceita um escritor por vez: com a plataforma
carregando dados, a geração falha até ela terminar.
"""

import argparse
import os
import shutil
from collections import Counter
from datetime import date
from pathlib import Path

import duckdb

from nocargo import dados, paginas, seo, textos
from nocargo.formato import arquivo_da_ficha

ENV_WAREHOUSE = "NOCARGO_WAREHOUSE"
DEFAULT_WAREHOUSE = "../dado-publico-brasil/data_store/warehouse.duckdb"
ESTATICOS = Path(__file__).parent / "static"


def escrever(caminho: Path, texto: str) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(texto, encoding="utf-8")


def construir(con: dados.Connection, saida: Path, hoje: date | None = None) -> int:
    """Escreve o site em `saida` e devolve quantas páginas gerou."""
    hoje = hoje or date.today()
    ano = dados.ultimo_ano(con)
    eleitos = dados.eleitos(con, ano)
    situacao = dados.situacao_dos_cargos(con, ano)
    capturado = max((r["dt_captura"] for r in situacao if r["dt_captura"]), default=None)
    saida.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ESTATICOS, saida, dirs_exist_ok=True)  # css, js, símbolo e fontes (arquivos binários)
    escritas: list[str] = ["index.html", "pessoas.html", "cargos.html", "como-calculamos.html"]
    escrever(saida / "index.html", paginas.brasil(ano, eleitos, situacao, capturado))
    escrever(saida / "pessoas.html", paginas.pessoas(ano, eleitos, capturado))
    escrever(saida / "cargos.html", textos.cargos())
    escrever(saida / "como-calculamos.html", textos.como_calculamos())
    total = 4
    for uf in paginas.UFS:
        escrever(saida / "estado" / f"{uf}.html", paginas.estado(uf, ano, eleitos, situacao, capturado))
        escritas.append(f"estado/{uf}.html")
        total += 1
    for r in eleitos:
        mandatos = dados.mandatos(con, r["id_pessoa"]) if r["id_pessoa"] else []
        candidaturas = dados.candidaturas(con, r["id_pessoa"]) if r["id_pessoa"] else []
        vistas = {(c["ano_eleicao"], c["cargo"]) for c in candidaturas}
        candidaturas += [
            h
            for h in dados.historico(con, r["id_candidatura"])
            if (h["ano_eleicao"], h["cargo"]) not in vistas
        ]
        desde = dados.ininterrupto_desde(mandatos, hoje)
        arquivo = arquivo_da_ficha(r["nome_urna"], r["id_candidatura"])
        escrever(saida / "pessoa" / arquivo, paginas.ficha(r, hoje, mandatos, candidaturas, desde))
        escritas.append(f"pessoa/{arquivo}")
        total += 1
    quantas = Counter(r["cargo"] for r in eleitos)
    escrever(saida / "404.html", paginas.nao_encontrada())
    escrever(saida / "robots.txt", seo.robots())
    escrever(saida / "sitemap.xml", seo.sitemap([(c, capturado) for c in escritas]))
    escrever(saida / "llms.txt", seo.llms(ano, capturado, dict(quantas)))
    escrever(saida / "CNAME", seo.SITE.removeprefix("https://") + "\n")  # domínio próprio no GitHub Pages
    escrever(saida / ".nojekyll", "")  # o Pages não passa o site pelo Jekyll
    return total


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera o site No Cargo a partir do warehouse da plataforma.")
    parser.add_argument(
        "--warehouse", type=Path, default=Path(os.environ.get(ENV_WAREHOUSE, DEFAULT_WAREHOUSE))
    )
    parser.add_argument("--saida", type=Path, default=Path("dist"))
    args = parser.parse_args()
    con = duckdb.connect(str(args.warehouse), read_only=True)
    try:
        total = construir(con, args.saida)
    finally:
        con.close()
    print(f"{total} páginas em {args.saida}")


if __name__ == "__main__":
    main()
