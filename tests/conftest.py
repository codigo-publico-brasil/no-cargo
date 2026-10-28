"""Um warehouse pequeno, só com o esquema `marts` e as colunas que o site lê, com dados inventados."""

from collections.abc import Iterator
from datetime import date

import duckdb
import pytest

ELEITOS = """
CREATE TABLE marts.eleitos (
    id_candidatura varchar, ano_eleicao integer, uf varchar, ue varchar, cargo varchar, nome_urna varchar,
    nome varchar, partido varchar, qtd_votos bigint, percentual_votos_nominais decimal(5, 2), id_pessoa bigint,
    tipo_mandato varchar, dt_captura date, fonte_url varchar, id_pessoa_tse bigint,
    ocupacao varchar, uf_nascimento varchar
)"""
CAMPANHAS = """
CREATE TABLE marts.eleitos_campanhas (
    id_candidatura varchar, valor_bens decimal(18, 2), valor_receitas decimal(18, 2), valor_despesas decimal(18, 2),
    fonte_url_bens varchar, fonte_url_contas varchar
)"""
CARGOS = """
CREATE TABLE marts.eleitos_cargos (
    ano_eleicao integer, uf varchar, ue varchar, cargo varchar, qtd_vagas integer, qtd_eleitos bigint,
    qtd_pendentes bigint, status varchar, dt_posse date, dt_captura date
)"""
PESSOAS = """
CREATE TABLE marts.pessoas (
    id_pessoa bigint, foto_url varchar, fonte varchar, nome_civil varchar, dt_nascimento date,
    municipio_nascimento varchar, uf_nascimento varchar, profissoes varchar, site_url varchar,
    rede_social_url varchar, dt_captura date
)"""
CANDIDATURAS = """
CREATE TABLE marts.candidaturas (
    id_pessoa bigint, ano_eleicao integer, turno integer, uf varchar, cargo varchar, partido varchar,
    resultado varchar, dt_captura date
)"""
HISTORICO = """
CREATE TABLE marts.eleitos_historico (
    id_candidatura varchar, ano_eleicao integer, turno integer, uf varchar, cargo varchar, partido varchar,
    resultado varchar, dt_captura date
)"""
MANDATOS = """
CREATE TABLE marts.mandatos (
    id_pessoa bigint, casa varchar, cargo varchar, uf varchar, dt_inicio date, dt_fim date,
    dt_legislatura_inicio date, dt_legislatura_fim date
)"""

URL = "https://dadosabertos.tse.jus.br/dataset/candidatos-2026"
CAPTURA = date(2026, 10, 24)
POSSE = date(2027, 2, 1)

# id, uf, cargo, nome de urna, partido, votos, id_pessoa, tipo_mandato
PESSOAS_ELEITAS = [
    ("2026:RJ:1", "RJ", "Deputado federal", "Ana Exemplo", "Partido A", 142300, 10, "reeleito"),
    (
        "2026:RJ:2",
        "RJ",
        "Deputado federal",
        "Bruno Modelo",
        "Partido B",
        98100,
        None,
        None,
    ),  # sem ligação: sem selo
    (
        "2026:RJ:8",
        "RJ",
        "Deputado federal",
        "Nina Nova",
        "Partido B",
        50500,
        14,
        "novato",
    ),  # ligada, sem mandato antes
    ("2026:RJ:3", "RJ", "Deputado federal", "<b>Carla</b> Teste", "Partido C", 201500, 12, "retorno"),
    ("2026:RJ:4", "RJ", "Senador", "Paulo Exemplo", "Partido B", 3100000, None, "novato"),
    ("2026:RJ:5", "RJ", "Governador", "Diego Amostra", "Partido A", 2400000, None, None),
    ("2026:SP:6", "SP", "Deputado estadual", "Elisa Ficticia", "Partido D", 70500, None, None),
    ("2026:DF:7", "DF", "Deputado distrital", "Fábio Exemplo", "Partido E", 12000, None, None),
]


@pytest.fixture
def warehouse(tmp_path) -> Iterator[duckdb.DuckDBPyConnection]:
    con = duckdb.connect(str(tmp_path / "warehouse.duckdb"))
    con.execute("CREATE SCHEMA marts")
    for ddl in (ELEITOS, CAMPANHAS, CARGOS, PESSOAS, CANDIDATURAS, MANDATOS, HISTORICO):
        con.execute(ddl)
    for id_, uf, cargo, urna, partido, votos, pessoa, tipo in PESSOAS_ELEITAS:
        con.execute(
            "INSERT INTO marts.eleitos VALUES (?, 2026, ?, ?, ?, ?, ?, ?, ?, 10.5, ?, ?, ?, ?, NULL, NULL, NULL)",
            (id_, uf, uf, cargo, urna, urna, partido, votos, pessoa, tipo, CAPTURA, URL),
        )
    # Bruno não tem cadastro: a profissão e o estado de nascimento vêm do TSE
    con.execute(
        "UPDATE marts.eleitos SET ocupacao = 'ENGENHEIRO', uf_nascimento = 'MG' WHERE id_candidatura = '2026:RJ:2'"
    )
    # Elisa foi eleita também em 2022 (mesma pessoa do TSE): quem foi reeleito aparece uma vez só
    con.execute("UPDATE marts.eleitos SET id_pessoa_tse = 77 WHERE id_candidatura = '2026:SP:6'")
    for id_, ano, uf, cargo, urna, partido, pessoa, tse in (
        (
            "2022:RJ:201",
            2022,
            "RJ",
            "Deputado estadual",
            "Gil Anterior",
            "Partido F",
            None,
            900,
        ),  # ainda no mandato
        ("2022:RJ:202", 2022, "RJ", "Governador", "Gov Anterior", "Partido G", None, 901),  # ainda no mandato
        ("2018:RJ:203", 2018, "RJ", "Senador", "Sena Antiga", "Partido H", None, 902),  # 8 anos: até 2026
        (
            "2018:RJ:204",
            2018,
            "RJ",
            "Deputado estadual",
            "Dep Velho",
            "Partido I",
            None,
            903,
        ),  # terminou em 2022
        (
            "2022:RJ:205",
            2022,
            "RJ",
            "Deputado federal",
            "Ana Exemplo",
            "Partido A",
            10,
            None,
        ),  # reeleita em 2026
        (
            "2022:SP:206",
            2022,
            "SP",
            "Deputado estadual",
            "Elisa Ficticia",
            "Partido D",
            None,
            77,
        ),  # reeleita em 2026
    ):
        con.execute(
            "INSERT INTO marts.eleitos (id_candidatura, ano_eleicao, uf, ue, cargo, nome_urna, nome, partido, qtd_votos,"
            " percentual_votos_nominais, id_pessoa, tipo_mandato, dt_captura, fonte_url, id_pessoa_tse)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1000, 1.5, ?, NULL, ?, ?, ?)",
            (id_, ano, uf, uf, cargo, urna, urna, partido, pessoa, CAPTURA, URL, tse),
        )
    # só a primeira pessoa tem total de campanha; as demais ficam sem dado (vazio, não zero)
    con.execute(
        "INSERT INTO marts.eleitos_campanhas VALUES ('2026:RJ:1', 1200000, 2400000, 2300000, ?, ?)",
        (URL, URL),
    )
    for uf, cargo, vagas, eleitos, status in (
        ("RJ", "Deputado federal", 3, 3, "eleito_provisorio"),
        ("RJ", "Senador", 2, 1, "aguardando_resultado"),
        ("RJ", "Governador", 1, 1, "eleito_provisorio"),
        ("RJ", "Presidente", 1, 0, "aguardando_resultado"),
        ("SP", "Governador", 1, 0, "aguardando_resultado"),
    ):
        con.execute(
            "INSERT INTO marts.eleitos_cargos VALUES (2026, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (uf, uf, cargo, vagas, eleitos, vagas - eleitos, status, POSSE, CAPTURA),
        )
    con.execute(  # Ana (10) tem cadastro completo; Carla (12) e Nina (14) só a foto, para mostrar Sem dado
        "INSERT INTO marts.pessoas VALUES (10, 'https://exemplo.gov.br/foto10.jpg', 'camara', 'Ana Maria Exemplo da Silva',"
        " DATE '1975-03-09', 'Niterói', 'RJ', 'Advogada; professora', 'https://exemplo.gov.br/ana', 'javascript:alert(1), https://www.instagram.com/ana.exemplo/?hl=pt&igsh=abcdefghijklmnopqrstuvwxyz0123456789,https://twitter.com/anaexemplo', ?),"
        " (12, NULL, 'camara', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),"
        " (14, NULL, 'senado', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)",
        (CAPTURA,),
    )
    con.execute(
        "INSERT INTO marts.candidaturas VALUES (10, 2022, 1, 'RJ', 'Deputado federal', 'Partido A', 'Eleito por qp', ?),"
        " (10, 2026, 1, 'RJ', 'Deputado federal', 'Partido A', 'Eleito por qp', ?),"
        " (12, 2018, 1, 'RJ', 'Deputado estadual', 'Partido C', 'Não eleito', ?),"
        " (10, 2018, 1, 'RJ', 'Governador', 'Partido A', '2º turno', ?),"
        " (10, 2018, 2, 'RJ', 'Governador', 'Partido A', 'Não eleito', ?),"
        " (10, 2014, 1, 'RJ', 'Governador', 'Partido A', 'Eleito', ?)",
        (CAPTURA, CAPTURA, CAPTURA, CAPTURA, CAPTURA, CAPTURA),
    )
    con.execute(
        "INSERT INTO marts.mandatos VALUES (10, 'Câmara dos Deputados', 'Deputado federal', 'RJ', NULL, NULL, ?, ?),"
        " (10, 'Câmara dos Deputados', 'Deputado federal', 'RJ', NULL, NULL, ?, ?)",
        (date(2019, 2, 1), date(2023, 1, 31), date(2023, 2, 1), date(2027, 1, 31)),
    )  # como no banco real: só a legislatura tem data
    # Bruno (sem ligação à Câmara) tem uma eleição anterior achada no TSE: foi eleito deputado federal em 2018
    con.execute(
        "INSERT INTO marts.eleitos_historico VALUES ('2026:RJ:2', 2018, 1, 'RJ', 'Deputado federal', 'Partido B', 'Eleito por qp', ?)",
        (CAPTURA,),
    )
    con.execute(
        "INSERT INTO marts.eleitos_historico VALUES ('2026:RJ:2', 2014, 1, 'RJ', 'Vereador', 'Partido B', 'Suplente', ?)",
        (CAPTURA,),
    )
    yield con
    con.close()
