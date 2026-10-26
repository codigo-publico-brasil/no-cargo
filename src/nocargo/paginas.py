"""As páginas do site, como texto HTML. Cada função devolve a página inteira; os links são relativos à pasta da página."""

from collections import Counter
from datetime import date

from nocargo.dados import EXECUTIVO, LEGISLATIVO, Row
from nocargo.formato import (
    data_curta,
    e,
    endereco,
    faixa,
    foto,
    hemiciclo,
    mes_ano,
    numero,
    percentual,
    reais,
    selo,
    tempo,
)

UFS = {
    "AC": ("Acre", "Norte"), "AL": ("Alagoas", "Nordeste"), "AP": ("Amapá", "Norte"), "AM": ("Amazonas", "Norte"),
    "BA": ("Bahia", "Nordeste"), "CE": ("Ceará", "Nordeste"), "DF": ("Distrito Federal", "Centro-Oeste"),
    "ES": ("Espírito Santo", "Sudeste"), "GO": ("Goiás", "Centro-Oeste"), "MA": ("Maranhão", "Nordeste"),
    "MT": ("Mato Grosso", "Centro-Oeste"), "MS": ("Mato Grosso do Sul", "Centro-Oeste"),
    "MG": ("Minas Gerais", "Sudeste"), "PA": ("Pará", "Norte"), "PB": ("Paraíba", "Nordeste"),
    "PR": ("Paraná", "Sul"), "PE": ("Pernambuco", "Nordeste"), "PI": ("Piauí", "Nordeste"),
    "RJ": ("Rio de Janeiro", "Sudeste"), "RN": ("Rio Grande do Norte", "Nordeste"),
    "RS": ("Rio Grande do Sul", "Sul"), "RO": ("Rondônia", "Norte"), "RR": ("Roraima", "Norte"),
    "SC": ("Santa Catarina", "Sul"), "SP": ("São Paulo", "Sudeste"), "SE": ("Sergipe", "Nordeste"),
    "TO": ("Tocantins", "Norte"),
}  # fmt: skip

PODERES = (
    ("1", "Poder Executivo", "Administra o governo e executa as leis: saúde, educação, segurança, estradas e o orçamento.",
     "Quem ocupa: presidente, governadores e prefeitos. Todos são eleitos pelo voto."),
    ("2", "Poder Legislativo", "Cria as leis, aprova o orçamento e fiscaliza o Executivo.",
     "Quem ocupa: deputados, senadores e vereadores. Todos são eleitos pelo voto."),
    ("3", "Poder Judiciário", "Julga os conflitos e garante que as leis sigam a Constituição.",
     "Quem ocupa: ministros, desembargadores e juízes. Não são eleitos: são nomeados ou entram por concurso."),
)  # fmt: skip

NAV = (("brasil", "Brasil", "index.html"), ("cargos", "Entenda os cargos", "cargos.html"),
       ("como", "Como calculamos", "como-calculamos.html"))  # fmt: skip


def pagina(titulo: str, corpo: str, ativa: str, raiz: str = "", descricao: str = "") -> str:
    menu = "".join(
        f'<a href="{raiz}{href}"{' aria-current="page"' if chave == ativa else ""}>{nome}</a>'
        for chave, nome, href in NAV
    )
    return (
        '<!doctype html>\n<html lang="pt-BR">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{e(titulo)} | No Cargo</title>\n"
        f'<meta name="description" content="{e(descricao or "Quem ocupa o poder no Brasil, pelos três poderes, com a fonte oficial ao lado.")}">\n'
        f'<link rel="stylesheet" href="{raiz}style.css">\n</head>\n<body>\n'
        '<header class="topo"><div class="marca"><span class="logo" aria-hidden="true">&#10003;</span>'
        f'<a href="{raiz}index.html">No Cargo</a></div><nav aria-label="Principal">{menu}</nav></header>\n'
        f"<main>\n{corpo}\n</main>\n"
        '<footer class="rodape"><b>No Cargo</b><p>Dados do TSE, da Câmara dos Deputados e do Senado Federal. '
        "Uma iniciativa Código Público Brasil.</p>"
        f'<a href="{raiz}como-calculamos.html">Como calculamos e de onde vêm os dados</a></footer>\n'
        f'<script src="{raiz}app.js" defer></script>\n</body>\n</html>\n'
    )


def faixa_de_titulo(chave: str, titulo: str, subtitulo: str, extra: str = "") -> str:
    return (
        f'<section class="heroi"><span class="sobretitulo">{e(chave)}</span><h1>{e(titulo)}</h1>'
        f"<p>{e(subtitulo)}</p>{extra}</section>"
    )


def aviso_provisorio(capturado: date | None) -> str:
    return (
        '<p class="aviso"><span class="selo provisorio">Resultado provisório</span> '
        f"TSE, capturado em {data_curta(capturado)}. O resultado só é confirmado na diplomação.</p>"
    )


def banda(numero_: str, nome: str, descricao: str, quem: str = "") -> str:
    return (
        f'<div class="poder"><div class="poder-nome"><span class="poder-num">{numero_}</span><h2>{e(nome)}</h2></div>'
        f"<p>{e(descricao)}</p>" + (f'<p class="quem">{e(quem)}</p>' if quem else "") + "</div>"
    )


def esfera(nome: str, escopo: str) -> str:
    return f'<div class="esfera"><span>{e(nome)}</span><i></i><small>{e(escopo)}</small></div>'


def em_construcao(titulo: str, texto: str) -> str:
    return (
        f'<div class="card obra"><b>{e(titulo)}</b> <span class="selo obra-selo">Em construção</span>'
        f"<p>{e(texto)}</p></div>"
    )


SEM_SELO = (
    '<span class="selo semselo" title="Não ligamos a pessoa a um mandato anterior, então não afirmamos nada">'
    'Histórico não confirmado</span><span class="qtd">{}</span>'
)


def casa(
    titulo: str,
    subtitulo: str,
    partidos: Counter[str],
    pendentes: int = 0,
    selos: Counter[str] | None = None,
    rotulo: str | None = None,
) -> str:
    """Casa legislativa: meia-lua com uma bolinha por cadeira (`rotulo` no centro). Sem `rotulo`, barra de 100%."""
    chips = ""
    if selos:
        chips = (
            '<div class="selos">'
            + "".join(
                f'{selo(t)}<span class="qtd">{numero(selos.get(t, 0))}</span>'
                for t in ("novato", "reeleito", "retorno")
                if selos.get(t)
            )
            + SEM_SELO.format(numero(sum(partidos.values()) - sum(selos.values())))
            + "</div>"
        )
    return (
        f'<div class="card casa"><h3>{e(titulo)}</h3><p class="sub">{e(subtitulo)}</p>'
        f"{hemiciclo(dict(partidos), rotulo) if rotulo else faixa(dict(partidos), pendentes)}{chips}</div>"
    )


def contar(eleitos: list[Row], cargos: tuple[str, ...]) -> Counter[str]:
    return Counter(r["partido"] or "Sem partido" for r in eleitos if r["cargo"] in cargos)


def brasil(ano: int, eleitos: list[Row], situacao: list[Row], capturado: date | None) -> str:
    governos = [s for s in situacao if s["cargo"] == "Governador"]
    pend = sum(int(s["qtd_pendentes"]) for s in governos)
    presidente = [r for r in eleitos if r["cargo"] == "Presidente"]
    pres_card = (
        f'<div class="card"><h3>Presidente da República</h3><p><a href="pessoa/{endereco(presidente[0]["id_candidatura"])}.html">'
        f"{e(presidente[0]['nome_urna'])}</a>, {e(presidente[0]['partido'])}.</p></div>"
        if presidente
        else '<div class="card aguardando"><h3>Presidente da República</h3><p>Aguardando o resultado do 2º turno. '
        "Quando o TSE divulgar, o eleito aparece aqui.</p></div>"
    )
    selos_dep = Counter(
        r["tipo_mandato"] for r in eleitos if r["cargo"] == "Deputado federal" and r["tipo_mandato"]
    )
    selos_sen = Counter(r["tipo_mandato"] for r in eleitos if r["cargo"] == "Senador" and r["tipo_mandato"])
    legislativo_estadual = contar(eleitos, ("Deputado estadual", "Deputado distrital"))
    corpo = [
        faixa_de_titulo(
            "A composição do poder no Brasil",
            "Quem está no cargo",
            f"Os eleitos nas eleições gerais de {ano}, pelos três poderes, de cima para baixo: federal, estadual e municipal.",
            aviso_provisorio(capturado),
        ),
        seletor_de_estado(),
        '<div class="secao">',
        banda(*PODERES[0]),
        esfera("Federal", "Todo o Brasil"),
        pres_card,
        esfera("Estadual", "27 estados e o Distrito Federal"),
        casa(
            "Governos estaduais",
            f"{len(governos)} estados, {len(governos) - pend} já definidos",
            contar(eleitos, ("Governador",)),
            pend,
        ),
        esfera("Municipal", "5.570 cidades"),
        em_construcao("Prefeitos", "Quem comanda cada cidade."),
        banda(*PODERES[1]),
        esfera("Federal", "Congresso Nacional, em Brasília"),
        casa(
            "Câmara dos Deputados",
            f"{sum(1 for r in eleitos if r['cargo'] == 'Deputado federal')} eleitos em {ano}",
            contar(eleitos, ("Deputado federal",)),
            0,
            selos_dep,
            "deputados",
        ),
        casa(
            "Senado Federal",
            f"{sum(1 for r in eleitos if r['cargo'] == 'Senador')} cadeiras em disputa em {ano}",
            contar(eleitos, ("Senador",)),
            0,
            selos_sen,
            "senadores",
        ),
        esfera("Estadual", "Capitais dos estados"),
        casa(
            "Assembleias Legislativas e Câmara Legislativa",
            f"{sum(legislativo_estadual.values())} eleitos em {ano}",
            legislativo_estadual,
            rotulo="deputados",
        ),
        esfera("Municipal", "5.570 cidades"),
        em_construcao("Câmaras de vereadores", "Quem faz as leis de cada cidade."),
        banda(*PODERES[2]),
        esfera("Federal", "Tribunais superiores, em Brasília"),
        em_construcao(
            "Supremo Tribunal Federal e tribunais superiores",
            "Os 11 ministros do STF e os ministros do STJ, TST, TSE e STM.",
        ),
        esfera("Estadual", "Tribunais de cada estado"),
        em_construcao("Tribunais de Justiça", "Os desembargadores de cada estado."),
        "</div>",
        legenda_dos_selos(),
    ]
    return pagina("Brasil", "\n".join(corpo), "brasil")


def seletor_de_estado() -> str:
    regioes = ["Todas", "Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
    botoes = "".join(
        f'<button type="button" class="filtro" data-regiao="{r}" aria-pressed="{"true" if r == "Todas" else "false"}">{r}</button>'
        for r in regioes
    )
    itens = "".join(
        f'<li data-nome="{e(nome.lower())} {uf.lower()}" data-regiao="{regiao}"><a href="estado/{uf}.html">'
        f'<b>{e(nome)}</b> <span>{uf}</span><i aria-hidden="true">&#8250;</i></a></li>'
        for uf, (nome, regiao) in sorted(UFS.items(), key=lambda kv: kv[1][0])
    )
    return (
        '<section class="secao seletor"><h2>Encontre seu estado</h2><div class="card">'
        '<label class="so-leitor" for="busca-estado">Buscar estado</label>'
        '<input id="busca-estado" type="search" placeholder="Digite o nome do estado" autocomplete="off">'
        f'<div class="filtros" role="group" aria-label="Região">{botoes}</div>'
        f'<ul class="lista-estados" id="estados">{itens}</ul></div></section>'
    )


def legenda_dos_selos() -> str:
    return (
        '<section class="secao"><h2>Como ler</h2><div class="card legenda-selos">'
        f"<p>{selo('novato')} Primeiro mandato nesta casa (Câmara ou Senado).</p><p>{selo('reeleito')} Já estava no cargo e foi eleito de novo.</p>"
        f"<p>{selo('retorno')} Já teve mandato, mas estava fora.</p>"
        '<p><span class="selo semselo">Sem selo</span> Não conseguimos ligar a pessoa a um mandato anterior. '
        "Isso não quer dizer que seja novata: simplesmente não afirmamos nada.</p>"
        '<p><span class="selo provisorio">Provisório</span> Só é confirmado na diplomação.</p></div></section>'
    )


def cartao_de_pessoa(r: Row) -> str:
    detalhe = f"{e(r['partido'])} &middot; {numero(r['qtd_votos'])} votos"
    return (
        f'<a class="card pessoa" href="../pessoa/{endereco(r["id_candidatura"])}.html" data-nome="{e(str(r["nome_urna"]).lower())}" '
        f'data-partido="{e(str(r["partido"]).lower())}" data-tipo="{e(r["tipo_mandato"] or "sem")}" '
        f'data-votos="{r["qtd_votos"] or 0}">{foto(r["foto_url"], r["nome_urna"], 60)}'
        f'<span class="dados"><b>{e(r["nome_urna"])}</b><span>{detalhe}</span>{selo(r["tipo_mandato"])}</span>'
        '<i aria-hidden="true">&#8250;</i></a>'
    )


def botoes_de_tipo(eleitos: list[Row]) -> str:
    """Um botão por tipo que existe na lista, com a contagem; quem não tem selo vira `Sem selo`."""
    nomes = (("novato", "Novatos"), ("reeleito", "Reeleitos"), ("retorno", "Retorno"), ("sem", "Sem selo"))
    contagem = Counter(r["tipo_mandato"] or "sem" for r in eleitos)
    return "".join(
        f'<button type="button" class="filtro" data-tipo="{t}" aria-pressed="false">{nome} ({contagem[t]})</button>'
        for t, nome in nomes
        if contagem[t]
    )


def lista_filtravel(eleitos: list[Row], com_selos: bool) -> str:
    controles = (
        '<div class="card controles"><label class="so-leitor" for="busca">Buscar por nome ou partido</label>'
        '<input id="busca" type="search" placeholder="Buscar por nome ou partido" autocomplete="off">'
    )
    if com_selos:
        controles += (
            '<div class="filtros" role="group" aria-label="Filtrar">'
            '<button type="button" class="filtro" data-tipo="" aria-pressed="true">Todos</button>'
            + botoes_de_tipo(eleitos)
            + "</div>"
        )
    controles += (
        '<div class="filtros" role="group" aria-label="Ordenar"><span>Ordenar por</span>'
        '<button type="button" class="filtro" data-ordem="nome" aria-pressed="true">Nome</button>'
        '<button type="button" class="filtro" data-ordem="votos" aria-pressed="false">Votos</button>'
        '<button type="button" class="filtro" data-ordem="partido" aria-pressed="false">Partido</button></div>'
        '<p class="contagem" aria-live="polite"></p></div>'
    )
    return (
        f'<div class="lista" data-filtravel>{controles}<div class="itens">'
        + "".join(cartao_de_pessoa(r) for r in eleitos)
        + "</div></div>"
    )


def estado(uf: str, ano: int, eleitos: list[Row], situacao: list[Row], capturado: date | None) -> str:
    nome, _ = UFS[uf]
    doestado = [r for r in eleitos if r["uf"] == uf]
    por_cargo = {c: [r for r in doestado if r["cargo"] == c] for c in (*EXECUTIVO, *LEGISLATIVO)}
    gov = por_cargo["Governador"]
    gov_html = (
        cartao_de_pessoa(gov[0])
        if gov
        else '<div class="card aguardando"><h3>Aguardando o 2º turno</h3><p>Os dois candidatos ainda disputam. '
        "Quando o TSE divulgar o resultado, o eleito aparece aqui.</p></div>"
    )
    deputados = por_cargo["Deputado federal"]
    estaduais = [*por_cargo["Deputado estadual"], *por_cargo["Deputado distrital"]]
    corpo = [
        faixa_de_titulo(
            "Estado",
            f"Quem está no cargo em {nome}",
            f"Os três poderes no estado. Mostramos os eleitos em {ano}, que assumem em {ano + 1}.",
            aviso_provisorio(capturado),
        ),
        '<div class="secao">',
        banda(*PODERES[0][:3]),
        esfera("Estadual", "No estado"),
        "<h3>Governador</h3>",
        gov_html,
        esfera("Municipal", "Cidades do estado"),
        em_construcao("Prefeitos", "Quem comanda cada cidade do estado."),
        banda(*PODERES[1][:3]),
        esfera("Federal", "Representam o estado em Brasília"),
        "<h3>Senadores</h3>",
        "".join(cartao_de_pessoa(r) for r in por_cargo["Senador"])
        or '<p class="nota">Sem senadores eleitos neste ano.</p>',
        f"<h3>Deputados federais ({len(deputados)})</h3>",
        casa(
            "Bancada federal por partido",
            f"{len(deputados)} cadeiras de {nome}",
            contar(doestado, ("Deputado federal",)),
            rotulo="deputados",
        ),
        lista_filtravel(deputados, True),
        esfera("Estadual", "Assembleia Legislativa"),
        f"<h3>Deputados estaduais e distritais ({len(estaduais)})</h3>",
        casa(
            "Assembleia por partido",
            f"{len(estaduais)} cadeiras de {nome}",
            contar(doestado, ("Deputado estadual", "Deputado distrital")),
            rotulo="deputados",
        ),
        lista_filtravel(estaduais, False),
        esfera("Municipal", "Cidades do estado"),
        em_construcao("Vereadores", "Os eleitos de cada cidade do estado."),
        banda(*PODERES[2][:3]),
        esfera("Estadual", "Tribunal de Justiça e Tribunal Regional Eleitoral"),
        em_construcao(
            "Tribunais do estado",
            "Os desembargadores do Tribunal de Justiça e do Tribunal Regional Eleitoral. Não são eleitos.",
        ),
        "</div>",
        legenda_dos_selos(),
    ]
    return pagina(
        f"Quem está no cargo em {nome}",
        "\n".join(corpo),
        "brasil",
        raiz="../",
        descricao=f"Os eleitos de {nome} em {ano}, pelos três poderes.",
    )


def linha_do_tempo(itens: list[tuple[str, str, str, str]]) -> str:
    """Cada item: tipo (proximo, atual, mandato, candidatura), título, linha 1 e linha 2."""
    return (
        '<ol class="tempo">'
        + "".join(
            f'<li class="{tipo}"><span class="ponto"></span><div><b>{e(titulo)}</b><span>{e(a)}</span><small>{e(b)}</small></div></li>'
            for tipo, titulo, a, b in itens
        )
        + "</ol>"
    )


def ficha(
    r: Row, hoje: date, mandatos_da_pessoa: list[Row], candidaturas_da_pessoa: list[Row], desde: date | None
) -> str:
    cargo = r["cargo"]
    anos = 8 if cargo == "Senador" else 4
    inicio = (
        r["ano_eleicao"] + 1
    )  # a posse é no início do ano seguinte; a data exata não vem de fonte confiável
    itens: list[tuple[str, str, str, str]] = [
        (
            "proximo",
            "Próximo mandato",
            f"A partir de {inicio}, por {anos} anos",
            f"Termina no início de {inicio + anos}. Eleito em {r['ano_eleicao']}, resultado provisório.",
        )
    ]
    for m in mandatos_da_pessoa:
        em_curso = m["dt_fim"] is None or m["dt_fim"] >= hoje
        itens.append(
            (
                "atual" if em_curso else "mandato",
                "Mandato atual" if em_curso else f"Mandato como {str(m['cargo']).lower()}",
                f"{mes_ano(m['dt_inicio'])} a {mes_ano(m['dt_fim'])}",
                f"Fonte: {'Senado Federal' if m['casa'] == 'Senado Federal' else 'Câmara dos Deputados'}.",
            )
        )
    for c in candidaturas_da_pessoa:
        if c["ano_eleicao"] == r["ano_eleicao"] or str(c["resultado"] or "").lower().startswith("eleito"):
            continue
        itens.append(
            (
                "candidatura",
                f"Candidatura em {c['ano_eleicao']}",
                f"{c['cargo']}, {str(c['resultado'] or 'resultado não informado').lower()}",
                f"Pelo {c['partido']}." if c["partido"] else "",
            )
        )
    if r["tipo_mandato"] == "novato":  # pessoa ligada, sem mandato anterior na casa
        sem_tempo, sem_tempo_nota = "Ainda não tomou posse", f"A posse é em {inicio}."
    elif cargo in ("Deputado federal", "Senador"):
        sem_tempo = "Histórico de mandatos não confirmado"
        sem_tempo_nota = "Não ligamos esta pessoa a um mandato na Câmara ou no Senado. Isso não quer dizer que seja novata."
    else:
        sem_tempo = "Histórico de mandatos não disponível"
        sem_tempo_nota = "A base só tem os mandatos da Câmara e do Senado."
    tempo_no_cargo = (
        f'<p class="grande">{tempo(desde, hoje)}</p><small>Sem interrupção, desde {mes_ano(desde)}.</small>'
        if desde
        else f'<p class="grande cinza">{sem_tempo}</p><small>{sem_tempo_nota}</small>'
    )
    casa_do_cargo = "no Senado Federal" if cargo == "Senador" else "na Câmara dos Deputados"
    outra_casa = any(
        m["casa"] != ("Senado Federal" if cargo == "Senador" else "Câmara dos Deputados")
        for m in mandatos_da_pessoa
    )
    aviso_novato = (
        '<div class="card destaque-novato">'
        + selo("novato")
        + f"<p>Primeiro mandato {casa_do_cargo}."
        + (
            " Já exerceu mandato na outra casa do Congresso, como mostra a linha do tempo."
            if outra_casa
            else ""
        )
        + "</p></div>"
        if r["tipo_mandato"] == "novato"
        else ""
    )
    campanha = "".join(
        f'<div class="card numero"><span>{rotulo}</span><b title="{e(exato)}">{texto}</b><small>{fonte}</small></div>'
        for rotulo, texto, exato, fonte in (
            ("Bens declarados", reais(r["valor_bens"]), r["valor_bens"], "TSE"),
            (
                "Votos",
                numero(r["qtd_votos"]),
                "",
                f"{percentual(r['percentual_votos_nominais'])} dos válidos",
            ),
            ("Receitas", reais(r["valor_receitas"]), r["valor_receitas"], "Prestação de contas"),
            ("Despesas", reais(r["valor_despesas"]), r["valor_despesas"], "Prestação de contas"),
        )
    )
    corpo = [
        '<section class="heroi ficha">',
        f'<a class="voltar" href="../estado/{e(r["uf"])}.html">&larr; {e(UFS.get(r["uf"], (r["uf"],))[0])}</a>',
        f'<div class="cabeca">{foto(r["foto_url"], r["nome_urna"], 104)}<div><h1>{e(r["nome_urna"])}</h1>'
        f'<p>{e(cargo)} &middot; {e(r["uf"])}</p><p class="partido">Partido {e(r["partido"])}</p></div></div>'
        f'<div class="selos">{selo(r["tipo_mandato"])}<span class="selo provisorio">Resultado provisório</span></div></section>',
        '<div class="secao">',
        aviso_novato,
        f'<h2>Tempo no cargo e mandatos</h2><div class="card">{tempo_no_cargo}{linha_do_tempo(itens)}'
        '<p class="nota">Mandato exercido, mandato que vai começar e candidatura sem mandato aparecem com marcas diferentes. '
        "Só temos o histórico de mandatos da Câmara e do Senado.</p></div>",
        f'<h2>A campanha de {r["ano_eleicao"]}</h2><div class="numeros">{campanha}</div>'
        '<p class="nota">Quando o dado não foi entregue ao TSE, mostramos Sem dado, nunca zero.</p>',
        f'<p class="nota">Fonte: <a href="{e(r["fonte_url"])}">TSE, candidaturas {r["ano_eleicao"]}</a>, capturado em {data_curta(r["dt_captura"])}. '
        'Veja <a href="../como-calculamos.html">como calculamos</a>.</p>',
        "</div>",
    ]
    return pagina(f"{r['nome_urna']}, {cargo}", "\n".join(corpo), "brasil", raiz="../")
