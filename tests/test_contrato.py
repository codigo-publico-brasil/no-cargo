"""O contrato com o lake: as colunas de que o site depende existem no manifesto publicado.

O lake aponta sempre para o dado atual, sem versão por data. Este teste pega a mudança antes de ir ao ar.
`NO_CARGO_MANIFESTO` troca o endereço (por exemplo, para um manifesto de teste).
"""

import json
import os
import urllib.request

import pytest

MANIFESTO = os.environ.get("NO_CARGO_MANIFESTO", "https://datalake.codigopublicobrasil.com.br/manifesto.json")

# (camada, tabela) -> colunas que `dados.py` lê.
COLUNAS = {
    ("marts", "fct_cargos_ocupacoes"): (
        "id_pessoa id_cargo id_territorio id_partido id_candidatura ano_inicio dt_inicio dt_fim id_captura "
        "dt_captura"
    ),
    ("marts", "fct_mandatos"): "id_candidatura tipo_mandato",
    ("marts", "fct_candidaturas"): (
        "id_candidatura id_disputa nome_urna ocupacao partido id_pessoa foto_caminho resultado fl_eleito"
    ),
    ("marts", "fct_resultados"): "id_candidatura turno qtd_votos_nominais percentual_votos_validos",
    ("marts", "fct_campanhas"): (
        "id_candidatura valor_bens valor_receitas valor_despesas id_captura_bens id_captura_receitas "
        "id_captura_despesas dt_captura"
    ),
    ("marts", "dim_cargos"): "id_cargo nome",
    ("marts", "dim_territorios"): "id_territorio sigla",
    ("marts", "dim_partidos"): "id_partido sigla",
    ("marts", "dim_pessoas"): (
        "id_pessoa nome_civil nome_publico dt_nascimento uf_nascimento profissoes fonte_nome_civil "
        "fonte_dt_nascimento fonte_uf_nascimento fonte_profissoes foto_caminho id_captura_tse dt_captura_tse"
    ),
    ("marts", "dim_pessoas_cadastro"): (  # cadastro parlamentar (Câmara e Senado)
        "id_pessoa municipio_nascimento site_url rede_social_url foto_url fontes id_captura dt_captura"
    ),
    ("marts", "dim_eleicoes"): "id_eleicao ano_eleicao",
    ("marts", "dim_disputas"): "id_disputa id_eleicao id_cargo ue qtd_vagas",
    ("metadata", "capturas"): "id_captura url",
}


def test_the_published_manifest_has_every_column_the_site_reads():
    # o User-Agent padrão do Python leva 403
    pedido = urllib.request.Request(MANIFESTO, headers={"User-Agent": "no-cargo-ci"})
    with urllib.request.urlopen(pedido, timeout=60) as resposta:  # noqa: S310
        manifesto = json.load(resposta)
    publicadas = {(t["camada"], t["tabela"]): {c["nome"] for c in t["colunas"]} for t in manifesto["tabelas"]}
    faltam = {
        f"{camada}.{tabela}": sorted(set(colunas.split()) - publicadas.get((camada, tabela), set()))
        for (camada, tabela), colunas in COLUNAS.items()
        if set(colunas.split()) - publicadas.get((camada, tabela), set())
    }
    if faltam:
        pytest.fail(f"O manifesto {manifesto['id_execucao']} não traz o que o site lê: {faltam}")
