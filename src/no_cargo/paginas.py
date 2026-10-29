"""As páginas do site, como texto HTML. Cada função devolve a página inteira; os links são relativos à pasta da página."""

import re
import unicodedata
from collections import Counter
from datetime import date

from no_cargo import seo
from no_cargo.dados import CARGOS, EXECUTIVO, LEGISLATIVO, Row
from no_cargo.formato import (
    arquivo_da_ficha,
    data_curta,
    e,
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

NAV = (
    ("inicio", "Início", "index.html"),
    ("pessoas", "Pessoas", "pessoas.html"),
    ("cargos", "Cargos", "cargos.html"),
    ("como", "Origens", "como-calculamos.html"),
)
SITE_MAE = "https://codigo-publico-brasil.github.io"
ICONE_GITHUB = "M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"
REPO = "https://github.com/codigo-publico-brasil/no-cargo"
FONTES = (
    ("TSE", "https://dadosabertos.tse.jus.br"),
    ("Câmara", "https://dadosabertos.camara.leg.br"),
    ("Senado", "https://www12.senado.leg.br/dados-abertos"),
)


def pagina(
    titulo: str,
    corpo: str,
    ativa: str,
    raiz: str = "",
    descricao: str = "",
    caminho: str | None = None,
    schema: list[dict[str, object]] | None = None,
) -> str:
    """A página inteira. Com `caminho` (relativo à raiz do site), leva canônico, cartões de compartilhamento e dados estruturados."""
    menu = "".join(
        f'<a href="{raiz}{href}"{' aria-current="page"' if chave == ativa else ""}>{nome}</a>'
        for chave, nome, href in NAV
    )
    fontes = " &middot; ".join(f'<a href="{url}">{nome}</a>' for nome, url in FONTES)
    descricao = descricao or "Quem ocupa o poder no Brasil, pelos três poderes, com a fonte oficial ao lado."
    busca = seo.cabecalho(titulo, descricao, caminho, schema) if caminho is not None else ""
    correcao = seo.link_de_correcao(titulo, caminho or "")
    return (
        '<!doctype html>\n<html lang="pt-BR" data-theme="light">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{e(titulo)} | No Cargo</title>\n"
        f'<meta name="description" content="{e(descricao)}">\n{busca}'
        f'<link rel="icon" href="{raiz}no-cargo.svg" type="image/svg+xml">\n'
        f'<link rel="stylesheet" href="{raiz}tokens.css">\n<link rel="stylesheet" href="{raiz}style.css">\n</head>\n<body>\n'
        f'<header class="topo"><div class="miolo"><a class="marca" href="{raiz}index.html" aria-label="No Cargo, página inicial">'
        f'<img src="{raiz}no-cargo.svg" alt="" width="32" height="32">'
        '<span class="marca-nome">No Cargo</span></a>'
        f'<nav class="nav" aria-label="Principal">{menu}</nav>'
        f'<div class="acoes"><a class="gh" href="{REPO}" aria-label="Código do No Cargo no GitHub" title="Código do No Cargo no GitHub">'
        f'<svg viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" d="{ICONE_GITHUB}"/></svg></a></div></div></header>\n<div class="faixa-cores"></div>\n'
        f"<main>\n{corpo}\n</main>\n"
        '<footer class="rodape"><div><b>No Cargo</b>'
        f'<p>Um projeto do <a href="{SITE_MAE}">Código Público Brasil</a>. Código sob AGPL-3.0; dados curados sob CC BY 4.0.</p>'
        f"<p>Dados oficiais: {fontes}.</p>"
        f'<p class="links"><a href="{raiz}index.html">Início</a><a href="{raiz}cargos.html">Entenda os cargos</a><a href="{raiz}como-calculamos.html">Como calculamos e de onde vêm os dados</a>'
        f'<a href="{correcao}">Encontrou um erro? Abra uma issue &#8599;</a><a href="{REPO}">Código no GitHub &#8599;</a></p></div></footer>\n'
        + tag_em_construcao(raiz, correcao)
        + f'<script src="{raiz}app.js" defer></script>\n</body>\n</html>\n'
    )


def nao_encontrada() -> str:
    """A página 404 do GitHub Pages: leva de volta ao início e à lista de pessoas. Fora do índice dos buscadores."""
    corpo = (
        '<section class="heroi"><span class="sobretitulo">404</span><h1>Esta página não existe</h1>'
        "<p>O endereço pode ter mudado. Procure a pessoa pelo nome ou volte ao início.</p></section>"
        '<div class="secao"><p><a href="/pessoas.html">Todas as pessoas eleitas</a> &middot; <a href="/">Início</a> &middot; '
        '<a href="/como-calculamos.html">Como calculamos</a></p></div>'
    )
    html = pagina("Página não encontrada", corpo, "", raiz="/")
    return html.replace("<head>\n", '<head>\n<meta name="robots" content="noindex">\n', 1)


def faixa_de_titulo(chave: str, titulo: str, subtitulo: str, extra: str = "") -> str:
    return (
        f'<section class="heroi"><span class="sobretitulo">{e(chave)}</span><h1>{e(titulo)}</h1>'
        f"<p>{e(subtitulo)}</p>{extra}</section>"
    )


def migalhas(itens: list[tuple[str, str | None]]) -> str:
    """Onde a pessoa está e como voltar: `(nome, link)`; o último item, sem link, é a página atual."""
    partes = [
        f'<a href="{e(link)}">{e(nome)}</a>' if link else f'<span aria-current="page">{e(nome)}</span>'
        for nome, link in itens
    ]
    return (
        '<nav class="migalhas" aria-label="Você está em">'
        + '<span aria-hidden="true">/</span>'.join(partes)
        + "</nav>"
    )


def aviso_provisorio(capturado: date | None) -> str:
    return (
        '<p class="aviso"><span class="selo provisorio">Resultado provisório</span> '
        f"TSE, capturado em {data_curta(capturado)}. O resultado só é confirmado na diplomação.</p>"
    )


ID_DO_PODER = {"1": "executivo", "2": "legislativo", "3": "judiciario"}


def indice_dos_poderes() -> str:
    return (
        '<nav class="indice" aria-label="Nesta página">'
        + "".join(
            f'<a href="#poder-{ID_DO_PODER[n]}">{nome.removeprefix("Poder ")}</a>' for n, nome, *_ in PODERES
        )
        + "</nav>"
    )


def tag_em_construcao(raiz: str, correcao: str) -> str:
    """A tag que flutua no canto de toda página; aberta, diz o que falta e que os dados ainda estão em validação (sem JavaScript)."""
    return (
        '<details class="obra-flutuante"><summary>Em construção</summary><div>'
        "<p><b>Este site está em construção e os dados ainda estão em validação.</b> Pode haver erros e lacunas.</p>"
        "<p>Prefeitos, vereadores e o Judiciário ainda não aparecem aqui. O que já está no site vem de fonte oficial, "
        "com a data de captura ao lado.</p>"
        f'<p><a href="{raiz}como-calculamos.html">Como calculamos</a> &middot; <a href="{correcao}">Encontrou um erro?</a></p>'
        "</div></details>\n"
    )


def banda(numero_: str, nome: str, descricao: str, quem: str = "") -> str:
    return (
        f'<div class="poder" id="poder-{ID_DO_PODER[numero_]}"><h2>{e(nome)}</h2>'
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


def _card_do_presidente(r: Row) -> str:
    """Foto, partido e votos de quem foi eleito presidente, com link para a ficha."""
    return (
        '<div class="card presidente">'
        + foto(r["foto_url"], r["nome_urna"], 88, r.get("foto_local"))
        + f"<div><h3>Presidente da República</h3><p><b>{e(r['nome_urna'])}</b>, {e(r['partido'])}.</p>"
        f"<p>{numero(r['qtd_votos'])} votos, {percentual(r['percentual_votos_nominais'])} dos válidos. "
        f"Eleito em {r['ano_eleicao']}.</p>"
        f'<p><a href="pessoa/{arquivo_da_ficha(r["nome_urna"], r["id_candidatura"])}">Ver a ficha completa</a></p></div></div>'
    )


def brasil(ano: int, eleitos: list[Row], situacao: list[Row], capturado: date | None) -> str:
    governos = [s for s in situacao if s["cargo"] == "Governador"]
    pend = sum(int(s["qtd_pendentes"]) for s in governos)
    presidente = [r for r in eleitos if r["cargo"] == "Presidente"]
    pres_card = (
        _card_do_presidente(presidente[0])
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
        indice_dos_poderes(),
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
    return pagina(
        "Brasil",
        "\n".join(corpo),
        "inicio",
        descricao=f"Quem foi eleito em {ano}: composição de cada casa por partido, pelos três poderes, com a fonte oficial ao lado.",
        caminho="index.html",
        schema=[seo.site_schema()],
    )


PLURAL = {
    "Presidente": "Presidente", "Governador": "Governadores", "Senador": "Senadores",
    "Deputado federal": "Deputados federais", "Deputado estadual": "Deputados estaduais",
    "Deputado distrital": "Deputados distritais",
}  # fmt: skip


def sem_acento(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto.lower()) if not unicodedata.combining(c))


def nome_do_local(uf: str) -> str:
    """`BR` é o cargo nacional (presidente), que não é um estado."""
    return "Brasil" if uf == "BR" else UFS.get(uf, (uf,))[0]


def linha_de_pessoa(r: Row) -> str:
    nome_uf = nome_do_local(r["uf"])
    return (
        f'<a class="pessoa linha" href="pessoa/{arquivo_da_ficha(r["nome_urna"], r["id_candidatura"])}" data-nome="{e(sem_acento(str(r["nome_urna"])))}" '
        f'data-partido="{e(sem_acento(str(r["partido"])))}" data-cargo="{e(r["cargo"])}" data-uf="{e(r["uf"])}" data-grupo="{"atual" if r.get("em_exercicio") else "novo"}" '
        f'data-local="{e(sem_acento(f"{r['cargo']} {r['uf']} {nome_uf}"))}"><span class="dados"><b>{e(r["nome_urna"])}</b>'
        f"<span>{e(r['cargo'])} &middot; {e(r['uf'] if r['uf'] != 'BR' else 'Brasil')} &middot; {e(r['partido'])} &middot; eleito em {r['ano_eleicao']}</span></span>"
        '<i aria-hidden="true">&#8250;</i></a>'
    )


def pessoas(
    ano: int, eleitos: list[Row], capturado: date | None, em_exercicio: list[Row] | None = None
) -> str:
    """Os eleitos do ano e quem ainda está no mandato de uma eleição anterior, de qualquer cargo e estado, em ordem alfabética; o JS só filtra e ordena."""
    todos = sorted(
        [*eleitos, *(em_exercicio or [])],
        key=lambda r: (sem_acento(str(r["nome_urna"])), str(r["id_candidatura"])),
    )
    contagem = Counter(r["cargo"] for r in todos)
    atuais = len(em_exercicio or [])
    botoes_cargo = (
        '<button type="button" class="filtro" data-cargo="" aria-pressed="true">Todos</button>'
        + "".join(
            f'<button type="button" class="filtro" data-cargo="{e(c)}" aria-pressed="false">{PLURAL[c]} ({numero(contagem[c])})</button>'
            for c in CARGOS
            if contagem[c]
        )
    )
    controles = (
        '<div class="card controles"><label class="so-leitor" for="busca">Buscar por nome, partido ou estado</label>'
        '<input id="busca" type="search" placeholder="Nome, partido ou estado" autocomplete="off">'
        f'<div class="filtros" role="group" aria-label="Situação">'
        '<button type="button" class="filtro" data-grupo="" aria-pressed="true">Todos</button>'
        f'<button type="button" class="filtro" data-grupo="novo" aria-pressed="false">Eleitos em {ano} ({numero(len(eleitos))})</button>'
        f'<button type="button" class="filtro" data-grupo="atual" aria-pressed="false">Em mandato, eleitos antes ({numero(atuais)})</button></div>'
        f'<div class="filtros" role="group" aria-label="Cargo">{botoes_cargo}</div>'
        '<div class="filtros" role="group" aria-label="Ordenar"><span>Ordenar por</span>'
        '<button type="button" class="filtro" data-ordem="nome" aria-pressed="true">Nome</button>'
        '<button type="button" class="filtro" data-ordem="uf" aria-pressed="false">Estado</button>'
        '<button type="button" class="filtro" data-ordem="partido" aria-pressed="false">Partido</button></div>'
        '<p class="contagem" aria-live="polite"></p></div>'
    )
    corpo = [
        faixa_de_titulo(
            "Pessoas · todo o Brasil",
            "Todas as pessoas eleitas",
            f"Quem foi eleito em {ano} e quem ainda está no mandato de uma eleição anterior, de todos os cargos e estados, em ordem alfabética. Procure por nome, partido ou estado.",
            aviso_provisorio(capturado),
        ),
        f'<div class="secao"><div class="lista" data-filtravel>{controles}<div class="itens lista-linhas">'
        + "".join(linha_de_pessoa(r) for r in todos)
        + "</div></div></div>",
    ]
    return pagina(
        "Todas as pessoas eleitas",
        chr(10).join(corpo),
        "pessoas",
        descricao=f"As {numero(len(todos))} pessoas eleitas em {ano} ou ainda no mandato de eleições anteriores, de todos os cargos e estados.",
        caminho="pessoas.html",
    )


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
        f'<ul class="lista-estados" id="estados">{itens}</ul></div>'
        '<p class="nota">Procura uma pessoa, de qualquer estado? <a href="pessoas.html">Veja todas as pessoas eleitas</a>.</p></section>'
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
        f'<a class="card pessoa" href="../pessoa/{arquivo_da_ficha(r["nome_urna"], r["id_candidatura"])}" data-nome="{e(str(r["nome_urna"]).lower())}" '
        f'data-partido="{e(str(r["partido"]).lower())}" data-tipo="{e(r["tipo_mandato"] or "sem")}" '
        f'data-votos="{r["qtd_votos"] or 0}">{foto(r["foto_url"], r["nome_urna"], 60, r.get("foto_local"), "../")}'
        f'<span class="dados"><b>{e(r["nome_urna"])}</b><span>{detalhe}</span>{selo(r["tipo_mandato"], r["cargo"])}</span>'
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


def lista_filtravel(eleitos: list[Row], com_selos: bool, titulo: str) -> str:
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
        f'<details class="recolhivel"><summary>{e(titulo)} ({len(eleitos)}): buscar e ver a lista</summary>'
        f'<div class="lista" data-filtravel>{controles}<div class="itens">'
        + "".join(cartao_de_pessoa(r) for r in eleitos)
        + "</div></div></details>"
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
        migalhas([("Brasil", "../index.html"), (nome, None)]),
        faixa_de_titulo(
            f"Estado · {uf}",
            nome,
            f"Quem está no cargo. Mostramos os eleitos em {ano}, que assumem em {ano + 1}.",
            aviso_provisorio(capturado),
        ),
        indice_dos_poderes(),
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
        lista_filtravel(deputados, True, "Deputados federais"),
        esfera("Estadual", "Assembleia Legislativa"),
        f"<h3>Deputados estaduais e distritais ({len(estaduais)})</h3>",
        casa(
            "Assembleia por partido",
            f"{len(estaduais)} cadeiras de {nome}",
            contar(doestado, ("Deputado estadual", "Deputado distrital")),
            rotulo="deputados",
        ),
        lista_filtravel(estaduais, False, "Deputados estaduais e distritais"),
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
        "",
        raiz="../",
        descricao=f"Governador, senadores e deputados eleitos em {nome} em {ano}, com histórico, selo e a fonte oficial.",
        caminho=f"estado/{uf}.html",
        schema=[seo.migalhas([("Brasil", "index.html"), (nome, f"estado/{uf}.html")])],
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


def vazio_ou(valor: str | None) -> str:
    return e(valor) if valor else "Sem dado"


REDES = {
    "facebook.com": "Facebook", "instagram.com": "Instagram", "twitter.com": "X", "x.com": "X",
    "youtube.com": "YouTube", "tiktok.com": "TikTok", "linkedin.com": "LinkedIn", "threads.net": "Threads",
    "t.me": "Telegram", "kwai.com": "Kwai",
}  # fmt: skip


def nome_do_link(url: str) -> str:
    """`https://www.instagram.com/ana/?hl=pt` vira `Instagram`; endereço que não é de rede conhecida mostra só o domínio."""
    dominio = url.split("//", 1)[1].split("/", 1)[0].split("?", 1)[0].removeprefix("www.").removeprefix("m.")
    return REDES.get(dominio, dominio)


def links_oficiais(valor: str | None) -> str:
    """Um ou mais endereços web que a fonte informa (separados por vírgula, ponto e vírgula ou espaço), cada um com um nome curto.
    O endereço inteiro vai no `title`. Só `http` e `https` viram link; qualquer outra coisa que a fonte traga não é clicável."""
    urls = [u for u in re.split(r"[,;\s]+", valor or "") if u.startswith(("http://", "https://"))]
    if not urls:
        return "Sem dado"
    return "".join(
        f'<a class="curto" href="{e(u)}" title="{e(u)}" rel="noopener noreferrer">{e(nome_do_link(u))}</a>'
        for u in urls
    )


def grade(
    linhas: tuple[tuple[str, str], ...],
    largos: tuple[str, ...] = (),
    numeros: tuple[str, ...] = (),
    duas: bool = False,
) -> str:
    """Rótulo pequeno em cima e valor embaixo, em colunas (3 no computador, 2 no celular); `Sem dado` aparece apagado.
    Os rótulos em `largos` ocupam a linha inteira."""

    def classe(rotulo: str, valor: str) -> str:
        nomes = [
            "vazio" if "Sem dado" in valor and "<" not in valor else "",
            "num" if rotulo in numeros else "",
        ]
        return f' class="{" ".join(n for n in nomes if n)}"' if any(nomes) else ""

    return (
        f'<dl class="grade{" duas" if duas else ""}">'
        + "".join(
            f"<div{' class=largo' if rotulo in largos else ''}><dt>{rotulo}</dt><dd{classe(rotulo, valor)}>{valor}</dd></div>"
            for rotulo, valor in linhas
        )
        + "</dl>"
    )


def sobre_a_pessoa(r: Row) -> str:
    """Quem é, no bloco do título: o nome completo vem do TSE; o resto, do cadastro da Câmara ou do Senado (só quem já é pessoa do projeto)."""
    casa = {"camara": "Câmara dos Deputados", "senado": "Senado Federal"}.get(str(r["fonte_cadastro"]))
    naturalidade = ", ".join(x for x in (r["municipio_nascimento"], r["uf_nascimento"]) if x)
    profissoes = ", ".join(x.strip() for x in str(r["profissoes"] or "").split(";") if x.strip())
    # quem não tem cadastro usa o que o TSE registra: a ocupação declarada e a UF de nascimento (o TSE não dá o município)
    profissao_tse = not profissoes and bool(r.get("ocupacao"))
    if profissao_tse:
        profissoes = str(r["ocupacao"]).capitalize()
    uf_tse = str(r.get("uf_nascimento_tse") or "")
    estado_tse = not naturalidade and uf_tse in UFS
    if estado_tse:
        naturalidade = UFS[uf_tse][0]
    linhas = (
        ("Nome completo", vazio_ou(r["nome_civil"] or r["nome"])),
        ("Nascimento", data_curta(r["dt_nascimento"]) if r["dt_nascimento"] else "Sem dado"),
        ("Naturalidade", vazio_ou(naturalidade)),
        ("Profissões", vazio_ou(profissoes)),
        ("Site", links_oficiais(r["site_url"])),
        ("Rede social", links_oficiais(r["rede_social_url"])),
    )
    capturado = f", capturado em {data_curta(r['dt_captura_cadastro'])}" if r["dt_captura_cadastro"] else ""
    do_tse = [
        x
        for x, vem in (
            ("nome completo", not (casa and r["nome_civil"])),
            ("profissão", profissao_tse),
            ("estado de nascimento", estado_tse),
        )
        if vem
    ]
    tse = f"{', '.join(do_tse[:-1])} e {do_tse[-1]}" if len(do_tse) > 1 else "".join(do_tse)
    de_tse = f"{tse.capitalize()}: TSE, capturado em {data_curta(r['dt_captura'])}. " if do_tse else ""
    if not casa:
        do_cadastro = (
            "Os demais dados: cadastro da Câmara ou do Senado, que ainda não está ligado a esta pessoa."
        )
    else:
        do_cadastro = f"{'Os demais dados' if do_tse else 'Fonte'}: cadastro da {casa}{capturado}."
    fonte = de_tse + do_cadastro
    return grade(linhas, largos=("Nome completo",), numeros=("Nascimento",)) + f'<p class="nota">{fonte}</p>'


def ficha(
    r: Row, hoje: date, mandatos_da_pessoa: list[Row], candidaturas_da_pessoa: list[Row], desde: date | None
) -> str:
    cargo = r["cargo"]
    caminho = "pessoa/" + arquivo_da_ficha(r["nome_urna"], r["id_candidatura"])
    anos = 8 if cargo == "Senador" else 4
    inicio = (
        r["ano_eleicao"] + 1
    )  # a posse é no início do ano seguinte; a data exata não vem de fonte confiável
    atual = bool(r.get("em_exercicio"))  # eleito antes e ainda no mandato, fora da lista dos eleitos do ano
    oficial_em_curso = any(m["dt_fim"] is None or m["dt_fim"] >= hoje for m in mandatos_da_pessoa)
    itens: list[tuple[str, str, str, str]]
    if (
        atual
    ):  # o mandato em curso previsto; quem tem mandato na Câmara ou no Senado já o vê abaixo, com a fonte
        itens = (
            []
            if oficial_em_curso
            else [
                (
                    "atual",
                    "Mandato atual",
                    f"De {inicio} a {inicio + anos - 1}, {anos} anos",
                    f"Eleito em {r['ano_eleicao']}. Previsto pelo resultado do TSE, que não registra afastamentos nem suplentes que assumiram.",
                )
            ]
        )
    else:
        itens = [
            (
                "proximo",
                "Próximo mandato",
                f"De {inicio} a {inicio + anos - 1}, {anos} anos",
                f"Eleito em {r['ano_eleicao']}. Os mandatos vão do início ao fim do ano.",
            )
        ]
    passado: list[
        tuple[int, tuple[str, str, str, str]]
    ] = []  # (ano, item): do mais recente para o mais antigo
    for m in mandatos_da_pessoa:
        em_curso = m["dt_fim"] is None or m["dt_fim"] >= hoje
        passado.append(
            (
                m["dt_inicio"].year,
                (
                    "atual" if em_curso else "mandato",
                    "Mandato atual" if em_curso else f"Mandato como {str(m['cargo']).lower()}",
                    f"{mes_ano(m['dt_inicio'])} a {mes_ano(m['dt_fim'])}",
                    f"Fonte: {'Senado Federal' if m['casa'] == 'Senado Federal' else 'Câmara dos Deputados'}.",
                ),
            )
        )
    for c in candidaturas_da_pessoa:
        if c["ano_eleicao"] == r["ano_eleicao"]:
            continue
        eleito = str(c["resultado"] or "").lower().startswith("eleito")
        if eleito and c["cargo"] in ("Deputado federal", "Senador") and mandatos_da_pessoa:
            continue  # o mandato na Câmara ou no Senado já vem dessas casas
        if eleito:  # outros cargos: o TSE diz que foi eleito, e o mandato previsto é o da lei
            duracao = 8 if c["cargo"] == "Senador" else 4
            passado.append(
                (
                    c["ano_eleicao"] + 1,
                    (
                        "mandato",
                        f"Eleito em {c['ano_eleicao']}",
                        f"{c['cargo']}, mandato previsto de {c['ano_eleicao'] + 1} a {c['ano_eleicao'] + duracao}",
                        "Fonte: TSE. O resultado da eleição não registra afastamentos.",
                    ),
                )
            )
            continue
        passado.append(
            (
                c["ano_eleicao"],
                (
                    "candidatura",
                    f"Candidatura em {c['ano_eleicao']}",
                    f"{c['cargo']}, {str(c['resultado'] or 'resultado não informado').lower()}",
                    f"Pelo {c['partido']}." if c["partido"] else "",
                ),
            )
        )
    itens += [item for _, item in sorted(passado, key=lambda x: -x[0])]
    ja_eleito = any(str(c["resultado"] or "").lower().startswith("eleito") for c in candidaturas_da_pessoa)
    em_curso_tse = (
        next(  # eleito antes para este cargo, com o mandato previsto ainda valendo hoje: (início, fim)
            (
                (c["ano_eleicao"] + 1, c["ano_eleicao"] + anos)
                for c in candidaturas_da_pessoa
                if c["cargo"] == cargo
                and c["ano_eleicao"] < r["ano_eleicao"]
                and str(c["resultado"] or "").lower().startswith("eleito")
                and c["ano_eleicao"] + 1 <= hoje.year <= c["ano_eleicao"] + anos
            ),
            None,
        )
    )
    if atual:
        sem_tempo = "Mandato em curso"
        sem_tempo_nota = "Previsto pelo resultado do TSE; o resultado não registra afastamentos nem suplentes que assumiram."
    elif r["tipo_mandato"] == "novato":  # pessoa ligada, sem mandato anterior na casa
        sem_tempo, sem_tempo_nota = "Ainda não tomou posse", f"A posse é em {inicio}."
    elif em_curso_tse:
        sem_tempo = f"No cargo desde {em_curso_tse[0]}"
        sem_tempo_nota = (
            f"Mandato de {em_curso_tse[0]} a {em_curso_tse[1]}, previsto pelo resultado do TSE, que não registra "
            "afastamentos. Mandatos anteriores podem não aparecer."
        )
    elif ja_eleito:
        sem_tempo = "Já foi eleito antes"
        sem_tempo_nota = "Pelas eleições do TSE, ligadas por nome e data de nascimento. O resultado da eleição não registra afastamentos."
    else:
        sem_tempo = "Histórico de mandatos não confirmado"
        sem_tempo_nota = "Ainda não ligamos esta pessoa às eleições e aos mandatos anteriores. Isso não quer dizer que seja novata."
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
        + selo("novato", cargo)
        + f"<p>Primeiro mandato {casa_do_cargo}."
        + (
            " Já exerceu mandato na outra casa do Congresso, como mostra a linha do tempo."
            if outra_casa
            else ""
        )
        + "</p></div>"
        if r["tipo_mandato"] == "novato" and not atual
        else ""
    )
    campanha = grade(
        (
            (
                "Votos",
                f"{numero(r['qtd_votos'])}<small>{percentual(r['percentual_votos_nominais'])} dos válidos</small>",
            ),
            ("Bens declarados", reais(r["valor_bens"])),
            ("Receita da campanha", reais(r["valor_receitas"])),
            ("Gasto da campanha", reais(r["valor_despesas"])),
        ),
        numeros=("Votos", "Bens declarados", "Receita da campanha", "Gasto da campanha"),
        duas=True,
    )
    corpo = [
        migalhas(
            [
                ("Brasil", "../index.html"),
                *([] if r["uf"] == "BR" else [(nome_do_local(r["uf"]), f"../estado/{r['uf']}.html")]),
                (str(r["nome_urna"]), None),
            ]
        ),
        '<section class="heroi ficha">',
        f'<div class="cabeca">{foto(r["foto_url"], r["nome_urna"], 104, r.get("foto_local"), "../")}<div><h1>{e(r["nome_urna"])}</h1>'
        f'<p>{e(cargo)} &middot; {e(r["uf"] if r["uf"] != "BR" else "Brasil")}</p><p class="partido">Partido {e(r["partido"])}</p></div></div>'
        + (
            '<div class="selos"><span class="selo semselo">Mandato em curso</span></div>'
            if atual
            else f'<div class="selos">{selo(r["tipo_mandato"], cargo)}</div>'
        )
        + f"{sobre_a_pessoa(r)}</section>",
        '<div class="secao">',
        aviso_novato,
        f'<h2>Tempo no cargo e mandatos</h2><div class="card">{tempo_no_cargo}{linha_do_tempo(itens)}'
        '<p class="nota">Mandato exercido, mandato que vai começar e candidatura sem mandato aparecem com marcas diferentes. '
        "Os mandatos da Câmara e do Senado vêm dessas casas; as eleições de outros cargos vêm do TSE e não registram afastamentos.</p></div>",
        f'<h2>A campanha de {r["ano_eleicao"]}</h2><div class="card">{campanha}</div>'
        '<p class="nota">Bens: declarados ao TSE. Receita e gasto: prestação de contas ao TSE, com as despesas contratadas. '
        "Quando o dado não foi entregue, mostramos Sem dado, nunca zero.</p>",
        f'<p class="nota">Fonte: <a href="{e(r["fonte_url"])}">TSE, candidaturas {r["ano_eleicao"]}</a>, capturado em {data_curta(r["dt_captura"])}. '
        + ("Foto: TSE, do registro da candidatura. " if r.get("foto_local") else "")
        + f'Veja <a href="../como-calculamos.html">como calculamos</a>. '
        f'Encontrou um erro neste dado? <a href="{seo.link_de_correcao(r["nome_urna"] + ", " + cargo, caminho)}">Abra uma issue</a>.</p>',
        "</div>",
    ]
    estado = nome_do_local(r["uf"])
    onde = "do Brasil" if r["uf"] == "BR" else f"por {estado}"
    return pagina(
        f"{r['nome_urna']}, {cargo}",
        "\n".join(corpo),
        "brasil",
        raiz="../",
        descricao=(
            f"{r['nome_urna']}, {cargo.lower()} {onde} ({r['partido']}), eleição de {r['ano_eleicao']}: "
            "mandatos, candidaturas, votos e campanha, com a fonte oficial."
        ),
        caminho=caminho,
        schema=[
            seo.pessoa_schema(
                r["nome_urna"], cargo, r["partido"], estado, caminho, r["fonte_url"], r["dt_captura"]
            ),
            seo.migalhas(
                [
                    ("Brasil", "index.html"),
                    *([] if r["uf"] == "BR" else [(estado, f"estado/{r['uf']}.html")]),
                    (r["nome_urna"], caminho),
                ]
            ),
        ],
    )
