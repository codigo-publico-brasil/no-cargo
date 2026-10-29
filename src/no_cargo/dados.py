"""Consultas ao warehouse. Lêem só o esquema `marts` da plataforma de dados, em modo somente leitura.

A aplicação não importa nada da camada de dados: o contrato entre as duas é o esquema `marts` (colunas e tipos
garantidos pelo contrato do dbt). Nada é calculado ou estimado aqui além de somas e contagens do que a fonte diz:
quem ocupa cada cargo, e de quando a quando, vem de `app_cargo_ocupantes`.
"""

from datetime import date
from typing import Any

import duckdb

Row = dict[str, Any]
Connection = duckdb.DuckDBPyConnection

# Os cargos de cada poder, na ordem em que a página os mostra.
EXECUTIVO = ("Presidente", "Governador")
LEGISLATIVO = ("Senador", "Deputado federal", "Deputado estadual", "Deputado distrital")
CARGOS = (*EXECUTIVO, *LEGISLATIVO)
FONTE_TSE = "https://dadosabertos.tse.jus.br/dataset/candidatos-{ano}"


def rows(con: Connection, sql: str, args: tuple[object, ...] = ()) -> list[Row]:
    result = con.execute(sql, args)
    names = [d[0] for d in result.description]
    return [dict(zip(names, row, strict=True)) for row in result.fetchall()]


def ultimo_ano(con: Connection) -> int:
    """O ano da eleição geral mais recente com eleitos."""
    marcadores = ", ".join("?" for _ in CARGOS)
    found = con.execute(
        f"SELECT max(ano_eleicao) FROM marts.app_pessoa_campanhas WHERE fl_eleito AND cargo IN ({marcadores})",
        CARGOS,
    ).fetchone()
    if not found or found[0] is None:
        raise SystemExit("marts.app_pessoa_campanhas está vazio: rode a plataforma de dados antes.")
    return int(found[0])


def captura_do_tse(con: Connection, ano: int) -> date | None:
    """Quando os dados da eleição foram capturados do TSE (a captura mais recente dos bens declarados do ano)."""
    found = con.execute(
        "SELECT max(dt_captura) FROM marts.fct_candidaturas_bens WHERE ano_eleicao = ?", (ano,)
    ).fetchone()
    return found[0] if found else None


_SELECT = """
SELECT b.id_candidatura, CAST(split_part(b.id_candidatura, ':', 1) AS INTEGER) AS ano_eleicao,
       split_part(b.id_candidatura, ':', 2) AS uf, r.turno, b.cargo, c.nome_urna, b.nome, b.partido,
       r.qtd_votos_nominais AS qtd_votos, r.percentual_votos_validos, b.id_pessoa, b.dt_inicio, b.dt_fim_prevista,
       k.valor_bens, k.valor_receitas, k.valor_despesas,
       p.foto_url, p.nome_civil, p.dt_nascimento, p.municipio_nascimento, p.uf_nascimento, p.profissoes,
       p.site_url, p.rede_social_url, p.fontes AS fonte_cadastro, p.dt_captura AS dt_captura_cadastro,
       c.ocupacao, c.foto_caminho
FROM {base} b
JOIN marts.fct_candidaturas c ON c.id_candidatura = b.id_candidatura
LEFT JOIN (
    SELECT id_candidatura, turno, qtd_votos_nominais, percentual_votos_validos FROM marts.fct_resultados
    QUALIFY row_number() OVER (PARTITION BY id_candidatura ORDER BY turno DESC) = 1
) r ON r.id_candidatura = b.id_candidatura
LEFT JOIN marts.fct_campanhas k ON k.id_candidatura = b.id_candidatura
LEFT JOIN marts.app_pessoas p ON p.id_pessoa = b.id_pessoa
"""
# Quem ocupa o cargo (com datas) ou quem ganhou a eleição, mesmo sem data de posse na base (hoje, os deputados estaduais).
_OCUPA = "marts.app_cargo_ocupantes"
_GANHOU = """(
    SELECT pc.id_candidatura, pc.id_pessoa, c0.nome, pc.cargo, pc.partido, o.dt_inicio, o.dt_fim_prevista
    FROM marts.app_pessoa_campanhas pc
    JOIN marts.fct_candidaturas c0 ON c0.id_candidatura = pc.id_candidatura
    LEFT JOIN marts.app_cargo_ocupantes o ON o.id_candidatura = pc.id_candidatura
    WHERE pc.fl_eleito
)"""


def _ocupantes(con: Connection, base: str, onde: str, args: tuple[object, ...]) -> list[Row]:
    marcadores = ", ".join("?" for _ in CARGOS)
    linhas = rows(
        con,
        _SELECT.format(base=base) + f" WHERE b.cargo IN ({marcadores}) AND {onde} "
        "ORDER BY uf, b.cargo, c.nome_urna, b.id_candidatura",
        (*CARGOS, *args),
    )
    capturas = {a: captura_do_tse(con, a) for a in {r["ano_eleicao"] for r in linhas}}
    for r in linhas:
        r["fonte_url"] = FONTE_TSE.format(ano=r["ano_eleicao"])
        r["dt_captura"] = capturas[r["ano_eleicao"]]
    return linhas


def eleitos(con: Connection, ano: int) -> list[Row]:
    """Eleitos das eleições gerais do ano, com o total da campanha e a foto. Ordem alfabética."""
    return _ocupantes(con, _GANHOU, "split_part(b.id_candidatura, ':', 1) = ?", (str(ano),))


def ocupantes(con: Connection, em: date) -> list[Row]:
    """Quem ocupa cada cargo das eleições gerais na data `em`, segundo a base (início e fim do mandato)."""
    return _ocupantes(con, _OCUPA, "b.dt_inicio <= ? AND b.dt_fim_prevista >= ?", (em, em))


def data_da_posse(con: Connection, hoje: date) -> date | None:
    """O dia em que a composição que vem das urnas está completa: a última das primeiras posses depois de `hoje`."""
    marcadores = ", ".join("?" for _ in CARGOS)
    linha = rows(
        con,
        "SELECT max(inicio) AS posse FROM (SELECT cargo, min(dt_inicio) AS inicio FROM marts.app_cargo_ocupantes "
        f"WHERE dt_inicio > ? AND cargo IN ({marcadores}) GROUP BY cargo)",
        (hoje, *CARGOS),
    )
    return linha[0]["posse"] if linha else None


def em_exercicio(con: Connection, hoje: date, eleitos_do_ano: list[Row]) -> list[Row]:
    """Quem ocupa o cargo hoje e não está entre os eleitos do ano (os reeleitos têm ficha pela eleição nova).
    Cada linha leva `em_exercicio = True`."""
    do_ano = {r["id_pessoa"] for r in eleitos_do_ano if r["id_pessoa"]}
    return [{**r, "em_exercicio": True} for r in ocupantes(con, hoje) if r["id_pessoa"] not in do_ano]


def situacao_dos_cargos(con: Connection, ano: int) -> list[Row]:
    """Vagas, eleitos e pendentes de cada cargo em cada unidade eleitoral (só os cargos das eleições gerais)."""
    marcadores = ", ".join("?" for _ in CARGOS)
    linhas = rows(
        con,
        "SELECT d.ue AS uf, g.nome AS cargo, d.qtd_vagas, "
        "count(o.id_candidatura) AS qtd_eleitos "
        "FROM marts.dim_disputas d "
        "JOIN marts.dim_eleicoes e ON e.id_eleicao = d.id_eleicao "
        "JOIN marts.dim_cargos g ON g.id_cargo = d.id_cargo "
        "LEFT JOIN marts.app_cargo_ocupantes o ON o.cargo = g.nome "
        "  AND split_part(o.id_candidatura, ':', 1) = CAST(e.ano_eleicao AS VARCHAR) "
        "  AND split_part(o.id_candidatura, ':', 2) = d.ue "
        f"WHERE e.ano_eleicao = ? AND g.nome IN ({marcadores}) "
        "GROUP BY d.ue, g.nome, d.qtd_vagas ORDER BY d.ue, g.nome",
        (ano, *CARGOS),
    )
    captura = captura_do_tse(con, ano)
    for r in linhas:
        r["qtd_pendentes"] = max(int(r["qtd_vagas"]) - int(r["qtd_eleitos"]), 0)
        r["dt_captura"] = captura
    return linhas


def candidaturas_das_pessoas(con: Connection, ids: list[int]) -> dict[int, list[Row]]:
    """Candidaturas de cada pessoa em todas as eleições carregadas, da mais recente para a mais antiga."""
    linhas = rows(
        con,
        "SELECT id_pessoa, ano_eleicao, cargo, partido, resultado, fl_eleito FROM marts.app_pessoa_campanhas "
        "WHERE list_contains(?, id_pessoa) ORDER BY ano_eleicao DESC",
        (ids,),
    )
    por_pessoa: dict[int, list[Row]] = {}
    for r in linhas:
        por_pessoa.setdefault(r["id_pessoa"], []).append(r)
    return por_pessoa


def ocupacoes_das_pessoas(con: Connection, ids: list[int]) -> dict[int, list[Row]]:
    """Todos os mandatos de cada pessoa na base (qualquer cargo), do mais recente para o mais antigo."""
    linhas = rows(
        con,
        "SELECT id_pessoa, id_candidatura, cargo, territorio, partido, dt_inicio, dt_fim_prevista, base_do_inicio "
        "FROM marts.app_cargo_ocupantes WHERE list_contains(?, id_pessoa) ORDER BY dt_inicio DESC",
        (ids,),
    )
    por_pessoa: dict[int, list[Row]] = {}
    for r in linhas:
        por_pessoa.setdefault(r["id_pessoa"], []).append(r)
    return por_pessoa


def ininterrupto_desde(mandatos_da_pessoa: list[Row], hoje: date) -> date | None:
    """Início da sequência de mandatos que chega até hoje, sem intervalo maior que 60 dias; vazio se não há mandato em curso."""
    ordenados = sorted(
        (m for m in mandatos_da_pessoa if m["dt_inicio"] is not None),
        key=lambda m: m["dt_inicio"],
        reverse=True,
    )
    inicio: date | None = None
    limite = hoje
    for m in ordenados:
        fim = m["dt_fim"] or hoje
        if fim < hoje and inicio is None:
            return None  # o mandato mais recente já terminou: não está no cargo
        if (limite - fim).days > 60:
            break
        inicio, limite = m["dt_inicio"], m["dt_inicio"]
    return inicio
