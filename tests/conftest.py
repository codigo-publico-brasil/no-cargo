"""Um warehouse pequeno, só com as tabelas do esquema `marts` que o site lê, com dados inventados."""

from collections.abc import Callable, Iterator
from datetime import date

import duckdb
import pytest

TABELAS = (
    """CREATE TABLE marts.fct_candidaturas (
        id_candidatura varchar, id_disputa varchar, nome varchar, nome_urna varchar, ocupacao varchar,
        partido varchar, id_pessoa bigint, foto_caminho varchar, resultado varchar, fl_eleito boolean
    )""",
    """CREATE TABLE marts.fct_resultados (
        id_candidatura varchar, turno integer, qtd_votos_nominais bigint, percentual_votos_validos decimal(5, 2)
    )""",
    """CREATE TABLE marts.fct_cargos_ocupacoes (
        id_ocupacao varchar, id_pessoa bigint, id_cargo varchar, id_territorio varchar, id_partido integer,
        id_candidatura varchar, ano_inicio integer, dt_inicio date, dt_fim date, id_captura bigint, dt_captura date
    )""",
    """CREATE TABLE marts.fct_mandatos (id_candidatura varchar, tipo_mandato varchar)""",
    """CREATE TABLE marts.fct_campanhas (
        id_candidatura varchar, valor_bens decimal(18, 2), valor_receitas decimal(18, 2),
        valor_despesas decimal(18, 2), id_captura_bens bigint, id_captura_receitas bigint,
        id_captura_despesas bigint, dt_captura date
    )""",
    """CREATE TABLE metadata.capturas (id_captura bigint, url varchar)""",
    """CREATE TABLE marts.dim_pessoas (
        id_pessoa bigint, nome_civil varchar, fonte_nome_civil varchar, nome_publico varchar,
        dt_nascimento date, fonte_dt_nascimento varchar, uf_nascimento varchar, fonte_uf_nascimento varchar,
        profissoes varchar, fonte_profissoes varchar, foto_caminho varchar, id_captura_tse bigint,
        dt_captura_tse date
    )""",
    """CREATE TABLE marts.dim_partidos (id_partido integer, sigla varchar)""",
    """CREATE TABLE marts.dim_pessoas_cadastro (
        id_pessoa bigint, municipio_nascimento varchar, site_url varchar, rede_social_url varchar,
        foto_url varchar, fontes varchar, id_captura bigint, dt_captura date
    )""",
    """CREATE TABLE marts.dim_territorios (id_territorio varchar, tipo varchar, nome varchar, sigla varchar)""",
    """CREATE TABLE marts.dim_eleicoes (id_eleicao varchar, ano_eleicao integer)""",
    """CREATE TABLE marts.dim_cargos (id_cargo varchar, nome varchar)""",
    """CREATE TABLE marts.dim_disputas (
        id_disputa varchar, id_eleicao varchar, id_cargo varchar, ue varchar, qtd_vagas integer
    )""",
)

CAPTURA = date(2026, 10, 24)
URL = "https://dadosabertos.tse.jus.br/dataset/candidatos-2026"
CARGOS_DA_BASE = (
    ("presidente", "Presidente"),
    ("governador", "Governador"),
    ("senador", "Senador"),
    ("deputado_federal", "Deputado federal"),
    ("deputado_estadual", "Deputado estadual"),
    ("deputado_distrital", "Deputado distrital"),
    ("vereador", "Vereador"),
)
# vagas de 2026 por cargo e estado, para saber quem falta; as demais disputas têm uma vaga
VAGAS = {
    ("deputado_federal", "RJ"): 3,
    ("senador", "RJ"): 2,
    ("governador", "RJ"): 1,
    ("presidente", "BR"): 1,
    ("governador", "SP"): 1,
}

# id, uf, cargo, nome de urna, partido, votos, id_pessoa, tipo_mandato
PESSOAS_ELEITAS = [
    ("2026:RJ:1", "RJ", "Deputado federal", "Ana Exemplo", "Partido A", 142300, 10, "reeleito"),
    ("2026:RJ:2", "RJ", "Deputado federal", "Bruno Modelo", "Partido B", 98100, 500, None),
    ("2026:RJ:8", "RJ", "Deputado federal", "Nina Nova", "Partido B", 50500, 14, "novato"),
    ("2026:RJ:3", "RJ", "Deputado federal", "<b>Carla</b> Teste", "Partido C", 201500, 12, "retorno"),
    ("2026:RJ:4", "RJ", "Senador", "Paulo Exemplo", "Partido B", 3100000, 600, "novato"),
    ("2026:RJ:5", "RJ", "Governador", "Diego Amostra", "Partido A", 2400000, 700, None),
    ("2026:SP:6", "SP", "Deputado estadual", "Elisa Ficticia", "Partido D", 70500, 77, None),
    ("2026:DF:7", "DF", "Deputado distrital", "Fábio Exemplo", "Partido E", 12000, 800, None),
]


def id_do_cargo(con: duckdb.DuckDBPyConnection, nome: str) -> str:
    return str(con.execute("SELECT id_cargo FROM marts.dim_cargos WHERE nome = ?", (nome,)).fetchone()[0])


def id_do_partido(con: duckdb.DuckDBPyConnection, sigla: str) -> int:
    achado = con.execute("SELECT id_partido FROM marts.dim_partidos WHERE sigla = ?", (sigla,)).fetchone()
    if achado:
        return int(achado[0])
    novo = int(con.execute("SELECT count(*) + 1 FROM marts.dim_partidos").fetchone()[0])
    con.execute("INSERT INTO marts.dim_partidos VALUES (?, ?)", (novo, sigla))
    return novo


def garantir_pessoa(con: duckdb.DuckDBPyConnection, pessoa: int, nome: str) -> None:
    if not con.execute("SELECT 1 FROM marts.dim_pessoas WHERE id_pessoa = ?", (pessoa,)).fetchone():
        con.execute(
            "INSERT INTO marts.dim_pessoas VALUES (?, NULL, NULL, ?, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)",
            (pessoa, nome),
        )


def garantir_disputa(con: duckdb.DuckDBPyConnection, ano: int, id_cargo: str, uf: str) -> str:
    id_eleicao, id_disputa = f"{ano}-1", f"{ano}:{id_cargo}:{uf}"
    if not con.execute("SELECT 1 FROM marts.dim_eleicoes WHERE id_eleicao = ?", (id_eleicao,)).fetchone():
        con.execute("INSERT INTO marts.dim_eleicoes VALUES (?, ?)", (id_eleicao, ano))
    if not con.execute("SELECT 1 FROM marts.dim_disputas WHERE id_disputa = ?", (id_disputa,)).fetchone():
        vagas = VAGAS.get((id_cargo, uf), 1) if ano == 2026 else 1
        con.execute(
            "INSERT INTO marts.dim_disputas VALUES (?, ?, ?, ?, ?)",
            (id_disputa, id_eleicao, id_cargo, uf, vagas),
        )
    return id_disputa


def inserir(
    con: duckdb.DuckDBPyConnection,
    id_candidatura: str,
    uf: str,
    cargo: str,
    urna: str,
    partido: str,
    pessoa: int,
    resultado: str = "Eleito",
    votos: int = 1000,
    percentual: float = 10.5,
    com_mandato: bool = True,
    tipo: str | None = None,
) -> None:
    """Uma candidatura. Se eleita, ganha resultado, mandato na base (do ano seguinte por 4 anos, 8 para senador)
    e, sem data de posse, o que a base ainda não sabe (`com_mandato=False`: deputado estadual de 2026)."""
    ano = int(id_candidatura.split(":")[0])
    eleito = resultado.lower().startswith("eleito")
    foto = f"{ano}/{uf}/{id_candidatura.rsplit(':', 1)[-1]}.jpg"  # o caminho que a base informa
    id_cargo = id_do_cargo(con, cargo)
    garantir_pessoa(con, pessoa, urna)
    con.execute(
        "INSERT INTO marts.fct_candidaturas VALUES (?, ?, ?, ?, NULL, ?, ?, ?, ?, ?)",
        (
            id_candidatura,
            garantir_disputa(con, ano, id_cargo, uf),
            urna,
            urna,
            partido,
            pessoa,
            foto,
            resultado,
            eleito,
        ),
    )
    if eleito:
        con.execute(
            "INSERT INTO marts.fct_resultados VALUES (?, 1, ?, ?)", (id_candidatura, votos, percentual)
        )
        anos = 8 if cargo == "Senador" else 4
        inicio, fim = (date(ano + 1, 1, 1), date(ano + anos, 12, 31)) if com_mandato else (None, None)
        con.execute(
            "INSERT INTO marts.fct_cargos_ocupacoes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)",
            (
                id_candidatura,
                pessoa,
                id_cargo,
                uf,
                id_do_partido(con, partido),
                id_candidatura,
                ano + 1,
                inicio,
                fim,
                CAPTURA,
            ),
        )
        con.execute("INSERT INTO marts.fct_mandatos VALUES (?, ?)", (id_candidatura, tipo))


def exercer(
    con: duckdb.DuckDBPyConnection,
    pessoa: int,
    nome: str,
    cargo: str,
    uf: str,
    partido: str,
    ano: int,
    inicio: date,
    fim: date,
    url: str | None = None,
) -> None:
    """Um período no cargo informado pela casa, sem candidatura própria (sem `id_candidatura`)."""
    garantir_pessoa(con, pessoa, nome)
    captura = None
    if url:
        captura = 100 + int(con.execute("SELECT count(*) FROM metadata.capturas").fetchone()[0])
        con.execute("INSERT INTO metadata.capturas VALUES (?, ?)", (captura, url))
    con.execute(
        "INSERT INTO marts.fct_cargos_ocupacoes VALUES (?, ?, ?, ?, ?, NULL, ?, ?, ?, ?, ?)",
        (
            f"exercicio:{pessoa}:{ano}:{uf}",
            pessoa,
            id_do_cargo(con, cargo),
            uf,
            id_do_partido(con, partido),
            ano,
            inicio,
            fim,
            captura,
            CAPTURA,
        ),
    )


@pytest.fixture
def candidatura(warehouse: duckdb.DuckDBPyConnection) -> Callable[..., None]:
    return lambda *args, **kwargs: inserir(warehouse, *args, **kwargs)


@pytest.fixture
def exercicio(warehouse: duckdb.DuckDBPyConnection) -> Callable[..., None]:
    return lambda *args, **kwargs: exercer(warehouse, *args, **kwargs)


@pytest.fixture
def warehouse(tmp_path) -> Iterator[duckdb.DuckDBPyConnection]:
    con = duckdb.connect(str(tmp_path / "warehouse.duckdb"))
    con.execute("CREATE SCHEMA marts")
    con.execute("CREATE SCHEMA metadata")
    for ddl in TABELAS:
        con.execute(ddl)
    for id_cargo, nome in CARGOS_DA_BASE:
        con.execute("INSERT INTO marts.dim_cargos VALUES (?, ?)", (id_cargo, nome))
    con.execute("INSERT INTO metadata.capturas VALUES (1, ?)", (URL,))
    for id_, uf, cargo, urna, partido, votos, pessoa, tipo in PESSOAS_ELEITAS:
        # os deputados estaduais e distritais de 2026 ainda não têm data de posse na base
        inserir(
            con,
            id_,
            uf,
            cargo,
            urna,
            partido,
            pessoa,
            votos=votos,
            com_mandato="Deputado e" not in cargo,
            tipo=tipo,
        )
    # Bruno não tem cadastro: a profissão vem do TSE
    con.execute(
        "UPDATE marts.fct_candidaturas SET ocupacao = 'ENGENHEIRO' WHERE id_candidatura = '2026:RJ:2'"
    )
    # quem estava no cargo antes: ainda no mandato, ou já fora dele
    for id_, uf, cargo, urna, partido, pessoa in (
        ("2022:RJ:201", "RJ", "Deputado estadual", "Gil Anterior", "Partido F", 900),
        ("2022:RJ:202", "RJ", "Governador", "Gov Anterior", "Partido G", 901),
        ("2018:RJ:203", "RJ", "Senador", "Sena Antiga", "Partido H", 902),
        ("2018:RJ:204", "RJ", "Deputado estadual", "Dep Velho", "Partido I", 903),  # terminou em 2022
        ("2022:RJ:205", "RJ", "Deputado federal", "Ana Exemplo", "Partido A", 10),  # reeleita em 2026
        (
            "2022:SP:206",
            "SP",
            "Deputado estadual",
            "Elisa Ficticia",
            "Partido D",
            77,
        ),  # reeleita em 2026
        ("2018:RJ:ANA", "RJ", "Deputado federal", "Ana Exemplo", "Partido A", 10),
        ("2014:RJ:ANA", "RJ", "Governador", "Ana Exemplo", "Partido A", 10),
        ("2018:RJ:BRUNO", "RJ", "Deputado federal", "Bruno Modelo", "Partido B", 500),
    ):
        inserir(con, id_, uf, cargo, urna, partido, pessoa)
    # a de Ana em 2018 começa em 1º de fev. de 2019, sem lacuna com o mandato de 2023
    con.execute(
        "UPDATE marts.fct_cargos_ocupacoes SET dt_inicio = DATE '2019-02-01', dt_fim = DATE '2022-12-31' "
        "WHERE id_candidatura IN ('2018:RJ:ANA', '2018:RJ:BRUNO')"
    )
    # candidaturas sem mandato
    for id_, cargo, urna, partido, pessoa, resultado in (
        ("2018:RJ:ANA-G", "Governador", "Ana Exemplo", "Partido A", 10, "Não eleito"),
        ("2018:RJ:CARLA", "Deputado estadual", "<b>Carla</b> Teste", "Partido C", 12, "Não eleito"),
        ("2014:RJ:BRUNO", "Vereador", "Bruno Modelo", "Partido B", 500, "Suplente"),
    ):
        inserir(con, id_, "RJ", cargo, urna, partido, pessoa, resultado=resultado)
    # só a primeira pessoa tem total de campanha; as demais ficam sem dado (vazio, não zero)
    con.execute("INSERT INTO metadata.capturas VALUES (2, 'https://exemplo.gov.br/bens.zip')")
    con.execute("INSERT INTO metadata.capturas VALUES (3, 'https://exemplo.gov.br/contas.zip')")
    con.execute(
        "INSERT INTO marts.fct_campanhas VALUES ('2026:RJ:1', 1200000, 2400000, 2300000, 2, 3, 3, DATE '2026-10-24')"
    )
    # Ana (10) tem o cadastro da Câmara; Carla (12) e Nina (14) só a linha do cadastro, para mostrar Sem dado;
    # Bruno (500), só o que o TSE informa
    con.execute(
        "INSERT INTO metadata.capturas VALUES (4, "
        "'https://dadosabertos.camara.leg.br/arquivos/deputados/csv/deputados.csv')"
    )
    con.execute(
        "INSERT INTO metadata.capturas VALUES (5, "
        "'https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand/consulta_cand_2026.zip')"
    )
    con.execute(
        "UPDATE marts.dim_pessoas SET nome_civil = 'Ana Maria Exemplo da Silva', fonte_nome_civil = 'camara',"
        " dt_nascimento = DATE '1975-03-09', fonte_dt_nascimento = 'camara', uf_nascimento = 'RJ',"
        " fonte_uf_nascimento = 'camara', profissoes = 'Advogada; professora', fonte_profissoes = 'camara'"
        " WHERE id_pessoa = 10"
    )
    con.execute(
        "UPDATE marts.dim_pessoas SET nome_civil = 'Bruno Modelo', fonte_nome_civil = 'tse', id_captura_tse = 5,"
        " dt_captura_tse = ? WHERE id_pessoa = 500",
        (CAPTURA,),
    )
    con.execute(
        "INSERT INTO marts.dim_pessoas_cadastro VALUES (10, 'Niterói', 'https://exemplo.gov.br/ana',"
        " 'javascript:alert(1), https://www.instagram.com/ana.exemplo/?hl=pt&igsh=abcdefghijklmnopqrstuvwxyz0123456789,"
        "https://twitter.com/anaexemplo', 'https://exemplo.gov.br/foto10.jpg', 'camara', 4, ?),"
        " (12, NULL, NULL, NULL, NULL, 'camara', NULL, NULL),"
        " (14, NULL, NULL, NULL, NULL, 'senado', NULL, NULL)",
        (CAPTURA,),
    )
    for sigla, tipo, nome in (
        ("BR", "pais", "Brasil"),
        ("RJ", "uf", "Rio de Janeiro"),
        ("SP", "uf", "São Paulo"),
        ("DF", "uf", "Distrito Federal"),
    ):
        con.execute("INSERT INTO marts.dim_territorios VALUES (?, ?, ?, ?)", (sigla, tipo, nome, sigla))
    yield con
    con.close()
