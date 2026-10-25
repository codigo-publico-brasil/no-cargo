"""Consultas ao warehouse. Lêem só o esquema `marts` da plataforma de dados, em modo somente leitura.

A aplicação não importa nada da camada de dados: o contrato entre as duas é o esquema `marts` (colunas e tipos
garantidos pelo contrato do dbt). Nada é calculado ou estimado aqui além de somas e contagens do que a fonte diz.
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
    found = con.execute(
        "SELECT max(ano_eleicao) FROM marts.eleitos WHERE cargo IN ('Presidente', 'Governador', 'Senador', 'Deputado federal')"
    ).fetchone()
    if not found or found[0] is None:
        raise SystemExit("marts.eleitos está vazio: rode a plataforma de dados antes.")
    return int(found[0])


def eleitos(con: Connection, ano: int) -> list[Row]:
    """Eleitos das eleições gerais do ano, com o total da campanha, a foto e a posse do cargo. Ordem alfabética."""
    marcadores = ", ".join("?" for _ in CARGOS)
    return rows(
        con,
        "SELECT e.id_candidatura, e.ano_eleicao, e.uf, e.cargo, e.nome_urna, e.nome, e.partido, e.qtd_votos, "
        "e.percentual_votos_nominais, e.id_pessoa, e.tipo_mandato, e.dt_captura, e.fonte_url, "
        "k.valor_bens, k.valor_receitas, k.valor_despesas, k.fonte_url_bens, k.fonte_url_contas, "
        "p.foto_url, c.dt_posse "
        "FROM marts.eleitos e "
        "LEFT JOIN marts.eleitos_campanhas k USING (id_candidatura) "
        "LEFT JOIN marts.pessoas p ON p.id_pessoa = e.id_pessoa "
        "LEFT JOIN marts.eleitos_cargos c ON c.ano_eleicao = e.ano_eleicao AND c.ue = e.ue AND c.cargo = e.cargo "
        f"WHERE e.ano_eleicao = ? AND e.cargo IN ({marcadores}) "
        "ORDER BY e.uf, e.cargo, e.nome_urna, e.id_candidatura",
        (ano, *CARGOS),
    )


def situacao_dos_cargos(con: Connection, ano: int) -> list[Row]:
    """Vagas, eleitos e pendentes de cada cargo em cada unidade eleitoral (só os cargos das eleições gerais)."""
    marcadores = ", ".join("?" for _ in CARGOS)
    return rows(
        con,
        "SELECT uf, cargo, qtd_vagas, qtd_eleitos, qtd_pendentes, status, dt_posse, dt_captura "
        f"FROM marts.eleitos_cargos WHERE ano_eleicao = ? AND cargo IN ({marcadores}) ORDER BY uf, cargo",
        (ano, *CARGOS),
    )


def candidaturas(con: Connection, id_pessoa: int) -> list[Row]:
    """Candidaturas da pessoa em todas as eleições carregadas, da mais recente para a mais antiga."""
    return rows(
        con,
        "SELECT ano_eleicao, turno, uf, cargo, partido, resultado, dt_captura FROM marts.candidaturas "
        "WHERE id_pessoa = ? ORDER BY ano_eleicao DESC, turno DESC",
        (id_pessoa,),
    )


def mandatos(con: Connection, id_pessoa: int) -> list[Row]:
    """Mandatos da pessoa na Câmara e no Senado, do mais recente para o mais antigo."""
    return rows(
        con,
        "SELECT casa, cargo, uf, dt_inicio, dt_fim, dt_legislatura_inicio, dt_legislatura_fim FROM marts.mandatos "
        "WHERE id_pessoa = ? ORDER BY dt_inicio DESC",
        (id_pessoa,),
    )


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
