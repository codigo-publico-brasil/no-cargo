"""Consultas ao datalake. Lêem só o esquema `marts` da plataforma (e `metadata.capturas`), em modo somente leitura.

A aplicação não importa nada da camada de dados: o contrato entre as duas é o esquema `marts` (colunas e tipos
garantidos pelo contrato do dbt). Nada é calculado ou estimado aqui além de somas e contagens do que a fonte diz:
quem ocupa cada cargo, e de quando a quando, vem de `fct_cargos_ocupacoes`.
"""

from datetime import date
from typing import Any

import duckdb

Row = dict[str, Any]
Connection = duckdb.DuckDBPyConnection

# O datalake público da plataforma: o catálogo (`catalogo.duckdb`) e, ao lado, os arquivos, como as fotos.
DATALAKE = "https://datalake.codigopublicobrasil.com.br"


def conectar(datalake: str = DATALAKE) -> Connection:
    """Anexa o catálogo do datalake em modo somente leitura. Não há dado local: `marts.` e `metadata.` são do catálogo."""
    con = duckdb.connect()
    con.execute("INSTALL httpfs")
    con.execute("LOAD httpfs")
    con.execute("ATTACH '" + f"{datalake}/catalogo.duckdb".replace("'", "''") + "' AS datalake (READ_ONLY)")
    con.execute("USE datalake")
    return con


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
        f"SELECT max(ano_eleicao) FROM {_CAMPANHAS} WHERE fl_eleito AND cargo IN ({marcadores})",
        CARGOS,
    ).fetchone()
    if not found or found[0] is None:
        raise SystemExit("Não há eleitos em marts.fct_candidaturas: rode a plataforma de dados antes.")
    return int(found[0])


# Um período em que uma pessoa ocupa um cargo num território, com os nomes juntados às dimensões. Só junta e
# renomeia: quem ocupa o quê, e de quando a quando, é regra do `marts`. `fonte_url` vem da captura do dado.
_OCUPANTES = """(
    SELECT o.id_candidatura, o.id_pessoa, coalesce(ps.nome_publico, ps.nome_civil) AS nome, g.nome AS cargo,
           t.sigla AS sigla_territorio, p.sigla AS partido, o.ano_inicio, o.dt_inicio, o.dt_fim AS dt_fim_prevista,
           m.tipo_mandato, cap.url AS fonte_url, o.dt_captura
    FROM marts.fct_cargos_ocupacoes o
    JOIN marts.dim_cargos g ON g.id_cargo = o.id_cargo
    LEFT JOIN marts.dim_territorios t ON t.id_territorio = o.id_territorio
    LEFT JOIN marts.dim_partidos p ON p.id_partido = o.id_partido
    LEFT JOIN marts.dim_pessoas ps ON ps.id_pessoa = o.id_pessoa
    LEFT JOIN marts.fct_mandatos m ON m.id_candidatura = o.id_candidatura
    LEFT JOIN metadata.capturas cap ON cap.id_captura = o.id_captura
)"""

# Uma candidatura, com a eleição e o cargo da disputa e os totais da campanha (nulos quando a fonte não entregou).
_CAMPANHAS = """(
    SELECT c.id_candidatura, c.id_pessoa, e.ano_eleicao, g.nome AS cargo, c.partido, c.resultado, c.fl_eleito,
           k.valor_bens, k.valor_receitas, k.valor_despesas, cb.url AS fonte_url_bens,
           cr.url AS fonte_url_receitas, cd.url AS fonte_url_despesas, k.dt_captura AS dt_captura_campanha
    FROM marts.fct_candidaturas c
    JOIN marts.dim_disputas d ON d.id_disputa = c.id_disputa
    JOIN marts.dim_eleicoes e ON e.id_eleicao = d.id_eleicao
    JOIN marts.dim_cargos g ON g.id_cargo = d.id_cargo
    LEFT JOIN marts.fct_campanhas k ON k.id_candidatura = c.id_candidatura
    LEFT JOIN metadata.capturas cb ON cb.id_captura = k.id_captura_bens
    LEFT JOIN metadata.capturas cr ON cr.id_captura = k.id_captura_receitas
    LEFT JOIN metadata.capturas cd ON cd.id_captura = k.id_captura_despesas
)"""

# A ficha da pessoa: `dim_pessoas` traz nome civil, nascimento, UF e profissões, cada um com a sua fonte (TSE,
# Câmara ou Senado); `dim_pessoas_cadastro` é o cadastro parlamentar (Câmara e Senado), de onde vêm município,
# site, rede social e a foto da casa. A URL de cada fonte vem da captura.
_PESSOA = """(
    SELECT p.id_pessoa, p.nome_civil, p.dt_nascimento, p.uf_nascimento, p.profissoes, p.fonte_nome_civil,
           p.fonte_dt_nascimento, p.fonte_uf_nascimento, p.fonte_profissoes, p.foto_caminho,
           capt.url AS fonte_tse_url, p.dt_captura_tse,
           d.municipio_nascimento, d.site_url, d.rede_social_url, d.foto_url, d.fontes AS fonte_cadastro,
           capd.url AS fonte_cadastro_url, d.dt_captura AS dt_captura_cadastro
    FROM marts.dim_pessoas p
    LEFT JOIN marts.dim_pessoas_cadastro d ON d.id_pessoa = p.id_pessoa
    LEFT JOIN metadata.capturas capt ON capt.id_captura = p.id_captura_tse
    LEFT JOIN metadata.capturas capd ON capd.id_captura = d.id_captura
)"""

_SELECT = f"""
SELECT coalesce(b.id_candidatura,
                CAST(b.ano_inicio AS VARCHAR) || ':' || coalesce(b.sigla_territorio, '--') || ':p'
                || CAST(b.id_pessoa AS VARCHAR)
       ) AS id_candidatura,
       b.id_candidatura IS NULL AS sem_eleicao,
       coalesce(CAST(split_part(b.id_candidatura, ':', 1) AS INTEGER), b.ano_inicio) AS ano_eleicao,
       coalesce(split_part(b.id_candidatura, ':', 2), b.sigla_territorio) AS uf, r.turno, b.cargo,
       coalesce(c.nome_urna, b.nome) AS nome_urna, b.nome, b.partido,
       r.qtd_votos_nominais AS qtd_votos, r.percentual_votos_validos, b.id_pessoa, b.tipo_mandato,
       b.ano_inicio, b.dt_inicio, b.dt_fim_prevista, b.fonte_url, b.dt_captura,
       k.valor_bens, k.valor_receitas, k.valor_despesas, k.fonte_url_bens, k.fonte_url_receitas,
       k.fonte_url_despesas, k.dt_captura_campanha,
       p.foto_url, p.nome_civil, p.dt_nascimento, p.municipio_nascimento, p.uf_nascimento, p.profissoes,
       p.site_url, p.rede_social_url, p.fonte_nome_civil, p.fonte_dt_nascimento, p.fonte_uf_nascimento,
       p.fonte_profissoes, p.fonte_cadastro, p.fonte_cadastro_url, p.dt_captura_cadastro, p.fonte_tse_url,
       p.dt_captura_tse, c.ocupacao, coalesce(c.foto_caminho, p.foto_caminho) AS foto_caminho
FROM {_OCUPANTES} b
LEFT JOIN marts.fct_candidaturas c ON c.id_candidatura = b.id_candidatura
LEFT JOIN (
    SELECT id_candidatura, turno, qtd_votos_nominais, percentual_votos_validos FROM marts.fct_resultados
    QUALIFY row_number() OVER (PARTITION BY id_candidatura ORDER BY turno DESC) = 1
) r ON r.id_candidatura = b.id_candidatura
LEFT JOIN {_CAMPANHAS} k ON k.id_candidatura = b.id_candidatura
LEFT JOIN {_PESSOA} p ON p.id_pessoa = b.id_pessoa
"""


def _ocupantes(con: Connection, onde: str, args: tuple[object, ...]) -> list[Row]:
    """Quem ocupa ou ocupará os cargos. Quem está no cargo sem eleição própria (a base só informa o exercício) vem
    com `sem_eleicao`; se a mesma pessoa tem as duas linhas no mesmo cargo, vale a da eleição."""
    marcadores = ", ".join("?" for _ in CARGOS)
    return rows(
        con,
        _SELECT + f" WHERE b.cargo IN ({marcadores}) AND {onde} "
        "QUALIFY row_number() OVER (PARTITION BY b.id_pessoa, b.cargo, b.ano_inicio "
        "ORDER BY b.id_candidatura IS NULL, b.dt_inicio DESC) = 1 "
        "ORDER BY uf, b.cargo, nome_urna, id_candidatura",
        (*CARGOS, *args),
    )


def eleitos(con: Connection, ano: int) -> list[Row]:
    """Eleitos das eleições gerais do ano, com o total da campanha e a foto. Ordem alfabética."""
    return _ocupantes(con, "b.ano_inicio = ? AND b.id_candidatura IS NOT NULL", (ano + 1,))


def ocupantes(con: Connection, em: date) -> list[Row]:
    """Quem ocupa cada cargo das eleições gerais na data `em`, segundo a base (início e fim do mandato)."""
    return _ocupantes(con, "b.dt_inicio <= ? AND b.dt_fim_prevista >= ?", (em, em))


def data_da_posse(con: Connection, hoje: date) -> date | None:
    """O dia em que a composição que vem das urnas está completa: a última das primeiras posses depois de `hoje`."""
    marcadores = ", ".join("?" for _ in CARGOS)
    linha = rows(
        con,
        f"SELECT max(inicio) AS posse FROM (SELECT cargo, min(dt_inicio) AS inicio FROM {_OCUPANTES} "
        f"WHERE dt_inicio > ? AND cargo IN ({marcadores}) GROUP BY cargo)",
        (hoje, *CARGOS),
    )
    return linha[0]["posse"] if linha else None


def na_posse(con: Connection, hoje: date, eleitos_do_ano: list[Row]) -> list[Row]:
    """A composição depois da posse: quem ocupa os cargos no dia em que a composição das urnas está completa, mais
    os eleitos do ano que a base ainda não data (hoje, os deputados estaduais e distritais)."""
    posse = data_da_posse(con, hoje)
    if posse is None:
        return []
    sem_data = [r for r in eleitos_do_ano if r["dt_inicio"] is None]
    renovadas = {(r["cargo"], r["uf"]) for r in sem_data}  # a casa inteira é renovada: o mandato antigo acaba
    ano = max((r["ano_eleicao"] for r in eleitos_do_ano), default=0)
    linhas = [
        r for r in ocupantes(con, posse) if (r["cargo"], r["uf"]) not in renovadas or r["ano_eleicao"] == ano
    ]
    vistos = {r["id_candidatura"] for r in linhas}
    return [*linhas, *(r for r in sem_data if r["id_candidatura"] not in vistos)]


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
        f"SELECT DISTINCT id_pessoa FROM {_OCUPANTES} "
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
        f"LEFT JOIN {_OCUPANTES} o ON o.cargo = g.nome "
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
        f"SELECT id_pessoa, ano_eleicao, cargo, partido, resultado, fl_eleito FROM {_CAMPANHAS} "
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
        "SELECT id_pessoa, id_candidatura, cargo, partido, ano_inicio, dt_inicio, dt_fim_prevista, tipo_mandato "
        f"FROM {_OCUPANTES} WHERE list_contains(?, id_pessoa) ORDER BY ano_inicio DESC, dt_inicio DESC",
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
