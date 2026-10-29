import html
import json
import re
from datetime import date, datetime
from pathlib import Path

from no_cargo import cores, dados, formato, seo
from no_cargo.__main__ import construir
from no_cargo.cores import SEM_COR
from no_cargo.paginas import FONTES, REPO, SITE_MAE, sem_acento

HOJE = date(2026, 10, 25)


def site(warehouse, tmp_path: Path) -> Path:
    saida = tmp_path / "dist"
    construir(warehouse, saida, HOJE)
    return saida


def texto(saida: Path, caminho: str) -> str:
    """Lê uma página; `*` acha a ficha pelo sufixo (o nome da pessoa vem antes no endereço)."""
    achados = list(saida.glob(caminho)) if "*" in caminho else [saida / caminho]
    assert len(achados) == 1, (caminho, achados)
    return achados[0].read_text(encoding="utf-8")


def test_the_site_has_the_main_pages_one_page_per_state_and_one_per_elected(warehouse, tmp_path):
    saida = site(warehouse, tmp_path)
    for pagina in ("index.html", "cargos.html", "como-calculamos.html", "style.css", "app.js"):
        assert (saida / pagina).exists()
    assert len(list((saida / "estado").glob("*.html"))) == 27
    assert (
        len(list((saida / "pessoa").glob("*.html"))) == 8 + 3
    )  # os 8 eleitos de 2026 e os 3 que ainda estão no mandato de antes


def test_brazil_page_separates_the_three_powers_and_their_spheres(warehouse, tmp_path):
    pagina = texto(site(warehouse, tmp_path), "index.html")
    assert [pagina.index(p) for p in ("Poder Executivo", "Poder Legislativo", "Poder Judiciário")] == sorted(
        pagina.index(p) for p in ("Poder Executivo", "Poder Legislativo", "Poder Judiciário")
    )
    for esfera in ("Federal", "Estadual", "Municipal"):
        assert esfera in pagina
    assert pagina.count('class="card obra"') == 4  # prefeitos, vereadores e os dois blocos do Judiciário
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
    css = (Path(__file__).parent.parent / "src" / "no_cargo" / "static" / "style.css").read_text(
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
    pagina = texto(site(warehouse, tmp_path), "pessoa/*-2026-rj-1.html")
    assert "7 anos e 8 meses" in pagina  # desde 1º de fev. de 2019 até 25/10/2026, sem interrupção
    assert "Próximo mandato" in pagina and "Mandato atual" in pagina and "2023 a 2027" in pagina
    assert (
        "R$ 1.200.000,00" in pagina
        and "R$ 2.400.000,00" in pagina
        and "R$ 2.300.000,00" in pagina
        and " mi<" not in pagina
    )
    assert "foto10.jpg" in pagina


def test_profile_never_shows_a_posse_month_or_empty_dates(warehouse, tmp_path):
    saida = site(warehouse, tmp_path)
    for caminho in saida.rglob("*.html"):
        pagina = caminho.read_text(encoding="utf-8")
        assert "sem data" not in pagina, caminho  # mandato sem data não vira linha de "sem data a sem data"
    pagina = texto(saida, "pessoa/*-2026-rj-1.html")
    assert "2027 a 2030" in pagina and "Termina no" not in pagina
    assert (
        "fev. de 2027" not in pagina and "mai. de" not in pagina
    )  # a data exata da posse não vem de fonte confiável
    senador = texto(saida, "pessoa/*-2026-rj-4.html")
    assert "2027 a 2034" in senador


def test_a_candidacy_with_two_rounds_appears_once_with_the_final_result(warehouse, tmp_path):
    pagina = texto(site(warehouse, tmp_path), "pessoa/*-2026-rj-1.html")
    assert pagina.count("Candidatura em 2018") == 1 and "Governador, não eleito" in pagina
    assert "2º turno" not in pagina.split("Candidatura em 2018")[1].split("</li>")[0]


def test_legislature_dates_stand_in_for_the_missing_mandate_dates(warehouse):
    todos = dados.mandatos(warehouse, 10)
    assert [(m["dt_inicio"], m["dt_fim"]) for m in todos] == [
        (date(2023, 2, 1), date(2027, 1, 31)),
        (date(2019, 2, 1), date(2023, 1, 31)),
    ]


def test_profile_without_data_says_so_instead_of_showing_zero(warehouse, tmp_path):
    pagina = texto(site(warehouse, tmp_path), "pessoa/*-2026-rj-2.html")
    campanha = pagina.split("A campanha de")[1]
    assert campanha.count('class="vazio num">Sem dado</dd>') == 3  # bens, receita e gasto
    assert "R$ 0" not in pagina


def test_an_elected_without_a_link_gets_no_novato_badge_and_says_the_history_is_unconfirmed(
    warehouse, tmp_path
):
    saida = site(warehouse, tmp_path)
    pagina = texto(
        saida, "pessoa/*-2026-sp-6.html"
    )  # deputado estadual sem ligação e sem eleição anterior achada
    assert "Histórico de mandatos não confirmado" in pagina and "não quer dizer que seja novata" in pagina
    assert "Novato" not in pagina and "Primeiro mandato na" not in pagina
    bruno = texto(saida, "pessoa/*-2026-rj-2.html")  # sem ligação à Câmara, mas com eleição anterior no TSE
    assert "Novato" not in bruno and "Primeiro mandato na" not in bruno


def test_novato_only_appears_for_someone_linked_and_without_a_previous_mandate(warehouse, tmp_path):
    pagina = texto(site(warehouse, tmp_path), "pessoa/*-2026-rj-8.html")
    assert (
        "Novato" in pagina
        and "Primeiro mandato na Câmara dos Deputados." in pagina
        and "Próximo mandato" in pagina
        and "começa em" in pagina
    )


def test_state_filters_only_list_the_types_that_exist_with_counts_and_a_no_badge_option(warehouse, tmp_path):
    pagina = texto(site(warehouse, tmp_path), "estado/RJ.html")
    assert "Sem selo (1)" in pagina and "Novatos (1)" in pagina and 'value="sem"' in pagina
    assert "Retorno (1)" in pagina and "Reeleitos (1)" in pagina


def test_past_candidacies_without_mandate_appear_apart_from_mandates(warehouse, tmp_path):
    pagina = texto(site(warehouse, tmp_path), "pessoa/*-2026-rj-3.html")
    assert "Candidatura em 2018" in pagina and "deputado estadual" in pagina.lower()


def test_names_are_escaped_and_pages_load_nothing_from_other_sites(warehouse, tmp_path):
    saida = site(warehouse, tmp_path)
    pagina = texto(saida, "estado/RJ.html")
    assert "<b>Carla</b>" not in pagina and "&lt;b&gt;Carla&lt;/b&gt; Teste" in pagina
    permitidos = {SITE_MAE, REPO, *(url for _, url in FONTES)}
    for caminho in saida.rglob("*.html"):
        html = re.sub(
            r'<a class="curto"[^>]*>', "", caminho.read_text(encoding="utf-8")
        )  # site e redes que a própria pessoa informou
        externos = re.findall(r'(?:src|href)="(https?://[^"]+)"', html)
        assert all(
            u in permitidos
            or u.startswith((REPO, seo.SITE))
            or "dadosabertos.tse.jus.br" in u
            or "exemplo.gov.br" in u
            for u in externos
        ), caminho
    for arquivo in (saida / "style.css", saida / "tokens.css"):
        assert "http" not in re.sub(r"/\*.*?\*/", "", arquivo.read_text(encoding="utf-8"), flags=re.S), (
            arquivo
        )
    assert all(
        (saida / "fonts" / f).stat().st_size > 1000
        for f in ("fraunces.woff2", "inter.woff2", "jetbrains-mono.woff2")
    )


def test_header_has_one_home_link_the_repo_and_the_project_symbol(warehouse, tmp_path):
    saida = site(warehouse, tmp_path)
    for caminho in ("index.html", "estado/RJ.html", "cargos.html"):
        pagina = texto(saida, caminho)
        topo = pagina[pagina.index('<header class="topo">') : pagina.index("</header>")]
        assert topo.count('class="marca"') == 1 and "no-cargo.svg" in topo and REPO in topo
    assert (saida / "no-cargo.svg").exists()
    assert (
        'data-theme="light"' in texto(saida, "index.html") and "Código Público Brasil" not in topo
    )  # só tema claro; o nome da organização fica no rodapé


def test_state_page_collapses_long_lists_and_links_to_the_three_powers(warehouse, tmp_path):
    pagina = texto(site(warehouse, tmp_path), "estado/RJ.html")
    assert (
        pagina.count('<details class="recolhivel">') == 2 and '<details class="recolhivel" open' not in pagina
    )
    for poder in ("executivo", "legislativo", "judiciario"):
        assert f'href="#poder-{poder}"' in pagina and f'id="poder-{poder}"' in pagina


def test_time_in_office_counts_a_chain_of_mandates_and_stops_at_a_gap(warehouse):
    todos = dados.mandatos(warehouse, 10)
    assert dados.ininterrupto_desde(todos, HOJE) == date(2019, 2, 1)
    com_lacuna = [m for m in todos if m["dt_inicio"] == date(2023, 2, 1)] + [
        {**todos[1], "dt_inicio": date(2010, 2, 1), "dt_fim": date(2014, 1, 31)}
    ]
    assert dados.ininterrupto_desde(com_lacuna, HOJE) == date(2023, 2, 1)
    assert dados.ininterrupto_desde([m for m in todos if m["dt_fim"] < HOJE], HOJE) is None  # já terminou


def test_formatting_helpers():
    assert formato.reais(None) == "Sem dado" and formato.reais(340000) == "R$ 340.000,00"
    assert formato.reais(1_200_000) == "R$ 1.200.000,00" and formato.numero(1234567) == "1.234.567"
    assert formato.tempo(date(2015, 2, 1), date(2026, 10, 25)) == "11 anos e 8 meses"
    assert formato.mes_ano(date(2027, 2, 1)) == "fev. de 2027"


def test_a_deputy_elected_senator_is_novato_in_the_senate_and_the_page_says_the_other_house(
    warehouse, tmp_path
):
    warehouse.execute(
        "UPDATE marts.eleitos SET id_pessoa = 10, tipo_mandato = 'novato' WHERE id_candidatura = '2026:RJ:4'"
    )
    pagina = texto(site(warehouse, tmp_path), "pessoa/*-2026-rj-4.html")
    assert "Primeiro mandato no Senado Federal." in pagina and "Já exerceu mandato na outra casa" in pagina
    assert "Primeiro mandato no Congresso" not in pagina


def test_a_win_for_another_office_appears_as_a_mandate_from_the_election_result(warehouse, tmp_path):
    pagina = texto(site(warehouse, tmp_path), "pessoa/*-2026-rj-1.html")
    assert "Eleito em 2014" in pagina and "Governador, mandato previsto de 2015 a 2018" in pagina
    assert "não registra afastamentos" in pagina
    assert "Eleito em 2022" not in pagina  # deputado federal: o mandato já vem da Câmara
    assert pagina.index("Eleito em 2014") > pagina.index(
        "Candidatura em 2018"
    )  # do mais recente para o mais antigo


def test_an_elected_without_a_link_shows_the_earlier_elections_found_in_the_tse(warehouse, tmp_path):
    pagina = texto(site(warehouse, tmp_path), "pessoa/*-2026-rj-2.html")  # Bruno
    assert "Eleito em 2018" in pagina and "Pelo Partido B." in pagina
    assert "Deputado federal, mandato previsto de 2019 a 2022" in pagina
    assert "Candidatura em 2014" in pagina and "Vereador, suplente" in pagina
    assert "Histórico de mandatos não confirmado" not in pagina  # há prova no TSE


def test_state_and_person_pages_say_where_you_are_and_link_back(warehouse, tmp_path):
    saida = site(warehouse, tmp_path)
    estado = texto(saida, "estado/RJ.html")
    assert 'aria-label="Você está em"' in estado and 'href="../index.html">Brasil</a>' in estado
    assert "<h1>Rio de Janeiro</h1>" in estado and "Estado · RJ" in estado
    pessoa = next((saida / "pessoa").glob("*.html")).read_text(encoding="utf-8")
    assert (
        'aria-label="Você está em"' in pessoa
        and 'href="../index.html">Brasil</a>' in pessoa
        and "../estado/" in pessoa
    )


def test_powers_are_section_headings_and_the_css_has_no_heavy_borders(warehouse, tmp_path):
    saida = site(warehouse, tmp_path)
    brasil = texto(saida, "index.html")
    assert brasil.count('class="poder"') == 3 and "<h2>Poder Executivo</h2>" in brasil
    css = texto(saida, "style.css")
    assert not re.search(
        r"border[a-z-]*:[^;}]*\b[2-9]px (solid|dashed)",
        css.replace("3px dashed", "").replace("3px solid", ""),
    )


def test_the_person_block_has_the_six_facts_and_short_links(warehouse, tmp_path):
    saida = site(warehouse, tmp_path)
    ana = texto(saida, "pessoa/*-2026-rj-1.html")
    topo = ana[
        ana.index('<section class="heroi ficha">') : ana.index("</section>")
    ]  # tudo no bloco do título
    assert "09/03/1975" in topo and "Niterói, RJ" in topo and "Advogada, professora" in topo
    assert ">Instagram</a>" in topo and ">X</a>" in topo and ">exemplo.gov.br</a>" in topo
    assert "igsh=" not in re.sub(
        r'title="[^"]*"|href="[^"]*"', "", topo
    )  # o endereço longo só vai no title e no href
    assert "javascript:" not in ana and "," not in topo.split("<dt>Rede social</dt>")[1].split("</dd>")[0]
    assert "Quem é</h2>" not in ana and "Na eleição de" not in ana and "No cadastro" not in ana
    bruno = texto(saida, "pessoa/*-2026-rj-2.html")  # sem ligação ao cadastro
    assert (
        "que ainda não está ligado a esta pessoa" in bruno
        and '<dt>Nascimento</dt><dd class="vazio num">Sem dado</dd>' in bruno
    )


def test_the_menu_has_no_origens_the_footer_does_and_the_home_has_the_powers_index(warehouse, tmp_path):
    saida = site(warehouse, tmp_path)
    brasil = texto(saida, "index.html")
    topo = brasil[brasil.index('<header class="topo">') : brasil.index("</header>")]
    nav = topo[topo.index('<nav class="nav"') : topo.index("</nav>")]
    assert ">Origens<" not in nav and "Método" not in topo and 'class="gh"' in topo and REPO in topo
    assert ">Origens dos dados</a>" in brasil[brasil.index('<footer class="rodape">') :]
    assert 'href="#poder-executivo"' in brasil and "Poder 1" not in brasil and "poder-num" not in brasil


def test_the_people_page_lists_everyone_elected_in_alphabetical_order_without_ranking(warehouse, tmp_path):
    saida = site(warehouse, tmp_path)
    pagina = texto(saida, "pessoas.html")
    nomes = re.findall(
        r'<a class="pessoa linha" href="pessoa/[^"]+"[^>]*><span class="dados"><b>(.*?)</b>', pagina
    )
    total = (
        warehouse.execute("SELECT count(*) FROM marts.eleitos WHERE ano_eleicao = 2026").fetchone()[0] + 3
    )  # mais os 3 em mandato
    assert len(nomes) == total and nomes == sorted(nomes, key=lambda n: sem_acento(html.unescape(n)))
    assert "&lt;b&gt;Carla&lt;/b&gt; Teste" in pagina  # nomes escapados
    assert "SP" in pagina and "Elisa Ficticia" in pagina  # de qualquer estado
    assert (
        'data-ordem="votos"' not in pagina and "<img" not in pagina.split("<main>")[1]
    )  # sem ordem por votos e sem foto (página leve)
    assert 'data-cargo="Senador"' in pagina and ">Pessoas</a>" in texto(saida, "index.html")
    assert 'href="pessoas.html"' in texto(saida, "index.html")
    assert "filtro-cargo" in texto(saida, "app.js")


def test_every_page_can_be_found_canonical_description_share_card_and_structured_data(warehouse, tmp_path):
    saida = site(warehouse, tmp_path)
    descricoes = set()
    for caminho in saida.rglob("*.html"):
        if caminho.name == "404.html":
            continue
        pagina = caminho.read_text(encoding="utf-8")
        relativo = caminho.relative_to(saida).as_posix()
        assert f'<link rel="canonical" href="{seo.url(relativo)}">' in pagina, relativo
        assert (
            'property="og:title"' in pagina and 'property="og:image"' in pagina and "twitter:card" in pagina
        ), relativo
        assert "noindex" not in pagina, relativo
        descricoes.add(re.search(r'<meta name="description" content="([^"]+)"', pagina).group(1))
    assert len(descricoes) > 8  # as fichas e os estados têm descrição própria, não a mesma para todos


def test_structured_data_is_valid_json_and_the_person_page_has_only_public_facts(warehouse, tmp_path):
    saida = site(warehouse, tmp_path)
    ficha = texto(saida, "pessoa/*-2026-rj-1.html")
    blocos = re.findall(r'<script type="application/ld\+json">(.*?)</script>', ficha, flags=re.S)
    dados_ = json.loads(blocos[0])["@graph"]
    pessoa = next(d for d in dados_ if d["@type"] == "Person")
    assert pessoa["name"] == "Ana Exemplo" and pessoa["jobTitle"] == "Deputado federal"
    assert not {"birthDate", "email", "telephone", "address"} & set(
        pessoa
    )  # só nome, cargo, partido e estado
    assert next(d for d in dados_ if d["@type"] == "BreadcrumbList")["itemListElement"][0]["name"] == "Brasil"
    assert json.loads(
        re.search(r'application/ld\+json">(.*?)</script>', texto(saida, "index.html"), flags=re.S).group(1)
    )


def test_the_site_publishes_robots_sitemap_llms_404_and_the_domain_for_github_pages(warehouse, tmp_path):
    saida = site(warehouse, tmp_path)
    robots = texto(saida, "robots.txt")
    assert (
        "Sitemap: " in robots
        and "User-agent: GPTBot\nAllow: /" in robots
        and "User-agent: ClaudeBot\nAllow: /" in robots
    )
    assert "Disallow" not in robots
    sitemap = texto(saida, "sitemap.xml")
    paginas = list(saida.rglob("*.html"))
    assert sitemap.count("<loc>") == len(paginas) - 1  # todas, menos a 404
    assert "/404.html" not in sitemap and seo.url("pessoas.html") in sitemap
    assert seo.SITE in texto(saida, "llms.txt") and "provisório" in texto(saida, "llms.txt")
    assert 'content="noindex"' in texto(saida, "404.html")
    assert (
        texto(saida, "CNAME").strip() == seo.SITE.removeprefix("https://") and (saida / ".nojekyll").exists()
    )


def test_a_person_page_links_to_a_prefilled_correction_issue(warehouse, tmp_path):
    ficha = texto(site(warehouse, tmp_path), "pessoa/*-2026-rj-1.html")
    assert f"{REPO}/issues/new?template=correcao.yml" in ficha and "pagina=https%3A%2F%2F" in ficha
    assert "Encontrou um erro?" in ficha


def test_person_pages_have_the_name_in_the_address(warehouse, tmp_path):
    saida = site(warehouse, tmp_path)
    nomes = {p.name for p in (saida / "pessoa").glob("*.html")}
    assert (
        "ana-exemplo-2026-rj-1.html" in nomes and "b-carla-b-teste-2026-rj-3.html" in nomes
    )  # a marcação HTML do nome não vira endereço, só letras e números


def test_every_page_has_the_floating_em_construcao_tag_saying_data_is_in_validation(warehouse, tmp_path):
    saida = site(warehouse, tmp_path)
    for caminho in (
        "index.html",
        "estado/RJ.html",
        "cargos.html",
        "pessoas.html",
        "como-calculamos.html",
        "pessoa/*-2026-rj-1.html",
    ):
        pagina = texto(saida, caminho)
        assert (
            pagina.count('<details class="obra-flutuante">') == 1
            and "<summary>Em construção</summary>" in pagina
        ), caminho
        assert "os dados ainda estão em validação" in pagina, caminho
        assert (
            "ainda não aparecem aqui: as partes" not in pagina
        )  # o aviso antigo dentro do bloco do título saiu


def test_the_people_page_includes_whoever_is_still_in_office_from_earlier_elections(warehouse, tmp_path):
    saida = site(warehouse, tmp_path)
    pagina = texto(saida, "pessoas.html")
    for nome in ("Gil Anterior", "Gov Anterior", "Sena Antiga"):  # mandato ainda em curso em 2026
        assert f"<b>{nome}</b>" in pagina, nome
    assert "Dep Velho" not in pagina  # o mandato de 2018 terminou em 2022
    assert (
        pagina.count("<b>Ana Exemplo</b>") == 1 and pagina.count("<b>Elisa Ficticia</b>") == 1
    )  # reeleito conta uma vez
    assert "eleito em 2022" in pagina and 'data-grupo="atual"' in pagina and 'data-grupo="novo"' in pagina
    assert ">Em mandato</button>" in pagina and ">Eleitos em 2026</button>" in pagina


def test_a_person_still_in_office_gets_a_page_with_the_current_mandate_and_no_provisional_result(
    warehouse, tmp_path
):
    saida = site(warehouse, tmp_path)
    pagina = texto(saida, "pessoa/gil-anterior-2022-rj-201.html")
    assert "Mandato em curso" in pagina and "2023 a 2026" in pagina and "Mandato atual" in pagina
    assert "Resultado provisório" not in pagina and "Próximo mandato" not in pagina
    senador = texto(saida, "pessoa/sena-antiga-2018-rj-203.html")
    assert "2019 a 2026" in senador


def test_the_menu_starts_with_inicio_and_marks_it_on_the_home(warehouse, tmp_path):
    saida = site(warehouse, tmp_path)
    for caminho, marcado in (("index.html", True), ("pessoas.html", False), ("estado/RJ.html", False)):
        pagina = texto(saida, caminho)
        topo = pagina[pagina.index('<nav class="nav"') : pagina.index("</nav>")]
        assert topo.index(">Brasil<") < topo.index(">Estados<") < topo.index(">Pessoas<"), caminho
        assert ('aria-current="page">Brasil</a>' in topo) is marcado, caminho


def test_the_national_office_has_no_fake_state_in_the_breadcrumb_header_or_list(warehouse, tmp_path):
    warehouse.execute(
        "INSERT INTO marts.eleitos (id_candidatura, ano_eleicao, uf, ue, cargo, nome_urna, nome, partido, qtd_votos,"
        " percentual_votos_nominais, id_pessoa, tipo_mandato, dt_captura, fonte_url, id_pessoa_tse)"
        " VALUES ('2022:BR:301', 2022, 'BR', 'BR', 'Presidente', 'Pres Anterior', 'Pres Anterior', 'Partido J', 1000, 50.9,"
        " NULL, NULL, DATE '2026-10-24', 'https://dadosabertos.tse.jus.br/dataset/candidatos-2022', 903)"
    )
    saida = site(warehouse, tmp_path)
    pagina = texto(saida, "pessoa/pres-anterior-2022-br-301.html")
    assert (
        "estado/BR.html" not in pagina
        and "Presidente &middot; Brasil" in pagina
        and "presidente do Brasil" in pagina
    )
    assert pagina.count("Mandato em curso") == 1  # a etiqueta; o período aparece na barra do mandato atual
    assert "Presidente &middot; Brasil &middot; Partido J" in texto(saida, "pessoas.html")


def test_who_has_no_register_uses_the_tse_profession_and_birth_state(warehouse, tmp_path):
    saida = site(warehouse, tmp_path)
    bruno = texto(
        saida, "pessoa/bruno-modelo-2026-rj-2.html"
    )  # sem cadastro: ocupação e UF de nascimento do TSE
    assert (
        "<dt>Profissões</dt><dd>Engenheiro</dd>" in bruno
        and "<dt>Naturalidade</dt><dd>Minas Gerais</dd>" in bruno
    )
    assert "Nome completo, profissão e estado de nascimento: TSE" in bruno
    ana = texto(saida, "pessoa/ana-exemplo-2026-rj-1.html")  # com cadastro: nada vem do TSE além da eleição
    assert (
        "Advogada, professora" in ana
        and "Fonte: cadastro da Câmara dos Deputados" in ana
        and "estado de nascimento" not in ana
    )


def test_photos_of_the_year_are_copied_and_served_from_the_site_itself(warehouse, tmp_path):
    origem = tmp_path / "fotos"
    (origem / "2026" / "RJ").mkdir(parents=True)
    (origem / "2026" / "RJ" / "1.jpg").write_bytes(b"\xff\xd8jpeg")  # Ana, 2026:RJ:1
    (origem / "2022" / "RJ").mkdir(parents=True)
    (origem / "2022" / "RJ" / "201.jpeg").write_bytes(b"22")  # Gil Anterior, em mandato (eleito em 2022)
    saida = tmp_path / "dist"
    construir(warehouse, saida, HOJE, fotos=origem)
    assert (saida / "fotos" / "2026" / "RJ" / "1.jpg").read_bytes() == b"\xff\xd8jpeg"
    ana = texto(saida, "pessoa/ana-exemplo-2026-rj-1.html")
    assert (
        'src="../fotos/2026/RJ/1.jpg"' in ana and "foto10.jpg" not in ana and "Foto: TSE" in ana
    )  # a local vale primeiro
    assert 'src="../fotos/2026/RJ/1.jpg"' in texto(saida, "estado/RJ.html")
    bruno = texto(saida, "pessoa/bruno-modelo-2026-rj-2.html")  # sem arquivo: segue o desenho de reserva
    assert "Sem foto" in bruno and "Foto: TSE" not in bruno
    assert len(list((saida / "fotos").rglob("*.jp*g"))) == 2
    gil = texto(
        saida, "pessoa/gil-anterior-2022-rj-201.html"
    )  # quem está em mandato usa a foto do ano da eleição
    assert 'src="../fotos/2022/RJ/201.jpeg"' in gil and "Foto: TSE" in gil
    assert "Sem foto" in texto(
        saida, "pessoa/sena-antiga-2018-rj-203.html"
    )  # sem arquivo de 2018: desenho de reserva


def test_without_a_photos_folder_nothing_is_copied_and_the_page_keeps_the_register_photo(warehouse, tmp_path):
    saida = site(warehouse, tmp_path)
    assert not (saida / "fotos").exists()
    assert "foto10.jpg" in texto(saida, "pessoa/ana-exemplo-2026-rj-1.html")


def test_the_home_shows_the_elected_president_with_photo_party_and_votes(warehouse, tmp_path):
    warehouse.execute(
        "INSERT INTO marts.eleitos (id_candidatura, ano_eleicao, uf, ue, cargo, nome_urna, nome, partido, qtd_votos,"
        " percentual_votos_nominais, id_pessoa, tipo_mandato, dt_captura, fonte_url, id_pessoa_tse)"
        " VALUES ('2026:BR:9', 2026, 'BR', 'BR', 'Presidente', 'Pres Novo', 'Pres Novo', 'Partido K', 64256232, 51.8,"
        " NULL, NULL, DATE '2026-10-24', 'https://dadosabertos.tse.jus.br/dataset/candidatos-2026', 904)"
    )
    fotos = tmp_path / "origem" / "2026" / "BR"
    fotos.mkdir(parents=True)
    (fotos / "9.jpg").write_bytes(b"jpg")
    saida = tmp_path / "dist"
    construir(warehouse, saida, hoje=date(2026, 10, 29), fotos=tmp_path / "origem")
    inicio = texto(saida, "index.html")
    card = inicio[inicio.index('class="card presidente"') :]
    card = card[: card.index("</div></div>")]
    assert 'src="fotos/2026/BR/9.jpg"' in card and "Partido K" in card and "64.256.232 votos" in card
    assert 'href="pessoa/pres-novo-2026-br-9.html"' in card


def test_a_person_page_does_not_carry_the_provisional_label(warehouse, tmp_path):
    pagina = texto(site(warehouse, tmp_path), "pessoa/ana-exemplo-2026-rj-1.html")
    assert "Próximo mandato" in pagina and "provisório" not in pagina.lower()


def test_the_current_mandate_shows_how_much_has_passed_and_the_next_one_starts_empty(warehouse, tmp_path):
    pagina = texto(site(warehouse, tmp_path), "pessoa/gil-anterior-2022-rj-201.html")
    # 2023-01-01 a 2026-12-31 e hoje = 25/10/2026: 1.394 de 1.461 dias
    assert '<progress max="100" value="95"' in pagina and "95% cumprido" in pagina
    assert "Períodos previstos pelo resultado do TSE" in pagina
    nova = texto(site(warehouse, tmp_path), "pessoa/*-2026-rj-8.html")
    assert '<progress max="100" value="0"' in nova and "começa em" in nova


def test_the_votes_say_what_the_percentage_refers_to_and_the_round(warehouse, tmp_path):
    pagina = texto(site(warehouse, tmp_path), "pessoa/*-2026-rj-1.html")
    assert "10,5% dos votos nominais para deputado federal em Rio de Janeiro, 1º turno" in pagina


def test_the_timeline_shows_the_party_of_each_past_election(warehouse, tmp_path):
    pagina = texto(site(warehouse, tmp_path), "pessoa/*-2026-rj-2.html")  # Bruno
    assert "Pelo Partido B. Fonte: TSE" in pagina


def test_the_states_have_their_own_page_and_the_home_only_links_to_it(warehouse, tmp_path):
    saida = site(warehouse, tmp_path)
    estados = texto(saida, "estados.html")
    assert estados.count('href="estado/') == 27 and "Nordeste" in estados
    inicio = texto(saida, "index.html")
    assert 'href="estados.html"' in inicio and inicio.count('href="estado/') == 0
    assert "busca-estado" not in inicio
    assert ">Estados</a>" in inicio[inicio.index('<nav class="nav"') : inicio.index("</nav>")]


def test_the_states_page_has_a_search_box_that_only_shows_with_javascript(warehouse, tmp_path):
    saida = site(warehouse, tmp_path)
    estados = texto(saida, "estados.html")
    assert 'id="busca-estado"' in estados and 'class="busca-estado" hidden' in estados
    assert 'data-nome="sao paulo sp"' in estados and "busca-estado" in texto(saida, "app.js")


def test_the_home_shows_when_the_site_was_updated_and_the_shortcuts_come_before_the_power_buttons(
    warehouse, tmp_path
):
    saida = tmp_path / "dist"
    construir(warehouse, saida, hoje=date(2026, 10, 29), agora=datetime(2026, 10, 29, 14, 32))
    inicio = texto(saida, "index.html")
    assert "Site atualizado em 29/10/2026 às 14:32" in inicio
    assert inicio.index('class="atalhos"') < inicio.index('class="indice"')
