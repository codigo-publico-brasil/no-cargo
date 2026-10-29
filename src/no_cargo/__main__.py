"""Gera o site estático.

Uso (depois de rodar a plataforma de dados):
    uv run no-cargo                                   # escreve em dist/
    uv run no-cargo --warehouse caminho/warehouse.duckdb --saida dist

O warehouse é aberto em modo somente leitura. Um arquivo DuckDB aceita um escritor por vez: com a plataforma
carregando dados, a geração falha até ela terminar.
"""

import argparse
import os
import shutil
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import duckdb

from no_cargo import dados, paginas, seo, textos
from no_cargo.formato import arquivo_da_ficha

ENV_WAREHOUSE = "NO_CARGO_WAREHOUSE"
DEFAULT_WAREHOUSE = "../dado-publico-brasil/data_store/warehouse.duckdb"
ENV_FOTOS = "NO_CARGO_FOTOS"
DEFAULT_FOTOS = "../dado-publico-brasil/data_store/fotos"  # <ano>/<UF>/<sequencial>.jpg, como o TSE publica
ESTATICOS = Path(__file__).parent / "static"


def escrever(caminho: Path, texto: str) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(texto, encoding="utf-8")


def trazer_fotos(pessoas: list[dados.Row], origem: Path | None, saida: Path) -> int:
    """Copia para o site a foto oficial (TSE) de cada pessoa, do ano da eleição dela, e marca a linha com o
    caminho: as fotos são servidas pelo próprio site, nunca de outro domínio. Sem arquivo, sem foto local."""
    if origem is None:
        return 0
    trazidas = 0
    for r in pessoas:
        caminho = r.get("foto_caminho")
        arquivo = origem / str(caminho) if caminho and (origem / str(caminho)).is_file() else None
        if arquivo:
            destino = Path("fotos") / str(caminho)
            (saida / destino).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(arquivo, saida / destino)
            r["foto_local"] = destino.as_posix()
            trazidas += 1
    return trazidas


def ligar_as_fichas(pessoas: list[dados.Row], visoes: dict[str, list[dados.Row]], ano: int) -> None:
    """Cada pessoa tem uma ficha só: quem foi reeleito usa a da eleição nova. Marca as linhas de cada
    composição com a ficha, a foto local e se é eleito do ano (os cartões usam isso)."""
    por_pessoa = {r["id_pessoa"]: r for r in pessoas if r["id_pessoa"]}
    for linhas in visoes.values():
        for r in linhas:
            dona = por_pessoa.get(r["id_pessoa"])
            if dona is None:
                continue
            r["ficha"] = arquivo_da_ficha(dona["nome_urna"], dona["id_candidatura"])
            r["foto_local"] = dona.get("foto_local")
            r["novo"] = dona["ano_eleicao"] == ano
    for r in pessoas:
        r["novo"] = r["ano_eleicao"] == ano


def construir(
    con: dados.Connection,
    saida: Path,
    hoje: date | None = None,
    fotos: Path | None = None,
    agora: datetime | None = None,
) -> int:
    """Escreve o site em `saida` e devolve quantas páginas gerou."""
    agora = agora or datetime.now(timezone(timedelta(hours=-3)))  # horário de Brasília, sem horário de verão
    hoje = hoje or agora.date()
    ano = dados.ultimo_ano(con)
    eleitos = dados.eleitos(con, ano)
    atuais = dados.em_exercicio(con, hoje, eleitos)
    hoje_linhas = dados.ocupantes(con, hoje)
    posse_linhas = dados.na_posse(con, hoje, eleitos)
    situacao = dados.situacao_dos_cargos(con, ano)
    capturado = max((r["dt_captura"] for r in situacao if r["dt_captura"]), default=None)
    saida.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ESTATICOS, saida, dirs_exist_ok=True)  # css, js, símbolo e fontes (arquivos binários)
    trazer_fotos([*eleitos, *atuais], fotos, saida)
    visoes = {"hoje": hoje_linhas, "posse": posse_linhas}
    ligar_as_fichas([*eleitos, *atuais], visoes, ano)
    escritas: list[str] = [
        "index.html",
        "pessoas.html",
        "estados.html",
        "cargos.html",
        "como-calculamos.html",
    ]
    escrever(saida / "index.html", paginas.brasil(ano, visoes, situacao, capturado, agora))
    escrever(
        saida / "pessoas.html",
        paginas.pessoas(ano, eleitos, capturado, atuais, dados.ids_em_mandato(con, hoje)),
    )
    escrever(saida / "estados.html", paginas.estados(capturado))
    escrever(saida / "cargos.html", textos.cargos())
    escrever(saida / "como-calculamos.html", textos.como_calculamos())
    total = 5
    for uf in paginas.UFS:
        escrever(saida / "estado" / f"{uf}.html", paginas.estado(uf, ano, visoes, capturado))
        escritas.append(f"estado/{uf}.html")
        total += 1
    pessoas = [*eleitos, *atuais]
    ids = [r["id_pessoa"] for r in pessoas if r["id_pessoa"]]
    ocupacoes_de = dados.ocupacoes_das_pessoas(con, ids)
    candidaturas_de = dados.candidaturas_das_pessoas(con, ids)
    for r in pessoas:
        ocupacoes = ocupacoes_de.get(r["id_pessoa"], [])
        candidaturas = candidaturas_de.get(r["id_pessoa"], [])
        desde = dados.ininterrupto_desde(
            [
                {"dt_inicio": o["dt_inicio"], "dt_fim": o["dt_fim_prevista"]}
                for o in ocupacoes
                if o["dt_inicio"] and o["dt_inicio"] <= hoje
            ],
            hoje,
        )
        arquivo = arquivo_da_ficha(r["nome_urna"], r["id_candidatura"])
        escrever(saida / "pessoa" / arquivo, paginas.ficha(r, hoje, ocupacoes, candidaturas, desde))
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
    parser.add_argument(
        "--fotos",
        type=Path,
        default=Path(os.environ.get(ENV_FOTOS, DEFAULT_FOTOS)),
        help="pasta das fotos do TSE",
    )
    args = parser.parse_args()
    con = duckdb.connect(str(args.warehouse), read_only=True)
    try:
        total = construir(con, args.saida, fotos=args.fotos if args.fotos.is_dir() else None)
    finally:
        con.close()
    print(f"{total} páginas em {args.saida}")


if __name__ == "__main__":
    main()
