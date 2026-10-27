"""Formatação de datas, valores e blocos HTML pequenos, iguais em todas as páginas."""

import math
import re
import unicodedata
from datetime import date
from html import escape

from nocargo.cores import SEM_COR, cor_do_partido

MESES = ["jan.", "fev.", "mar.", "abr.", "mai.", "jun.", "jul.", "ago.", "set.", "out.", "nov.", "dez."]

LISTRADO = "repeating-linear-gradient(45deg,#9AA5B1 0 4px,#E3E9F0 4px 8px)"

CASA_DO_CARGO = {"Senador": "no Senado", "Deputado federal": "na Câmara"}
SELOS = {
    "novato": ("novato", "&#9733; Novato"),
    "reeleito": ("reeleito", "&#10003; Reeleito"),
    "retorno": ("retorno", "&#8634; Retorno"),
}


def e(valor: object) -> str:
    return escape("" if valor is None else str(valor), quote=True)


def endereco(id_candidatura: str) -> str:
    """Nome do arquivo da ficha: o identificador da candidatura sem os dois pontos, que o Windows não aceita."""
    return id_candidatura.replace(":", "-")


def slug(texto: str, limite: int = 60) -> str:
    """`Erika Hilton` vira `erika-hilton`: o nome no endereço ajuda a achar a página, e o identificador a mantém única."""
    sem_acento = "".join(c for c in unicodedata.normalize("NFD", texto) if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", sem_acento.lower()).strip("-")[:limite].strip("-")


def arquivo_da_ficha(nome_urna: str, id_candidatura: str) -> str:
    """`erika-hilton-2026-sp-250002539612.html`: nome, ano, UF e sequencial, estável entre gerações do site."""
    return f"{slug(nome_urna)}-{endereco(id_candidatura).lower()}.html"


def mes_ano(d: date | None) -> str:
    return "sem data" if d is None else f"{MESES[d.month - 1]} de {d.year}"


def data_curta(d: date | None) -> str:
    return "sem data" if d is None else f"{d.day:02d}/{d.month:02d}/{d.year}"


def numero(n: int | None) -> str:
    return "sem dado" if n is None else f"{n:,}".replace(",", ".")


def percentual(p: object) -> str:
    return "sem dado" if p is None else f"{float(str(p)):.1f}%".replace(".", ",")


def reais(valor: object) -> str:
    """O valor completo, com centavos (`R$ 2.381.659,40`). Vazio é `Sem dado`, nunca zero."""
    if valor is None:
        return "Sem dado"
    return "R$ " + f"{float(str(valor)):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def selo(tipo_mandato: str | None, cargo: str | None = None) -> str:
    """O selo do tipo de mandato. Novato diz a casa (`Novato no Senado`), porque é o primeiro mandato naquela casa."""
    if tipo_mandato not in SELOS:
        return ""
    classe, texto = SELOS[tipo_mandato]
    if tipo_mandato == "novato" and cargo in CASA_DO_CARGO:
        texto += f" {CASA_DO_CARGO[cargo]}"
    return f'<span class="selo {classe}">{texto}</span>'


def tempo(de: date, ate: date) -> str:
    """`11 anos e 8 meses`, contando meses completos entre as duas datas."""
    meses = (ate.year - de.year) * 12 + ate.month - de.month - (1 if ate.day < de.day else 0)
    anos, resto = divmod(max(meses, 0), 12)
    partes = []
    if anos:
        partes.append(f"{anos} ano{'s' if anos > 1 else ''}")
    if resto or not anos:
        partes.append(f"{resto} {'mês' if resto == 1 else 'meses'}")
    return " e ".join(partes)


def foto(url: str | None, nome: str, tamanho: int = 64) -> str:
    if url:
        return (
            f'<img class="foto" src="{e(url)}" alt="Foto de {e(nome)}" width="{tamanho}" height="{tamanho}" '
            'loading="lazy" referrerpolicy="no-referrer">'
        )
    return (
        f'<svg class="foto" width="{tamanho}" height="{tamanho}" viewBox="0 0 84 84" role="img" '
        'aria-label="Sem foto"><circle cx="42" cy="42" r="41" fill="#DCE5F0"/><circle cx="42" cy="34" r="14" '
        'fill="#9FB0C8"/><path d="M14 74c3-16 14-22 28-22s25 6 28 22" fill="#9FB0C8"/></svg>'
    )


def _grupos(contagens: dict[str, int], pendentes: int = 0) -> list[tuple[str, int, str]]:
    """Os partidos do maior para o menor número de cadeiras, cada um com a sua cor de marca (cinza se a fonte não tem)."""
    ordem = sorted(contagens.items(), key=lambda kv: (-kv[1], kv[0]))
    grupos = [(nome, qtd, cor_do_partido(nome) or SEM_COR) for nome, qtd in ordem]
    if pendentes:
        grupos.append(("Aguardando 2º turno", pendentes, LISTRADO))
    return grupos


def _legenda(grupos: list[tuple[str, int, str]], total: int) -> str:
    itens = "".join(
        f'<li tabindex="0" data-grupo="{i}"><span class="ponto" style="background:{cor}"></span>'
        f'<span class="nome">{e(nome)}</span><b>{numero(qtd)}</b><span class="pct">{round(100 * qtd / total)}%</span></li>'
        for i, (nome, qtd, cor) in enumerate(grupos)
    )
    return f'<ul class="legenda">{itens}</ul>'


def _nota_das_cores(grupos: list[tuple[str, int, str]]) -> str:
    sem_cor = (
        "; cinza é partido sem cor registrada na fonte" if any(cor == SEM_COR for _, _, cor in grupos) else ""
    )
    return (
        '<p class="nota">Do partido com mais cadeiras para o com menos, não por posição política. '
        f"Cada partido usa a sua cor de marca{sem_cor}.</p>"
    )


def faixa(contagens: dict[str, int], pendentes: int = 0) -> str:
    """Uma barra de 100% com cada partido na sua cor, do maior para o menor, e a legenda com nome e número."""
    grupos = _grupos(contagens, pendentes)
    total = sum(qtd for _, qtd, _ in grupos)
    if total == 0:
        return '<p class="nota">Sem eleitos registrados.</p>'
    descricao = ", ".join(f"{nome} {qtd}" for nome, qtd, _ in grupos)
    segmentos = "".join(f'<span style="flex:{qtd} 1 0;background:{cor}"></span>' for _, qtd, cor in grupos)
    return (
        f'<div class="faixa" role="img" aria-label="{e(descricao)}">{segmentos}</div>'
        f"{_legenda(grupos, total)}{_nota_das_cores(grupos)}"
    )


RAIO_MAXIMO = 7  # raio máximo da bolinha: poucas cadeiras não podem virar bolas gigantes
FOLGA = 2


def _fileiras(total: int) -> int:
    return max(2, min(18, round(math.sqrt(total) / 1.9)))


def _cadeiras(total: int) -> tuple[list[tuple[float, float]], float]:
    """Posição (ângulo, raio de 0 a 1) de cada cadeira em fileiras concêntricas, da esquerda para a direita.

    Devolve também o menor passo entre duas cadeiras vizinhas (na mesma escala), que limita o tamanho da bolinha.
    """
    fileiras = _fileiras(total)
    raios = [0.42 + 0.58 * i / (fileiras - 1) for i in range(fileiras)]
    por_fileira = [round(total * r / sum(raios)) for r in raios]
    por_fileira[-1] += total - sum(por_fileira)
    passo = 0.58 / (fileiras - 1)
    cadeiras = []
    for raio, n in zip(raios, por_fileira, strict=True):
        if n > 1:
            passo = min(passo, math.pi * raio / (n - 1))
        for j in range(n):
            cadeiras.append((math.pi * (1 - j / (n - 1)) if n > 1 else math.pi / 2, raio))
    return sorted(cadeiras, key=lambda c: (-c[0], c[1])), passo


def hemiciclo(contagens: dict[str, int], rotulo: str) -> str:
    """Uma bolinha por cadeira, em meia-lua, com o total no centro e a legenda com nome e número.

    Os partidos entram do maior para o menor, nunca por posição política, e as cores só separam os grupos.
    """
    total = sum(contagens.values())
    if total == 0:
        return '<p class="nota">Sem eleitos registrados.</p>'
    grupos = _grupos(contagens)
    dono = [i for i, (_, qtd, _) in enumerate(grupos) for _ in range(qtd)]
    cadeiras, passo = _cadeiras(total)
    r = round(min(RAIO_MAXIMO, 0.42 * passo * 100), 2)  # a bolinha nunca encosta na vizinha
    fora = 110 - r - FOLGA  # raio da fileira de fora: a bolinha inteira fica dentro do desenho
    cy = r + fora + FOLGA
    altura = round(cy + r + FOLGA, 2)
    bolas = "".join(
        f'<circle class="g{g}" cx="{round(110 + fora * raio * math.cos(ang), 2)}" '
        f'cy="{round(cy - fora * raio * math.sin(ang), 2)}" r="{r}" fill="{grupos[g][2]}" stroke="#16202B" stroke-opacity=".2" stroke-width=".4"/>'
        for (ang, raio), g in zip(cadeiras, dono, strict=True)
    )
    tamanho_total = 24 if len(numero(total)) <= 3 else 17  # o número precisa caber no vazio do meio
    descricao = ", ".join(f"{nome} {qtd}" for nome, qtd, _ in grupos)
    return (
        f'<div class="hemiciclo"><svg viewBox="0 0 220 {altura}" role="img" aria-label="{e(rotulo)}: {e(descricao)}">{bolas}'
        f'<text x="110" y="{round(cy - 12, 2)}" text-anchor="middle" class="total" style="font-size:{tamanho_total}px">{numero(total)}</text>'
        f'<text x="110" y="{round(cy - 3, 2)}" text-anchor="middle" class="rotulo">{e(rotulo)}</text></svg>'
        f"{_legenda(grupos, total)}</div>" + _nota_das_cores(grupos)
    )
