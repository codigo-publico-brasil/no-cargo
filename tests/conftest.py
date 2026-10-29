"""Um warehouse pequeno, só com as tabelas do esquema `marts` que o site lê, com dados inventados."""

from collections.abc import Callable, Iterator
from datetime import date

import duckdb
import pytest

TABELAS = (
    """CREATE TABLE marts.fct_candidaturas (
        id_candidatura varchar, nome varchar, nome_urna varchar, ocupacao varchar, partido varchar,
        id_pessoa bigint, foto_caminho varchar, fl_eleito boolean
    )""",
    """CREATE TABLE marts.fct_resultados (
        id_candidatura varchar, turno integer, qtd_votos_nominais bigint, percentual_votos_validos decimal(5, 2)
    )""",
    """CREATE TABLE marts.fct_campanhas (
        id_candidatura varchar, valor_bens decimal(18, 2), valor_receitas decimal(18, 2), valor_despesas decimal(18, 2)
    )""",
    """CREATE TABLE marts.fct_candidaturas_bens (ano_eleicao integer, dt_captura date)""",
    """CREATE TABLE marts.app_cargo_ocupantes (
        id_candidatura varchar, id_pessoa bigint, nome varchar, cargo varchar, territorio varchar, partido varchar,
        dt_inicio date, base_do_inicio varchar, dt_fim_prevista date, base_eleicao varchar
    )""",
    """CREATE TABLE marts.app_pessoa_campanhas (
        id_candidatura varchar, id_pessoa bigint, ano_eleicao integer, cargo varchar, partido varchar,
        resultado varchar, fl_eleito boolean
    )""",
    """CREATE TABLE marts.app_pessoas (
        id_pessoa bigint, nome varchar, nome_civil varchar, dt_nascimento date, municipio_nascimento varchar,
        uf_nascimento varchar, profissoes varchar, site_url varchar, rede_social_url varchar, foto_url varchar,
        fontes varchar, dt_captura date
    )""",
    """CREATE TABLE marts.dim_eleicoes (id_eleicao varchar, ano_eleicao integer)""",
    """CREATE TABLE marts.dim_cargos (id_cargo varchar, nome varchar)""",
    """CREATE TABLE marts.dim_disputas (id_eleicao varchar, id_cargo varchar, ue varchar, qtd_vagas integer)""",
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
)

# id, uf, cargo, nome de urna, partido, votos, id_pessoa
PESSOAS_ELEITAS = [
    ("2026:RJ:1", "RJ", "Deputado federal", "Ana Exemplo", "Partido A", 142300, 10),
    ("2026:RJ:2", "RJ", "Deputado federal", "Bruno Modelo", "Partido B", 98100, 500),
    ("2026:RJ:8", "RJ", "Deputado federal", "Nina Nova", "Partido B", 50500, 14),
    ("2026:RJ:3", "RJ", "Deputado federal", "<b>Carla</b> Teste", "Partido C", 201500, 12),
    ("2026:RJ:4", "RJ", "Senador", "Paulo Exemplo", "Partido B", 3100000, 600),
    ("2026:RJ:5", "RJ", "Governador", "Diego Amostra", "Partido A", 2400000, 700),
    ("2026:SP:6", "SP", "Deputado estadual", "Elisa Ficticia", "Partido D", 70500, 77),
    ("2026:DF:7", "DF", "Deputado distrital", "Fábio Exemplo", "Partido E", 12000, 800),
]


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
) -> None:
    """Uma candidatura. Se eleita, ganha resultado, mandato na base (do ano seguinte por 4 anos, 8 para senador)
    e, sem data de posse, o que a base ainda não sabe (`com_mandato=False`: deputado estadual de 2026)."""
    ano = int(id_candidatura.split(":")[0])
    eleito = resultado.lower().startswith("eleito")
    foto = f"{ano}/{uf}/{id_candidatura.rsplit(':', 1)[-1]}.jpg"  # o caminho que a base informa
    con.execute(
        "INSERT INTO marts.fct_candidaturas VALUES (?, ?, ?, NULL, ?, ?, ?, ?)",
        (id_candidatura, urna, urna, partido, pessoa, foto, eleito),
    )
    con.execute(
        "INSERT INTO marts.app_pessoa_campanhas VALUES (?, ?, ?, ?, ?, ?, ?)",
        (id_candidatura, pessoa, ano, cargo, partido, resultado, eleito),
    )
    if eleito:
        con.execute(
            "INSERT INTO marts.fct_resultados VALUES (?, 1, ?, ?)", (id_candidatura, votos, percentual)
        )
    if eleito and com_mandato:
        anos = 8 if cargo == "Senador" else 4
        con.execute(
            "INSERT INTO marts.app_cargo_ocupantes VALUES (?, ?, ?, ?, ?, ?, ?, 'derivado', ?, 'informado')",
            (id_candidatura, pessoa, urna, cargo, uf, partido, date(ano + 1, 1, 1), date(ano + anos, 12, 31)),
        )


@pytest.fixture
def candidatura(warehouse: duckdb.DuckDBPyConnection) -> Callable[..., None]:
    return lambda *args, **kwargs: inserir(warehouse, *args, **kwargs)


@pytest.fixture
def warehouse(tmp_path) -> Iterator[duckdb.DuckDBPyConnection]:
    con = duckdb.connect(str(tmp_path / "warehouse.duckdb"))
    con.execute("CREATE SCHEMA marts")
    for ddl in TABELAS:
        con.execute(ddl)
    for id_cargo, nome in CARGOS_DA_BASE:
        con.execute("INSERT INTO marts.dim_cargos VALUES (?, ?)", (id_cargo, nome))
    con.execute("INSERT INTO marts.dim_eleicoes VALUES ('2026-1', 2026)")
    for ano in (2014, 2018, 2022, 2026):
        con.execute("INSERT INTO marts.fct_candidaturas_bens VALUES (?, ?)", (ano, CAPTURA))
    for id_, uf, cargo, urna, partido, votos, pessoa in PESSOAS_ELEITAS:
        # os deputados estaduais e distritais de 2026 ainda não têm data de posse na base
        inserir(
            con, id_, uf, cargo, urna, partido, pessoa, votos=votos, com_mandato="Deputado e" not in cargo
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
        "UPDATE marts.app_cargo_ocupantes SET dt_inicio = DATE '2019-02-01', dt_fim_prevista = DATE '2022-12-31' "
        "WHERE id_candidatura IN ('2018:RJ:ANA', '2018:RJ:BRUNO')"
    )
    # candidaturas sem mandato
    for id_, ano, cargo, partido, pessoa, resultado in (
        ("2018:RJ:ANA-G", 2018, "Governador", "Partido A", 10, "Não eleito"),
        ("2018:RJ:CARLA", 2018, "Deputado estadual", "Partido C", 12, "Não eleito"),
        ("2014:RJ:BRUNO", 2014, "Vereador", "Partido B", 500, "Suplente"),
    ):
        con.execute(
            "INSERT INTO marts.app_pessoa_campanhas VALUES (?, ?, ?, ?, ?, ?, false)",
            (id_, pessoa, ano, cargo, partido, resultado),
        )
    # só a primeira pessoa tem total de campanha; as demais ficam sem dado (vazio, não zero)
    con.execute("INSERT INTO marts.fct_campanhas VALUES ('2026:RJ:1', 1200000, 2400000, 2300000)")
    # vagas por cargo e estado, para saber quem falta
    for id_cargo, uf, vagas in (
        ("deputado_federal", "RJ", 3),
        ("senador", "RJ", 2),
        ("governador", "RJ", 1),
        ("presidente", "BR", 1),
        ("governador", "SP", 1),
    ):
        con.execute("INSERT INTO marts.dim_disputas VALUES ('2026-1', ?, ?, ?)", (id_cargo, uf, vagas))
    # Ana (10) tem cadastro completo; Carla (12) e Nina (14) só a foto, para mostrar Sem dado
    con.execute(
        "INSERT INTO marts.app_pessoas VALUES (10, 'Ana Exemplo', 'Ana Maria Exemplo da Silva', DATE '1975-03-09',"
        " 'Niterói', 'RJ', 'Advogada; professora', 'https://exemplo.gov.br/ana', 'javascript:alert(1),"
        " https://www.instagram.com/ana.exemplo/?hl=pt&igsh=abcdefghijklmnopqrstuvwxyz0123456789,"
        "https://twitter.com/anaexemplo', 'https://exemplo.gov.br/foto10.jpg', 'camara', ?),"
        " (12, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'camara', NULL),"
        " (14, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'senado', NULL)",
        (CAPTURA,),
    )
    yield con
    con.close()
