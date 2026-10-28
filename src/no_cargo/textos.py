"""Páginas de texto: o que cada cargo faz e como os dados são tratados. Escritas à mão, iguais para todos os partidos."""

from no_cargo import seo
from no_cargo.paginas import (
    PODERES,
    banda,
    em_construcao,
    esfera,
    faixa_de_titulo,
    pagina,
)

CARGOS = (
    # poder, nome, o que faz, fatos (rótulo, valor)
    (0, "Presidente", "Comanda o governo do país. Cuida de áreas como saúde, educação e estradas federais, propõe o orçamento e sanciona ou veta as leis aprovadas pelo Congresso.",
     (("Onde atua", "Todo o Brasil"), ("Quantos", "1"), ("Mandato", "4 anos"), ("Reeleição", "1 vez seguida"))),
    (0, "Governador", "Comanda o governo do estado. Cuida de segurança pública, hospitais e escolas estaduais, estradas do estado e do orçamento estadual.",
     (("Onde atua", "No estado"), ("Quantos por estado", "1"), ("Mandato", "4 anos"), ("Reeleição", "1 vez seguida"))),
    (1, "Senador", "Representa o estado no Senado Federal, em Brasília. Vota as leis do país, aprova indicados do presidente (como ministros do STF) e julga o presidente em caso de impeachment.",
     (("Onde atua", "Brasília"), ("Quantos", "3 por estado (81)"), ("Mandato", "8 anos"), ("Reeleição", "Sem limite"))),
    (1, "Deputado federal", "Faz parte da Câmara dos Deputados, em Brasília. Propõe e vota leis, aprova o orçamento da União e fiscaliza o governo federal.",
     (("Onde atua", "Brasília"), ("Quantos", "513 no país"), ("Vagas por estado", "de 8 a 70"), ("Mandato", "4 anos"), ("Reeleição", "Sem limite"))),
    (1, "Deputado estadual", "Faz parte da Assembleia Legislativa do estado, na capital. Propõe e vota as leis do estado, aprova o orçamento estadual e fiscaliza o governador. No Distrito Federal o cargo se chama deputado distrital e atua na Câmara Legislativa.",
     (("Onde atua", "Capital do estado"), ("Quantos", "1.035 no país, 24 no DF"), ("Mandato", "4 anos"), ("Reeleição", "Sem limite"))),
)  # fmt: skip


def _cartao(nome: str, texto: str, fatos: tuple[tuple[str, str], ...]) -> str:
    linhas = "".join(f'<div class="fato"><span>{r}</span><b>{v}</b></div>' for r, v in fatos)
    return f'<div class="card cargo"><h3>{nome}</h3><p>{texto}</p>{linhas}</div>'


def cargos() -> str:
    corpo = [
        faixa_de_titulo(
            "Entenda os cargos",
            "Quem faz o quê nos três poderes",
            "O poder se divide em três: quem executa, quem faz as leis e quem julga. Cada um existe na esfera federal, estadual e municipal.",
        ),
        '<div class="secao">',
    ]
    for i, poder in enumerate(PODERES):
        corpo.append(banda(*poder[:3]))
        corpo += [_cartao(n, t, f) for p, n, t, f in CARGOS if p == i]
        if i == 0:
            corpo.append(esfera("Municipal", "Cidades"))
            corpo.append(
                em_construcao(
                    "Prefeito", "Comanda a cidade. É escolhido nas eleições municipais, a cada 4 anos."
                )
            )
        if i == 1:
            corpo.append(em_construcao("Vereador", "Faz as leis do município e fiscaliza a prefeitura."))
        if i == 2:
            corpo.append(
                em_construcao(
                    "Ministros e juízes",
                    "O Supremo Tribunal Federal tem 11 ministros, indicados pelo presidente e aprovados pelo Senado. Juízes e desembargadores entram por concurso.",
                )
            )
    corpo += [
        "<h2>Perguntas comuns</h2>",
        '<div class="card perguntas">'
        "<p><b>O que é um mandato?</b><br>O tempo que a pessoa fica no cargo depois de eleita.</p>"
        "<p><b>O que é ser eleito de novo?</b><br>Quem já estava no cargo e ganhou outra vez. Chamamos de reeleito.</p>"
        "<p><b>Por que algumas pessoas aparecem sem selo?</b><br>Quando não conseguimos ligar a pessoa às eleições e aos mandatos anteriores, não afirmamos nada: nem novata, nem reeleita.</p></div>",
        '<p class="nota">Fonte: Constituição Federal, artigos 27, 28, 44 a 46, 77 e 82.</p>',
        "</div>",
    ]
    return pagina(
        "Entenda os cargos",
        "\n".join(corpo),
        "cargos",
        descricao="O que faz cada cargo eleito no Brasil (presidente, governador, senador, deputados), em palavras simples.",
        caminho="cargos.html",
    )


def como_calculamos() -> str:
    corpo = [
        faixa_de_titulo(
            "Como calculamos",
            "De onde vêm os dados",
            "Aqui está de onde vêm os dados, com que frequência mudam, o critério que vale para todos e como pedir uma correção.",
        ),
        '<div class="secao">'
        "<h2>O que mostramos</h2><p>Para cada estado: o governador, os senadores e os deputados eleitos, com a foto quando a fonte tem. "
        "Em cada ficha: quem é, o tempo no cargo, o histórico de mandatos e candidaturas e os totais da campanha. "
        "Não damos nota, não fazemos ranking e não recomendamos voto. Mostramos fatos com fonte e data.</p>"
        "<h2>De onde vêm os dados</h2>"
        '<div class="card"><p><b>Resultado e candidaturas:</b> Tribunal Superior Eleitoral (TSE), dados abertos.</p>'
        "<p><b>Bens, receitas e despesas:</b> declarados pelos candidatos ao TSE. Mostramos só os totais.</p>"
        "<p><b>Mandatos e fotos de quem já exerce mandato:</b> Câmara dos Deputados e Senado Federal, dados abertos.</p></div>"
        "<h2>Em construção e em validação</h2>"
        '<div class="card"><p>Este site está em construção e os dados ainda estão em validação: pode haver erros e lacunas. '
        "Prefeitos, vereadores e o Judiciário ainda não aparecem aqui. Cada dado mostra a fonte oficial e a data de captura, para você conferir.</p></div>"
        "<h2>Provisório e confirmado</h2>"
        '<div class="card aguardando"><p><b>Aguardando resultado:</b> o cargo ainda não tem eleito, por exemplo enquanto o 2º turno não termina.</p></div>'
        '<div class="card"><p><b>Resultado provisório:</b> o TSE já informa o eleito, mas a diplomação, que confirma o resultado, ainda não aconteceu.</p></div>'
        '<div class="card"><p><b>Confirmado:</b> o resultado passa a ser confirmado na diplomação, que a Justiça Eleitoral faz depois da eleição e antes da posse. '
        "Hoje todos os resultados aparecem como provisórios, porque a plataforma de dados ainda não traz a diplomação.</p></div>"
        "<h2>O critério é igual para todos</h2><ul>"
        "<li>Mesmo modelo de página e mesmos campos, na mesma ordem, para todos os partidos.</li>"
        "<li>Listas de pessoas começam em ordem alfabética; quem quiser filtra ou ordena. A barra de partidos vai do que tem mais cadeiras ao que tem menos, e as cores só separam os grupos.</li>"
        "<li>Os selos Novato, Reeleito e Retorno são iguais para todos os partidos.</li>"
        "<li>Cada partido aparece na sua cor de marca, registrada no Wikidata. Partido sem cor registrada aparece em cinza, e nenhuma cor é inventada. A ordem é sempre do maior para o menor número de cadeiras.</li>"
        "<li>Só dados públicos e oficiais, sem CPF, endereço ou telefone. Sem antecedentes, processos ou palavras de opinião.</li></ul>"
        "<h2>De onde vêm as fotos</h2><p>As fotos vêm direto dos sites da Câmara dos Deputados e do Senado Federal: o seu navegador as busca nesses sites, que podem registrar o acesso (não informamos de qual página você vem). Quem não tem foto na fonte aparece com um desenho.</p>"
        "<h2>Encontrou um erro?</h2><p>Abra uma issue pública com a página, o dado e o link da fonte oficial: o repositório é o canal de correção. Corrigimos o que estiver errado, mostrando a data da correção.</p>"
        f'<p><a href="{seo.link_de_correcao("Como calculamos", "como-calculamos.html")}">Abrir uma issue de correção &#8599;</a></p>'
        "</div>",
    ]
    return pagina(
        "Como calculamos",
        "\n".join(corpo),
        "como",
        descricao="De onde vêm os dados do No Cargo, como as pessoas são ligadas entre eleições e o que ainda não sabemos.",
        caminho="como-calculamos.html",
    )
