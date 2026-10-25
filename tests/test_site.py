import re
from datetime import date
from pathlib import Path

from nocargo import dados, formato
from nocargo.__main__ import construir

HOJE = date(2026, 10, 25)


def site(warehouse, tmp_path: Path) -> Path:
    saida = tmp_path / "dist"
    construir(warehouse, saida, HOJE)
    return saida


def texto(saida: Path, caminho: str) -> str:
    return (saida / caminho).read_text(encoding="utf-8")


def test_the_site_has_the_main_pages_one_page_per_state_and_one_per_elected(warehouse, tmp_path):
    saida = site(warehouse, tmp_path)
    for pagina in ("index.html", "cargos.html", "como-calculamos.html", "style.css", "app.js"):
        assert (saida / pagina).exists()
    assert len(list((saida / "estado").glob("*.html"))) == 27
    assert len(list((saida / "pessoa").glob("*.html"))) == 7


def test_brazil_page_separates_the_three_powers_and_their_spheres(warehouse, tmp_path):
    pagina = texto(site(warehouse, tmp_path), "index.html")
    assert [pagina.index(p) for p in ("Poder Executivo", "Poder Legislativo", "Poder Judiciário")] == sorted(
        pagina.index(p) for p in ("Poder Executivo", "Poder Legislativo", "Poder Judiciário")
    )
    for esfera in ("Federal", "Estadual", "Municipal"):
        assert esfera in pagina
    assert pagina.count("Em construção") == 4  # prefeitos, vereadores e os dois blocos do Judiciário
    assert "Aguardando o resultado do 2º turno" in pagina  # o presidente ainda não tem eleito


def test_party_bar_orders_by_seats_keeps_five_and_groups_the_rest(warehouse, tmp_path):
    barra = formato.faixa({f"P{i}": 10 - i for i in range(8)}, pendentes=2)
    nomes = re.findall(r'<span class="nome">([^<]+)</span>', barra)
    assert nomes == ["P0", "P1", "P2", "P3", "P4", "Outros partidos", "Aguardando 2º turno"]
    assert "indicam partido" in barra  # a legenda avisa que a cor não identifica partido


def test_state_page_lists_the_elected_with_badges_and_filters_data(warehouse, tmp_path):
    pagina = texto(site(warehouse, tmp_path), "estado/RJ.html")
    assert 'data-tipo="novato"' in pagina and 'data-tipo="reeleito"' in pagina
    assert "Novato" in pagina and "Reeleito" in pagina and "Retorno" in pagina
    assert pagina.index("Ana Exemplo") < pagina.index("Bruno Modelo")  # ordem alfabética por padrão
    assert "Aguardando o 2º turno" not in pagina  # o governador do RJ está eleito
    assert "Aguardando o 2º turno" in texto(site(warehouse, tmp_path), "estado/SP.html")


def test_district_deputies_are_shown_with_the_state_ones(warehouse, tmp_path):
    saida = site(warehouse, tmp_path)
    assert "Fábio Exemplo" in texto(saida, "estado/DF.html")
    assert "Elisa Ficticia" in texto(saida, "estado/SP.html")


def test_profile_shows_time_in_office_timeline_and_the_campaign_totals(warehouse, tmp_path):
    pagina = texto(site(warehouse, tmp_path), "pessoa/2026-RJ-1.html")
    assert "7 anos e 8 meses" in pagina  # desde 1º de fev. de 2019 até 25/10/2026, sem interrupção
    assert "Próximo mandato" in pagina and "Mandato atual" in pagina
    assert "R$ 1,2 mi" in pagina and "R$ 2,4 mi" in pagina
    assert "foto10.jpg" in pagina


def test_profile_without_data_says_so_instead_of_showing_zero(warehouse, tmp_path):
    pagina = texto(site(warehouse, tmp_path), "pessoa/2026-RJ-2.html")
    assert pagina.count(">Sem dado</b>") == 3  # bens, receitas e despesas
    assert "Ainda não tomou posse" in pagina
    assert "Primeiro mandato no Congresso" in pagina  # o novato tem aviso e selo
    assert "R$ 0" not in pagina


def test_past_candidacies_without_mandate_appear_apart_from_mandates(warehouse, tmp_path):
    pagina = texto(site(warehouse, tmp_path), "pessoa/2026-RJ-3.html")
    assert "Candidatura em 2018" in pagina and "deputado estadual" in pagina.lower()


def test_names_are_escaped_and_pages_load_nothing_from_other_sites(warehouse, tmp_path):
    saida = site(warehouse, tmp_path)
    pagina = texto(saida, "estado/RJ.html")
    assert "<b>Carla</b>" not in pagina and "&lt;b&gt;Carla&lt;/b&gt; Teste" in pagina
    for caminho in saida.rglob("*.html"):
        externos = re.findall(r'(?:src|href)="(https?://[^"]+)"', caminho.read_text(encoding="utf-8"))
        assert all("dadosabertos.tse.jus.br" in u or "exemplo.gov.br" in u for u in externos), caminho


def test_time_in_office_counts_a_chain_of_mandates_and_stops_at_a_gap(warehouse):
    todos = dados.mandatos(warehouse, 10)
    assert dados.ininterrupto_desde(todos, HOJE) == date(2019, 2, 1)
    com_lacuna = [m for m in todos if m["dt_inicio"] == date(2023, 2, 1)] + [
        {**todos[1], "dt_inicio": date(2010, 2, 1), "dt_fim": date(2014, 1, 31)}
    ]
    assert dados.ininterrupto_desde(com_lacuna, HOJE) == date(2023, 2, 1)
    assert dados.ininterrupto_desde([m for m in todos if m["dt_fim"] < HOJE], HOJE) is None  # já terminou


def test_formatting_helpers():
    assert formato.reais(None) == "Sem dado" and formato.reais(340000) == "R$ 340 mil"
    assert formato.reais(1_200_000) == "R$ 1,2 mi" and formato.numero(1234567) == "1.234.567"
    assert formato.tempo(date(2015, 2, 1), date(2026, 10, 25)) == "11 anos e 8 meses"
    assert formato.mes_ano(date(2027, 2, 1)) == "fev. de 2027"
