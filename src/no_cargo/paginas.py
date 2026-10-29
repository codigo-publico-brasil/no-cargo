"""As páginas do site, como texto HTML. Cada função devolve a página inteira; os links são relativos à pasta da página."""

import re
import unicodedata
from collections import Counter
from datetime import date, datetime

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
    ("inicio", "Brasil", "index.html"),
    ("estados", "Estados", "estados.html"),
    ("pessoas", "Pessoas", "pessoas.html"),
    ("cargos", "Cargos", "cargos.html"),
)
SITE_MAE = "https://codigo-publico-brasil.github.io"
ICONE_GITHUB = "M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"
REPO = "https://github.com/codigo-publico-brasil/no-cargo"
FONTES = (
    ("TSE", "https://dadosabertos.tse.jus.br"),
    ("Câmara", "https://dadosabertos.camara.leg.br"),
    ("Senado", "https://www12.senado.leg.br/dados-abertos"),
)


# A base informa o arquivo de cada fonte (um .csv ou .zip que baixa sozinho). O link do site leva à página do
# conjunto de dados, que explica o dado; o endereço do arquivo fica no `title`.
PAGINAS_DAS_FONTES = (
    (r"cdn\.tse\.jus\.br/.*(?:consulta_cand|bem_candidato)_(\d{4})", "https://dadosabertos.tse.jus.br/dataset/candidatos-{}"),
    (r"cdn\.tse\.jus\.br/.*prestacao.*?(\d{4})", "https://dadosabertos.tse.jus.br/dataset/prestacao-de-contas-eleitorais-{}"),
    (r"dadosabertos\.camara\.leg\.br/arquivos/", "https://dadosabertos.camara.leg.br/"),
    (r"legis\.senado\.leg\.br/dadosabertos/", "https://www12.senado.leg.br/dados-abertos"),
)  # fmt: skip


def pagina_da_fonte(url: str) -> str:
    """Do arquivo da fonte para a página do conjunto de dados; sem regra conhecida, o próprio endereço."""
    for padrao, pagina_ in PAGINAS_DAS_FONTES:
        achou = re.search(padrao, url)
        if achou:
            return pagina_.format(*achou.groups())
    return url


def link_da_fonte(url: object, texto: str) -> str:
    """O link de uma fonte oficial: abre a página do conjunto de dados; o arquivo vai no `title`."""
    if not url:
        return e(texto)
    return f'<a href="{e(pagina_da_fonte(str(url)))}" title="Arquivo: {e(url)}">{e(texto)}</a>'


def _links_externos_em_nova_guia(html: str) -> str:
    """Todo link para fora do site (fontes oficiais, redes e sites dos eleitos, repositório) abre em outra guia."""

    def ajusta(m: re.Match[str]) -> str:
        tag = m.group(0)
        if "target=" in tag or seo.SITE in m.group(1):
            return tag
        tag = re.sub(r'\srel="[^"]*"', "", tag)
        return tag[:-1] + ' target="_blank" rel="noopener noreferrer">'

    return re.sub(r'<a\s[^>]*?href="(https?://[^"]+)"[^>]*>', ajusta, html)


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
    return _links_externos_em_nova_guia(
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
        f'<p class="links"><a href="{raiz}index.html">Brasil</a><a href="{raiz}cargos.html">Entenda os cargos</a><a href="{raiz}como-calculamos.html">Origens dos dados</a>'
        f'<a href="{correcao}">Encontrou um erro? Abra uma issue &#8599;</a><a href="{REPO}">Código no GitHub &#8599;</a></p></div></footer>\n'
        + tag_em_construcao(raiz, correcao)
        + f'<script src="{raiz}app.js" defer></script>\n</body>\n</html>\n'
    )


def nao_encontrada() -> str:
    """A página 404 do GitHub Pages: leva de volta ao início e à lista de pessoas. Fora do índice dos buscadores."""
    corpo = (
        '<section class="heroi"><span class="sobretitulo">404</span><h1>Esta página não existe</h1>'
        "<p>O endereço pode ter mudado. Procure a pessoa pelo nome ou volte ao início.</p></section>"
        '<div class="secao"><p><a href="/pessoas.html">Todas as pessoas eleitas</a> &middot; <a href="/">Brasil</a> &middot; '
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


def aviso_provisorio(capturado: date | None, atualizado: datetime | None = None) -> str:
    """Selos do alto da página: o resultado é provisório e quando os dados foram atualizados."""
    quando = (
        f"Atualizado em {data_curta(atualizado)} às {atualizado:%H:%M}"
        if atualizado
        else f"TSE, capturado em {data_curta(capturado)}"
    )
    return (
        '<p class="chips"><span class="selo provisorio">Resultado provisório</span>'
        f'<span class="chip">{quando}</span></p>'
    )


ID_DO_PODER = {"1": "executivo", "2": "legislativo", "3": "judiciario"}


def indice_dos_poderes(sufixo: str = "") -> str:
    return (
        '<nav class="indice" aria-label="Nesta página">'
        + "".join(
            f'<a href="#poder-{ID_DO_PODER[n]}{sufixo}">{nome.removeprefix("Poder ")}</a>'
            for n, nome, *_ in PODERES
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


def banda(numero_: str, nome: str, descricao: str, quem: str = "", sufixo: str = "") -> str:
    return (
        f'<div class="poder" id="poder-{ID_DO_PODER[numero_]}{sufixo}"><h2>{e(nome)}</h2>'
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
    turno = f" &middot; {r['turno']}º turno" if r.get("turno") else ""
    return (
        '<a class="card presidente" href="pessoa/'
        + (r.get("ficha") or arquivo_da_ficha(r["nome_urna"], r["id_candidatura"]))
        + '">'
        + foto(r["foto_url"], r["nome_urna"], 72, r.get("foto_local"))
        + f"<div><h3>Presidente da República</h3><p><b>{e(r['nome_urna'])}</b> &middot; {e(r['partido'])}</p>"
        f"<p>{numero(r['qtd_votos'])} votos &middot; {percentual(r['percentual_votos_validos'])}{turno}</p></div>"
        '<i aria-hidden="true">&#8250;</i></a>'
    )


VISOES = (("hoje", "Hoje"), ("posse", "Depois da posse"))


def seletor_de_visao() -> tuple[str, str]:
    """Os botões de escolha e o controle: a página traz as duas composições e o CSS mostra uma (sem JavaScript)."""
    entradas = "".join(
        f'<input type="radio" name="visao" id="visao-{chave}" class="so-leitor"{" checked" if chave == "hoje" else ""}>'
        for chave, _ in VISOES
    )
    controle = (
        '<div class="visoes" role="group" aria-label="Composição">'
        + "".join(f'<label for="visao-{chave}">{rotulo}</label>' for chave, rotulo in VISOES)
        + "</div>"
    )
    return entradas, controle


def _poderes_do_brasil(linhas: list[Row], sufixo: str, pendentes: int) -> str:
    """Os três poderes com a composição de `linhas`; `sufixo` deixa as âncoras únicas quando há mais de uma visão."""
    governadores = [r for r in linhas if r["cargo"] == "Governador"]
    presidente = [r for r in linhas if r["cargo"] == "Presidente"]
    pres_card = (
        _card_do_presidente(presidente[0])
        if presidente
        else '<div class="card aguardando"><h3>Presidente da República</h3><p>Aguardando o resultado do 2º turno. '
        "Quando o TSE divulgar, o eleito aparece aqui.</p></div>"
    )
    selos_dep = Counter(
        r["tipo_mandato"] for r in linhas if r["cargo"] == "Deputado federal" and r["tipo_mandato"]
    )
    selos_sen = Counter(r["tipo_mandato"] for r in linhas if r["cargo"] == "Senador" and r["tipo_mandato"])
    legislativo_estadual = contar(linhas, ("Deputado estadual", "Deputado distrital"))
    deputados = sum(1 for r in linhas if r["cargo"] == "Deputado federal")
    senadores = sum(1 for r in linhas if r["cargo"] == "Senador")
    partes = [
        indice_dos_poderes(sufixo),
        '<div class="secao">',
        banda(*PODERES[0], sufixo=sufixo),
        esfera("Federal", "Todo o Brasil"),
        pres_card,
        esfera("Estadual", "27 estados e o Distrito Federal"),
        casa(
            "Governos estaduais",
            f"{len(governadores)} governadores" + (f", {pendentes} ainda por definir" if pendentes else ""),
            contar(linhas, ("Governador",)),
            pendentes,
        ),
        esfera("Municipal", "5.570 cidades"),
        em_construcao("Prefeitos", "Quem comanda cada cidade."),
        banda(*PODERES[1], sufixo=sufixo),
        esfera("Federal", "Congresso Nacional, em Brasília"),
        casa(
            "Câmara dos Deputados",
            f"{deputados} deputados",
            contar(linhas, ("Deputado federal",)),
            0,
            selos_dep,
            "deputados",
        ),
        casa(
            "Senado Federal",
            f"{senadores} senadores",
            contar(linhas, ("Senador",)),
            0,
            selos_sen,
            "senadores",
        ),
        esfera("Estadual", "Capitais dos estados"),
        casa(
            "Assembleias Legislativas e Câmara Legislativa",
            f"{sum(legislativo_estadual.values())} deputados",
            legislativo_estadual,
            rotulo="deputados",
        ),
        esfera("Municipal", "5.570 cidades"),
        em_construcao("Câmaras de vereadores", "Quem faz as leis de cada cidade."),
        banda(*PODERES[2], sufixo=sufixo),
        esfera("Federal", "Tribunais superiores, em Brasília"),
        em_construcao(
            "Supremo Tribunal Federal e tribunais superiores",
            "Os 11 ministros do STF e os ministros do STJ, TST, TSE e STM.",
        ),
        esfera("Estadual", "Tribunais de cada estado"),
        em_construcao("Tribunais de Justiça", "Os desembargadores de cada estado."),
        "</div>",
    ]
    return "\n".join(partes)


def brasil(
    ano: int,
    visoes: dict[str, list[Row]],
    situacao: list[Row],
    capturado: date | None,
    atualizado: datetime | None = None,
) -> str:
    """A composição do poder: `visoes` traz quem ocupa os cargos hoje e depois da posse, e a página mostra uma por vez."""
    pendentes = sum(int(s["qtd_pendentes"]) for s in situacao if s["cargo"] == "Governador")
    entradas, controle = seletor_de_visao()
    corpo = [
        entradas,
        faixa_de_titulo(
            "A composição do poder no Brasil",
            "Quem está no cargo",
            "A composição do poder público no Brasil, nos três poderes.",
            aviso_provisorio(capturado, atualizado),
        ),
        controle,
        atalhos_da_home(),
        *(
            f'<div class="visao visao-{chave}">'
            + _poderes_do_brasil(visoes[chave], f"-{chave}", pendentes if chave == "posse" else 0)
            + "</div>"
            for chave, _ in VISOES
        ),
        legenda_dos_selos(),
    ]
    return pagina(
        "Brasil",
        "\n".join(corpo),
        "inicio",
        descricao=f"Quem ocupa o poder no Brasil hoje e depois da posse de {ano + 1}: composição de cada casa por partido, pelos três poderes, com a fonte oficial ao lado.",
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


def _de_onde_veio(r: Row) -> str:
    """`eleito em 2022` ou, para quem está no cargo sem eleição própria, `no cargo desde 2024`."""
    return f"no cargo desde {r['ano_inicio']}" if r.get("sem_eleicao") else f"eleito em {r['ano_eleicao']}"


def linha_de_pessoa(r: Row, em_mandato: bool = False) -> str:
    nome_uf = nome_do_local(r["uf"])
    return (
        f'<a class="pessoa linha" href="pessoa/{arquivo_da_ficha(r["nome_urna"], r["id_candidatura"])}" data-nome="{e(sem_acento(str(r["nome_urna"])))}" '
        f'data-partido="{e(sem_acento(str(r["partido"])))}" data-cargo="{e(r["cargo"])}" data-uf="{e(r["uf"])}" data-tipo="{e(r["tipo_mandato"] or "sem")}" data-grupo="{"atual" if r.get("em_exercicio") else "novo atual" if em_mandato else "novo"}" '
        f'data-local="{e(sem_acento(f"{r['cargo']} {r['uf']} {nome_uf}"))}"><span class="dados"><b>{e(r["nome_urna"])}</b>'
        f"<span>{e(r['cargo'])} &middot; {e(r['uf'] if r['uf'] != 'BR' else 'Brasil')} &middot; {e(r['partido'])} &middot; {_de_onde_veio(r)}</span></span>"
        '<i aria-hidden="true">&#8250;</i></a>'
    )


def pessoas(
    ano: int,
    eleitos: list[Row],
    capturado: date | None,
    em_exercicio: list[Row] | None = None,
    em_mandato: set[int] | None = None,
) -> str:
    """Os eleitos do ano e quem ainda está no mandato de uma eleição anterior, de qualquer cargo e estado, em ordem alfabética; o JS só filtra e ordena."""
    todos = sorted(
        [*eleitos, *(em_exercicio or [])],
        key=lambda r: (sem_acento(str(r["nome_urna"])), str(r["id_candidatura"])),
    )
    contagem = Counter(r["cargo"] for r in todos)
    opcoes_cargo = '<option value="">Todos os cargos</option>' + "".join(
        f'<option value="{e(c)}">{PLURAL[c]} ({numero(contagem[c])})</option>' for c in CARGOS if contagem[c]
    )
    controles = (
        '<div class="card controles"><label class="so-leitor" for="busca">Buscar por nome, partido ou estado</label>'
        '<input id="busca" type="search" placeholder="Buscar por nome, partido ou estado" autocomplete="off">'
        '<div class="segmentos" role="group" aria-label="Situação">'
        '<button type="button" data-grupo="" aria-pressed="true">Todos</button>'
        f'<button type="button" data-grupo="novo" aria-pressed="false">Eleitos em {ano}</button>'
        '<button type="button" data-grupo="atual" aria-pressed="false">Em mandato</button></div>'
        '<div class="selecoes"><label>Cargo<select data-filtro="cargo">' + opcoes_cargo + "</select></label>"
        '<label>Tipo de mandato<select data-filtro="tipo"><option value="">Todos</option>'
        + opcoes_de_tipo(todos)
        + "</select></label>"
        '<label>Ordenar por<select data-filtro="ordem"><option value="nome">Nome</option>'
        '<option value="uf">Estado</option><option value="partido">Partido</option></select></label></div>'
        '<p class="contagem" aria-live="polite"></p></div>'
    )
    corpo = [
        faixa_de_titulo(
            "Pessoas · todo o Brasil",
            "Todas as pessoas eleitas",
            f"Quem foi eleito em {ano} e quem segue no mandato de uma eleição anterior.",
            aviso_provisorio(capturado),
        ),
        f'<div class="secao"><div class="lista" data-filtravel>{controles}<div class="itens lista-linhas">'
        + "".join(linha_de_pessoa(r, r["id_pessoa"] in (em_mandato or set())) for r in todos)
        + "</div></div></div>",
    ]
    return pagina(
        "Todas as pessoas eleitas",
        chr(10).join(corpo),
        "pessoas",
        descricao=f"As {numero(len(todos))} pessoas eleitas em {ano} ou ainda no mandato de eleições anteriores, de todos os cargos e estados.",
        caminho="pessoas.html",
    )


def atalhos_da_home() -> str:
    """Duas portas curtas no alto da home: o resto da página fica para o cenário geral."""
    return (
        '<div class="atalhos">'
        '<a class="card" href="estados.html"><b>Estados</b><span>27 estados e DF</span></a>'
        '<a class="card" href="pessoas.html"><b>Pessoas</b><span>Busca por nome</span></a>'
        "</div>"
    )


def estados(capturado: date | None) -> str:
    """Os 27 estados em grade, por região: cada um é um link; sem busca nem filtro."""
    regioes = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
    blocos = "".join(
        f'<h2 class="regiao">{regiao}</h2><ul class="estados">'
        + "".join(
            f'<li data-nome="{e(sem_acento(nome))} {uf.lower()}"><a href="estado/{uf}.html"><b>{uf}</b><span>{e(nome)}</span></a></li>'
            for uf, (nome, reg) in sorted(UFS.items(), key=lambda kv: kv[1][0])
            if reg == regiao
        )
        + "</ul>"
        for regiao in regioes
    )
    busca = (
        '<div class="busca-estado" hidden><label class="so-leitor" for="busca-estado">Buscar estado</label>'
        '<input id="busca-estado" type="search" placeholder="Digite o nome ou a sigla do estado" autocomplete="off">'
        '<p class="contagem" aria-live="polite"></p></div>'
    )
    corpo = [
        faixa_de_titulo(
            "Estados · todo o Brasil",
            "Escolha um estado",
            "Quem foi eleito em cada estado e no Distrito Federal, pelos três poderes.",
            aviso_provisorio(capturado),
        ),
        f'<div class="secao" id="estados">{busca}{blocos}</div>',
    ]
    return pagina(
        "Estados",
        "\n".join(corpo),
        "estados",
        descricao="Os 27 estados e o Distrito Federal: escolha um para ver quem foi eleito.",
        caminho="estados.html",
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
    detalhe = (
        f"{e(r['partido'])} &middot; {_de_onde_veio(r)}"
        if r.get("sem_eleicao")
        else f"{e(r['partido'])} &middot; {numero(r['qtd_votos'])} votos"
        + ("" if r.get("novo") else f" &middot; eleito em {r['ano_eleicao']}")
    )
    return (
        f'<a class="card pessoa" href="../pessoa/{r.get("ficha") or arquivo_da_ficha(r["nome_urna"], r["id_candidatura"])}" data-nome="{e(str(r["nome_urna"]).lower())}" '
        f'data-partido="{e(str(r["partido"]).lower())}" data-tipo="{e(r["tipo_mandato"] or "sem")}" '
        f'data-grupo="{"novo" if r.get("novo") else "antes"}" '
        f'data-votos="{r["qtd_votos"] or 0}">{foto(r["foto_url"], r["nome_urna"], 60, r.get("foto_local"), "../")}'
        f'<span class="dados"><b>{e(r["nome_urna"])}</b><span>{detalhe}</span>{selo(r["tipo_mandato"], r["cargo"])}</span>'
        '<i aria-hidden="true">&#8250;</i></a>'
    )


def opcoes_de_tipo(eleitos: list[Row]) -> str:
    """Uma opção por tipo que existe na lista, com a contagem; quem não tem selo vira `Sem selo`."""
    nomes = (("novato", "Novatos"), ("reeleito", "Reeleitos"), ("retorno", "Retorno"), ("sem", "Sem selo"))
    contagem = Counter(r["tipo_mandato"] or "sem" for r in eleitos)
    return "".join(f'<option value="{t}">{nome} ({contagem[t]})</option>' for t, nome in nomes if contagem[t])


def lista_filtravel(eleitos: list[Row], com_selos: bool, titulo: str, sufixo: str = "") -> str:
    por_tipo = (
        '<label>Tipo de mandato<select data-filtro="tipo"><option value="">Todos</option>'
        + opcoes_de_tipo(eleitos)
        + "</select></label>"
        if com_selos
        else ""
    )
    novos = sum(1 for r in eleitos if r.get("novo"))
    por_eleicao = (
        '<label>Eleição<select data-filtro="grupo"><option value="">Todas</option>'
        f'<option value="novo">Eleitos em 2026 ({novos})</option>'
        f'<option value="antes">Eleitos antes ({len(eleitos) - novos})</option></select></label>'
        if 0 < novos < len(eleitos)
        else ""
    )
    controles = (
        f'<div class="card controles"><label class="so-leitor" for="busca{sufixo}">Buscar por nome ou partido</label>'
        f'<input id="busca{sufixo}" type="search" placeholder="Buscar por nome ou partido" autocomplete="off">'
        f'<div class="selecoes">{por_eleicao}{por_tipo}<label>Ordenar por<select data-filtro="ordem">'
        '<option value="nome">Nome</option><option value="votos">Votos</option>'
        '<option value="partido">Partido</option></select></label></div>'
        '<p class="contagem" aria-live="polite"></p></div>'
    )
    return (
        f'<details class="recolhivel"><summary>{e(titulo)} ({len(eleitos)}): buscar e ver a lista</summary>'
        f'<div class="lista" data-filtravel>{controles}<div class="itens">'
        + "".join(cartao_de_pessoa(r) for r in eleitos)
        + "</div></div></details>"
    )


def _poderes_do_estado(uf: str, nome: str, linhas: list[Row], sufixo: str) -> str:
    doestado = [r for r in linhas if r["uf"] == uf]
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
    partes = [
        indice_dos_poderes(sufixo),
        '<div class="secao">',
        banda(*PODERES[0][:3], sufixo=sufixo),
        esfera("Estadual", "No estado"),
        "<h3>Governador</h3>",
        gov_html,
        esfera("Municipal", "Cidades do estado"),
        em_construcao("Prefeitos", "Quem comanda cada cidade do estado."),
        banda(*PODERES[1][:3], sufixo=sufixo),
        esfera("Federal", "Representam o estado em Brasília"),
        f"<h3>Senadores ({len(por_cargo['Senador'])})</h3>",
        "".join(cartao_de_pessoa(r) for r in por_cargo["Senador"])
        or '<p class="nota">Sem senadores neste estado.</p>',
        f"<h3>Deputados federais ({len(deputados)})</h3>",
        casa(
            "Bancada federal por partido",
            f"{len(deputados)} cadeiras de {nome}",
            contar(doestado, ("Deputado federal",)),
            rotulo="deputados",
        ),
        lista_filtravel(deputados, True, "Deputados federais", sufixo),
        esfera("Estadual", "Assembleia Legislativa"),
        f"<h3>Deputados estaduais e distritais ({len(estaduais)})</h3>",
        casa(
            "Assembleia por partido",
            f"{len(estaduais)} cadeiras de {nome}",
            contar(doestado, ("Deputado estadual", "Deputado distrital")),
            rotulo="deputados",
        ),
        lista_filtravel(estaduais, False, "Deputados estaduais e distritais", f"{sufixo}-e"),
        esfera("Municipal", "Cidades do estado"),
        em_construcao("Vereadores", "Os eleitos de cada cidade do estado."),
        banda(*PODERES[2][:3], sufixo=sufixo),
        esfera("Estadual", "Tribunal de Justiça e Tribunal Regional Eleitoral"),
        em_construcao(
            "Tribunais do estado",
            "Os desembargadores do Tribunal de Justiça e do Tribunal Regional Eleitoral. Não são eleitos.",
        ),
        "</div>",
    ]
    return "\n".join(partes)


def estado(uf: str, ano: int, visoes: dict[str, list[Row]], capturado: date | None) -> str:
    nome, _ = UFS[uf]
    entradas, controle = seletor_de_visao()
    corpo = [
        entradas,
        migalhas([("Brasil", "../index.html"), (nome, None)]),
        faixa_de_titulo(
            f"Estado · {uf}",
            nome,
            f"Quem ocupa os cargos hoje e quem assume em {ano + 1}.",
            aviso_provisorio(capturado),
        ),
        controle,
        *(
            f'<div class="visao visao-{chave}">'
            + _poderes_do_estado(uf, nome, visoes[chave], f"-{chave}")
            + "</div>"
            for chave, _ in VISOES
        ),
        legenda_dos_selos(),
    ]
    return pagina(
        f"Quem está no cargo em {nome}",
        "\n".join(corpo),
        "",
        raiz="../",
        descricao=f"Governador, senadores e deputados de {nome} hoje e depois da posse de {ano + 1}, com histórico, selo e a fonte oficial.",
        caminho=f"estado/{uf}.html",
        schema=[seo.migalhas([("Brasil", "index.html"), (nome, f"estado/{uf}.html")])],
    )


def base_do_percentual(r: Row) -> str:
    """A que se refere a porcentagem: votos nominais da disputa daquele cargo e turno."""
    onde = "no Brasil" if r["uf"] == "BR" else f"em {nome_do_local(r['uf'])}"
    turno = f", {r['turno']}º turno" if r.get("turno") else ""
    return f"{percentual(r['percentual_votos_validos'])} dos votos válidos para {str(r['cargo']).lower()} {onde}{turno}"


def periodo_de(de: date, ate: date) -> str:
    return f"{de.year} a {ate.year}" if de.year != ate.year else str(de.year)


def barra_de_mandato(de: date, ate: date, hoje: date) -> str:
    """Quanto do mandato já passou: barra de progresso e o que falta; sem JavaScript."""
    total = (ate - de).days + 1
    feito = min(max((hoje - de).days + 1, 0), total)
    pct = round(100 * feito / total)
    if hoje < de:
        esquerda, direita = f"começa em {mes_ano(de)}", ""
    elif hoje > ate:
        esquerda, direita = "encerrado", ""
    else:
        falta = (ate - hoje).days
        esquerda = f"{pct}% cumprido"
        direita = f"faltam {falta} dias" if falta < 45 else f"faltam {tempo(hoje, ate)}"
    return (
        f'<div class="barra{" futuro" if hoje < de else ""}">'
        f'<progress max="100" value="{pct}" aria-label="{pct}% do mandato cumprido">{pct}%</progress>'
        f"<div><span>{esquerda}</span><span>{direita}</span></div></div>"
    )


def linha_do_tempo(itens: list[tuple[str, str, str, str, str]]) -> str:
    """Cada item: tipo (proximo, atual, mandato, candidatura), título, linha 1, linha 2 e um bloco extra (a barra)."""
    return (
        '<ol class="tempo">'
        + "".join(
            f'<li class="{tipo}"><span class="ponto"></span><div><b>{e(titulo)}</b><span>{a}</span>'
            + (f"<small>{e(b)}</small>" if b else "")
            + f"{extra}</div></li>"
            for tipo, titulo, a, b, extra in itens
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


def _nome_da_fonte(r: Row) -> str:
    return (
        "mandato informado pelo Senado ou pela Câmara"
        if r.get("sem_eleicao")
        else f"TSE, candidaturas {r['ano_eleicao']}"
    )


def fontes_da_campanha(r: Row) -> str:
    """De onde vêm os totais da campanha: os bens declarados e a prestação de contas, cada um com seu endereço."""

    capturado = f", capturado em {data_curta(r['dt_captura_campanha'])}" if r["dt_captura_campanha"] else ""
    return (
        f"Fonte: {link_da_fonte(r['fonte_url_bens'], 'bens declarados')} e "
        f"{link_da_fonte(r['fonte_url_receitas'], 'prestação de contas')} ao TSE{capturado}. "
        "Sem dado quando não entregue, nunca zero."
    )


def sobre_a_pessoa(r: Row) -> str:
    """Quem é, no bloco do título: o cadastro da pessoa (TSE, Câmara ou Senado); sem dado, `Sem dado`."""
    casa = {
        "camara": "Câmara dos Deputados",
        "senado": "Senado Federal",
        "camara, senado": "Câmara e Senado",
    }.get(str(r["fonte_cadastro"]))
    naturalidade = ", ".join(x for x in (r["municipio_nascimento"], r["uf_nascimento"]) if x)
    profissoes = ", ".join(x.strip() for x in str(r["profissoes"] or "").split(";") if x.strip())
    profissao_tse = not profissoes and bool(r.get("ocupacao"))  # sem cadastro: a ocupação declarada ao TSE
    if profissao_tse:
        profissoes = str(r["ocupacao"]).capitalize()
    linhas = (
        ("Nome completo", vazio_ou(r["nome_civil"] or r["nome"])),
        ("Nascimento", data_curta(r["dt_nascimento"]) if r["dt_nascimento"] else "Sem dado"),
        ("Naturalidade", vazio_ou(naturalidade)),
        ("Profissões", vazio_ou(profissoes)),
        ("Site", links_oficiais(r["site_url"])),
        ("Rede social", links_oficiais(r["rede_social_url"])),
    )
    if casa:
        capturado = (
            f", capturado em {data_curta(r['dt_captura_cadastro'])}" if r["dt_captura_cadastro"] else ""
        )
        fonte = f"Fonte: {link_da_fonte(r['fonte_cadastro_url'], 'cadastro da ' + casa)}{capturado}."
        if profissao_tse:
            fonte += f" Profissão: TSE, capturado em {data_curta(r['dt_captura'])}."
    else:
        capturado = (
            f", capturado em {data_curta(r['dt_captura_cadastro'])}" if r["dt_captura_cadastro"] else ""
        )
        fonte = f"Fonte: {link_da_fonte(r['fonte_cadastro_url'], 'TSE')}{capturado}."
    return grade(linhas, largos=("Nome completo",), numeros=("Nascimento",)) + f'<p class="nota">{fonte}</p>'


def _sobrepoe(a: Row, b: Row) -> bool:
    """Dois mandatos do mesmo cargo que se cruzam no tempo (sem data, não se cruzam)."""
    if a["cargo"] != b["cargo"] or None in (
        a["dt_inicio"],
        a["dt_fim_prevista"],
        b["dt_inicio"],
        b["dt_fim_prevista"],
    ):
        return False
    return bool(a["dt_inicio"] <= b["dt_fim_prevista"] and b["dt_inicio"] <= a["dt_fim_prevista"])


def _eleito(c: Row) -> bool:
    return bool(c.get("fl_eleito")) or str(c["resultado"] or "").lower().startswith("eleito")


def ficha(
    r: Row,
    hoje: date,
    ocupacoes: list[Row],
    candidaturas_da_pessoa: list[Row],
    desde: date | None,
) -> str:
    cargo = r["cargo"]
    caminho = "pessoa/" + arquivo_da_ficha(r["nome_urna"], r["id_candidatura"])
    atual = bool(r.get("em_exercicio"))  # eleito antes e ainda no mandato, fora da lista dos eleitos do ano
    com_eleicao = [o for o in ocupacoes if o["id_candidatura"]]
    ocupacoes = [  # o exercício informado pela Câmara ou pelo Senado não repete o mandato que a eleição já deu
        o for o in ocupacoes if o["id_candidatura"] or not any(_sobrepoe(o, x) for x in com_eleicao)
    ]
    itens: list[tuple[str, str, str, str, str]] = []
    mandatos_passados: list[tuple[int, tuple[str, str, str, str, str]]] = []
    for o in ocupacoes:  # do mais recente para o mais antigo; as datas vêm do banco
        sem_data = o["dt_inicio"] is None or o["dt_fim_prevista"] is None
        if sem_data:
            tipo = "proximo" if o["ano_inicio"] > hoje.year else "atual"
        else:
            tipo = (
                "proximo" if o["dt_inicio"] > hoje else "atual" if o["dt_fim_prevista"] >= hoje else "mandato"
            )
        eleito_em = str(o["id_candidatura"]).split(":", 1)[0] if o["id_candidatura"] else None
        periodo = (
            f"a partir de {o['ano_inicio']}" if sem_data else periodo_de(o["dt_inicio"], o["dt_fim_prevista"])
        )
        titulo = {"proximo": "Próximo mandato", "atual": "Mandato atual"}.get(tipo, f"Mandato de {periodo}")
        linha = (
            (f"{periodo} &middot; " if tipo != "mandato" else "")
            + (f"eleito em {eleito_em} &middot; " if eleito_em else "")
            + e(o["cargo"])
            + (f" &middot; {e(o['partido'])}" if o["partido"] else "")
        )
        item = (
            tipo,
            titulo,
            linha,
            "Data de posse: sem dado." if sem_data else "",
            ""
            if sem_data or tipo == "mandato"
            else barra_de_mandato(o["dt_inicio"], o["dt_fim_prevista"], hoje),
        )
        if tipo == "mandato":
            mandatos_passados.append((int(eleito_em or o["ano_inicio"]), item))
        else:
            itens.append(item)
    ocupadas = {
        (int(str(o["id_candidatura"]).split(":", 1)[0]), o["cargo"]) for o in ocupacoes if o["id_candidatura"]
    }
    passado = [
        (
            c["ano_eleicao"],
            (
                "candidatura",
                f"Candidatura em {c['ano_eleicao']}",
                f"{c['cargo']}, {str(c['resultado'] or 'resultado não informado').lower()}"
                + (f" &middot; {c['partido']}" if c["partido"] else ""),
                "",
                "",
            ),
        )
        for c in candidaturas_da_pessoa
        if c["ano_eleicao"] != r["ano_eleicao"] and (int(c["ano_eleicao"]), c["cargo"]) not in ocupadas
    ]
    itens += [item for _, item in sorted([*mandatos_passados, *passado], key=lambda x: -x[0])]
    if desde:
        tempo_no_cargo = (
            f'<p class="nota">Há {tempo(desde, hoje)} no cargo, sem interrupção, desde {mes_ano(desde)}.</p>'
        )
    else:
        tempo_no_cargo = ""
    aviso_novato = (
        '<div class="card destaque-novato">'
        + selo("novato", cargo)
        + f"<p>Primeiro mandato como {cargo.lower()}.</p></div>"
        if r["tipo_mandato"] == "novato" and not atual
        else ""
    )
    campanha = grade(
        (
            (
                "Votos",
                f"{numero(r['qtd_votos'])}<small>{base_do_percentual(r)}</small>",
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
        '<p class="nota">Datas dos mandatos previstas pela base a partir da eleição, sem registro de afastamentos.</p></div>',
        ""
        if r.get("sem_eleicao")
        else f'<h2>A campanha de {r["ano_eleicao"]}</h2><div class="card">{campanha}</div>'
        f'<p class="nota">{fontes_da_campanha(r)}</p>',
        f'<p class="nota">Fonte: {link_da_fonte(r["fonte_url"], _nome_da_fonte(r))}, capturado em {data_curta(r["dt_captura"])}. '
        + ("Foto: TSE. " if r.get("foto_local") else "")
        + f'<a href="../como-calculamos.html">Como calculamos</a>. '
        f'<a href="{seo.link_de_correcao(r["nome_urna"] + ", " + cargo, caminho)}">Encontrou um erro?</a></p>',
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
