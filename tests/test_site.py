import re
from datetime import date
from pathlib import Path

from nocargo import cores, dados, formato
from nocargo.__main__ import construir
from nocargo.cores import SEM_COR

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
    assert len(list((saida / "pessoa").glob("*.html"))) == 8


def test_brazil_page_separates_the_three_powers_and_their_spheres(warehouse, tmp_path):
    pagina = texto(site(warehouse, tmp_path), "index.html")
    assert [pagina.index(p) for p in ("Poder Executivo", "Poder Legislativo", "Poder Judiciário")] == sorted(
        pagina.index(p) for p in ("Poder Executivo", "Poder Legislativo", "Poder Judiciário")
    )
    for esfera in ("Federal", "Estadual", "Municipal"):
        assert esfera in pagina
    assert pagina.count("Em construção") == 4  # prefeitos, vereadores e os dois blocos do Judiciário
    assert "Aguardando o resultado do 2º turno" in pagina  # o presidente ainda não tem eleito


def test_party_bar_orders_by_seats_and_shows_every_party_in_its_own_brand_color():
    barra = formato.faixa({"PT": 5, "PL": 9, "NOVO": 2}, pendentes=2)
    assert re.findall(r'<span class="nome">([^<]+)</span>', barra) == [
        "PL",
        "PT",
        "NOVO",
        "Aguardando 2º turno",
    ]
    assert "background:#0F0073" in barra and "background:#DA1208" in barra and "background:#FF8511" in barra
    assert "posição política" in barra and "cor de marca" in barra


def test_party_without_a_registered_color_is_gray_and_the_legend_says_so():
    barra = formato.faixa({"PL": 3, "MISSÃO": 1})
    assert f"background:{SEM_COR}" in barra and "sem cor registrada" in barra
    assert "sem cor registrada" not in formato.faixa({"PL": 3})  # todos com cor: nada a avisar


def test_party_names_are_matched_the_way_the_tse_writes_them():
    assert cores.cor_do_partido("PC do B") == cores.cor_do_partido("PCdoB") == "#DA251C"
    assert cores.cor_do_partido("UNIÃO") == "#40CCFF" and cores.cor_do_partido("inexistente") is None


def test_every_registered_color_is_a_valid_hex_and_keys_are_normalized():
    for chave, cor in cores.CORES.items():
        assert re.fullmatch(r"#[0-9A-F]{6}", cor), chave
        assert chave == cores.chave(chave)


def test_hemicycle_has_one_dot_per_seat_grouped_by_party_from_largest_to_smallest():
    svg = formato.hemiciclo({"PT": 3, "PL": 5, "NOVO": 2}, "deputados")
    bolas = re.findall(r'<circle class="g(\d+)"', svg)
    assert len(bolas) == 10
    assert [bolas.count(str(i)) for i in range(3)] == [5, 3, 2]  # do maior para o menor
    assert re.findall(r'<span class="nome">([^<]+)</span>', svg) == ["PL", "PT", "NOVO"]
    assert 'fill="#0F0073"' in svg  # as bolinhas do PL, na cor do PL
    assert ">10</text>" in svg and "deputados" in svg and "não por posição política" in svg


def test_hemicycle_dots_stay_inside_the_drawing_and_never_overlap_for_any_size():
    for total, partidos in ((1, 1), (3, 2), (10, 4), (24, 6), (81, 14), (513, 20), (1035, 25)):
        base, resto = divmod(total, partidos)
        contagens = {f"P{i}": base + (1 if i < resto else 0) for i in range(partidos)}
        svg = formato.hemiciclo(contagens, "deputados")
        largura, altura = map(float, re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg).groups())
        bolas = [
            (float(x), float(y), float(r))
            for x, y, r in re.findall(r'cx="([\d.]+)" cy="([\d.]+)" r="([\d.]+)"', svg)
        ]
        assert len(bolas) == total
        for x, y, r in bolas:
            assert r <= formato.RAIO_MAXIMO
            assert r <= x <= largura - r and r <= y <= altura - r  # a bolinha inteira cabe no desenho
        for i, (x1, y1, r1) in enumerate(bolas):
            for x2, y2, r2 in bolas[i + 1 :]:
                assert (x1 - x2) ** 2 + (y1 - y2) ** 2 >= (r1 + r2) ** 2 * 0.99, (total, x1, y1, x2, y2)


def test_person_list_badges_are_not_overridden_by_the_gray_text_rule():
    css = (Path(__file__).parent.parent / "src" / "nocargo" / "static" / "style.css").read_text(
        encoding="utf-8"
    )
    assert ".pessoa .dados>span:not(.selo)" in css  # a regra do texto cinza não pode pintar o selo


def test_state_page_lists_the_elected_with_badges_and_filters_data(warehouse, tmp_path):
    pagina = texto(site(warehouse, tmp_path), "estado/RJ.html")
    assert 'data-tipo="novato"' in pagina and 'data-tipo="reeleito"' in pagina
    assert "Novato" in pagina and "Reeleito" in pagina and "Retorno" in pagina
    assert pagina.index("Ana Exemplo") < pagina.index("Bruno Modelo")  # ordem alfabética por padrão
    assert 'class="hemiciclo"' in pagina  # a bancada aparece em meia-lua
    assert "Aguardando o 2º turno" not in pagina  # o governador do RJ está eleito
    assert "Aguardando o 2º turno" in texto(site(warehouse, tmp_path), "estado/SP.html")


def test_district_deputies_are_shown_with_the_state_ones(warehouse, tmp_path):
    saida = site(warehouse, tmp_path)
    assert "Fábio Exemplo" in texto(saida, "estado/DF.html")
    assert "Elisa Ficticia" in texto(saida, "estado/SP.html")


def test_profile_shows_time_in_office_timeline_and_the_campaign_totals(warehouse, tmp_path):
    pagina = texto(site(warehouse, tmp_path), "pessoa/2026-RJ-1.html")
    assert "7 anos e 8 meses" in pagina  # desde 1º de fev. de 2019 até 25/10/2026, sem interrupção
    assert (
        "Próximo mandato" in pagina and "Mandato atual" in pagina and "fev. de 2023 a jan. de 2027" in pagina
    )
    assert "R$ 1,2 mi" in pagina and "R$ 2,4 mi" in pagina
    assert "foto10.jpg" in pagina


def test_profile_never_shows_a_posse_month_or_empty_dates(warehouse, tmp_path):
    saida = site(warehouse, tmp_path)
    for caminho in saida.rglob("*.html"):
        pagina = caminho.read_text(encoding="utf-8")
        assert "sem data" not in pagina, caminho  # mandato sem data não vira linha de "sem data a sem data"
    pagina = texto(saida, "pessoa/2026-RJ-1.html")
    assert "A partir de 2027, por 4 anos" in pagina and "Termina no início de 2031" in pagina
    assert (
        "fev. de 2027" not in pagina and "mai. de" not in pagina
    )  # a data exata da posse não vem de fonte confiável
    senador = texto(saida, "pessoa/2026-RJ-4.html")
    assert "A partir de 2027, por 8 anos" in senador and "Termina no início de 2035" in senador


def test_a_candidacy_with_two_rounds_appears_once_with_the_final_result(warehouse, tmp_path):
    pagina = texto(site(warehouse, tmp_path), "pessoa/2026-RJ-1.html")
    assert pagina.count("Candidatura em 2018") == 1 and "Governador, não eleito" in pagina
    assert "2º turno" not in pagina.split("Candidatura em 2018")[1].split("</li>")[0]


def test_legislature_dates_stand_in_for_the_missing_mandate_dates(warehouse):
    todos = dados.mandatos(warehouse, 10)
    assert [(m["dt_inicio"], m["dt_fim"]) for m in todos] == [
        (date(2023, 2, 1), date(2027, 1, 31)),
        (date(2019, 2, 1), date(2023, 1, 31)),
    ]


def test_profile_without_data_says_so_instead_of_showing_zero(warehouse, tmp_path):
    pagina = texto(site(warehouse, tmp_path), "pessoa/2026-RJ-2.html")
    assert pagina.count(">Sem dado</b>") == 3  # bens, receitas e despesas
    assert "R$ 0" not in pagina


def test_an_elected_without_a_link_gets_no_novato_badge_and_says_the_history_is_unconfirmed(
    warehouse, tmp_path
):
    saida = site(warehouse, tmp_path)
    pagina = texto(saida, "pessoa/2026-RJ-2.html")  # Bruno: deputado federal sem ligação a uma pessoa
    assert "Histórico de mandatos não confirmado" in pagina and "não quer dizer que seja novata" in pagina
    assert "Novato" not in pagina and "Primeiro mandato na" not in pagina
    assert "Histórico de mandatos não confirmado" in texto(
        saida, "pessoa/2026-SP-6.html"
    )  # estadual sem ligação


def test_novato_only_appears_for_someone_linked_and_without_a_previous_mandate(warehouse, tmp_path):
    pagina = texto(site(warehouse, tmp_path), "pessoa/2026-RJ-8.html")
    assert (
        "Novato" in pagina
        and "Primeiro mandato na Câmara dos Deputados." in pagina
        and "Ainda não tomou posse" in pagina
    )


def test_state_filters_only_list_the_types_that_exist_with_counts_and_a_no_badge_option(warehouse, tmp_path):
    pagina = texto(site(warehouse, tmp_path), "estado/RJ.html")
    assert "Sem selo (1)" in pagina and "Novatos (1)" in pagina and 'data-tipo="sem"' in pagina
    assert "Retorno (1)" in pagina and "Reeleitos (1)" in pagina


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


def test_a_deputy_elected_senator_is_novato_in_the_senate_and_the_page_says_the_other_house(
    warehouse, tmp_path
):
    warehouse.execute(
        "UPDATE marts.eleitos SET id_pessoa = 10, tipo_mandato = 'novato' WHERE id_candidatura = '2026:RJ:4'"
    )
    pagina = texto(site(warehouse, tmp_path), "pessoa/2026-RJ-4.html")
    assert "Primeiro mandato no Senado Federal." in pagina and "Já exerceu mandato na outra casa" in pagina
    assert "Primeiro mandato no Congresso" not in pagina


def test_a_win_for_another_office_appears_as_a_mandate_from_the_election_result(warehouse, tmp_path):
    pagina = texto(site(warehouse, tmp_path), "pessoa/2026-RJ-1.html")
    assert "Eleito em 2014" in pagina and "Governador, mandato previsto de 2015 a 2018" in pagina
    assert "não registra afastamentos" in pagina
    assert "Eleito em 2022" not in pagina  # deputado federal: o mandato já vem da Câmara
    assert pagina.index("Eleito em 2014") > pagina.index(
        "Candidatura em 2018"
    )  # do mais recente para o mais antigo
