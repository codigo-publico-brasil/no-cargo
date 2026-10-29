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


_SELECT = """
SELECT b.id_candidatura, CAST(split_part(b.id_candidatura, ':', 1) AS INTEGER) AS ano_eleicao,
       split_part(b.id_candidatura, ':', 2) AS uf, r.turno, b.cargo, c.nome_urna, b.nome, b.partido,
       r.qtd_votos_nominais AS qtd_votos, r.percentual_votos_validos, b.id_pessoa, b.tipo_mandato,
       b.ano_inicio, b.dt_inicio, b.dt_fim_prevista, b.fonte_url, b.dt_captura,
       k.valor_bens, k.valor_receitas, k.valor_despesas, k.fonte_url_bens, k.fonte_url_receitas,
       k.fonte_url_despesas, k.dt_captura_campanha,
       p.foto_url, p.nome_civil, p.dt_nascimento, p.municipio_nascimento, p.uf_nascimento, p.profissoes,
       p.site_url, p.rede_social_url, p.fontes AS fonte_cadastro, p.fonte_url AS fonte_cadastro_url,
       p.dt_captura AS dt_captura_cadastro, c.ocupacao, c.foto_caminho
FROM marts.app_cargo_ocupantes b
JOIN marts.fct_candidaturas c ON c.id_candidatura = b.id_candidatura
LEFT JOIN (
    SELECT id_candidatura, turno, qtd_votos_nominais, percentual_votos_validos FROM marts.fct_resultados
    QUALIFY row_number() OVER (PARTITION BY id_candidatura ORDER BY turno DESC) = 1
) r ON r.id_candidatura = b.id_candidatura
LEFT JOIN marts.app_pessoa_campanhas k ON k.id_candidatura = b.id_candidatura
LEFT JOIN marts.app_pessoas p ON p.id_pessoa = b.id_pessoa
"""


def _ocupantes(con: Connection, onde: str, args: tuple[object, ...]) -> list[Row]:
    marcadores = ", ".join("?" for _ in CARGOS)
    return rows(
        con,
        _SELECT + f" WHERE b.cargo IN ({marcadores}) AND {onde} "
        "ORDER BY uf, b.cargo, c.nome_urna, b.id_candidatura",
        (*CARGOS, *args),
    )


def eleitos(con: Connection, ano: int) -> list[Row]:
    """Eleitos das eleições gerais do ano, com o total da campanha e a foto. Ordem alfabética."""
    return _ocupantes(con, "b.ano_inicio = ?", (ano + 1,))


def ocupantes(con: Connection, em: date) -> list[Row]:
    """Quem ocupa cada cargo das eleições gerais na data `em`, segundo a base (início e fim do mandato)."""
    return _ocupantes(con, "b.dt_inicio <= ? AND b.dt_fim_prevista >= ?", (em, em))


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


def ids_em_mandato(con: Connection, hoje: date) -> set[int]:
    """As pessoas que ocupam hoje um cargo das eleições gerais, inclusive quem foi reeleito."""
    marcadores = ", ".join("?" for _ in CARGOS)
    linhas = rows(
        con,
        "SELECT DISTINCT id_pessoa FROM marts.app_cargo_ocupantes "
        f"WHERE dt_inicio <= ? AND dt_fim_prevista >= ? AND cargo IN ({marcadores})",
        (hoje, hoje, *CARGOS),
    )
    return {r["id_pessoa"] for r in linhas}


def situacao_dos_cargos(con: Connection, ano: int) -> list[Row]:
    """Vagas, eleitos e pendentes de cada cargo em cada unidade eleitoral (só os cargos das eleições gerais)."""
    marcadores = ", ".join("?" for _ in CARGOS)
    linhas = rows(
        con,
        "SELECT d.ue AS uf, g.nome AS cargo, d.qtd_vagas, "
        "count(o.id_candidatura) AS qtd_eleitos, max(o.dt_captura) AS dt_captura "
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
    for r in linhas:
        r["qtd_pendentes"] = max(int(r["qtd_vagas"]) - int(r["qtd_eleitos"]), 0)
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
        "SELECT id_pessoa, id_candidatura, cargo, territorio, partido, ano_inicio, dt_inicio, dt_fim_prevista, "
        "base_do_inicio, tipo_mandato "
        "FROM marts.app_cargo_ocupantes WHERE list_contains(?, id_pessoa) ORDER BY ano_inicio DESC, dt_inicio DESC",
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
