"""Gera o site estático.

Uso:
    uv run no-cargo                                   # escreve em dist/
    uv run no-cargo --datalake https://exemplo.org --saida dist

Os dados vêm do catálogo público do datalake (anexado em modo somente leitura); nada é lido de disco.
As fotos não são copiadas: as páginas apontam para o arquivo no datalake.
"""

import argparse
import os
import shutil
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from no_cargo import cartoes, dados, paginas, seo, textos
from no_cargo.formato import arquivo_da_ficha

ENV_DATALAKE = "NO_CARGO_DATALAKE"
ESTATICOS = Path(__file__).parent / "static"


def escrever(caminho: Path, texto: str) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(texto, encoding="utf-8")


def apontar_fotos(pessoas: list[dados.Row], datalake: str | None) -> None:
    """Marca cada linha com o endereço da foto oficial (TSE) no datalake, do ano da eleição da pessoa.
    Sem datalake ou sem caminho informado, sem foto do TSE."""
    for r in pessoas:
        if datalake and r.get("foto_caminho"):
            r["foto_local"] = f"{datalake}/{r['foto_caminho']}"


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
    datalake: str | None = None,
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
    apontar_fotos([*eleitos, *atuais], datalake)
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
    with ThreadPoolExecutor(max_workers=16) as pool:  # as fotos vêm do datalake: baixar em paralelo
        fotos = pool.map(lambda r: cartoes.baixar(r["foto_local"]) if r.get("foto_local") else None, pessoas)
        for r, foto in zip(pessoas, fotos, strict=True):
            linhas, etiqueta = paginas.texto_do_cartao_da_pessoa(r)
            cartoes.cartao(str(r["nome_urna"]), linhas, etiqueta, saida / paginas.imagem_da_pessoa(r), foto)
    for uf, (nome, _) in paginas.UFS.items():
        cartoes.cartao(
            nome,
            ["Quem ocupa os cargos hoje", f"e quem assume em {ano + 1}"],
            f"Estado · {uf}",
            saida / paginas.imagem_do_estado(uf),
        )
    quantas = Counter(r["cargo"] for r in eleitos)
    escrever(saida / "404.html", paginas.nao_encontrada())
    escrever(saida / "robots.txt", seo.robots())
    escrever(saida / "sitemap.xml", seo.sitemap([(c, capturado) for c in escritas]))
    escrever(saida / "llms.txt", seo.llms(ano, capturado, dict(quantas)))
    return total


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera o site No Cargo a partir do datalake público.")
    parser.add_argument(
        "--datalake", default=os.environ.get(ENV_DATALAKE) or dados.DATALAKE, help="endereço base do datalake"
    )
    parser.add_argument("--saida", type=Path, default=Path("dist"))
    args = parser.parse_args()
    con = dados.conectar(args.datalake)
    try:
        total = construir(con, args.saida, datalake=args.datalake)
    finally:
        con.close()
    print(f"{total} páginas em {args.saida}")
