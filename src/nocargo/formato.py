"""Formatação de datas, valores e blocos HTML pequenos, iguais em todas as páginas."""

from datetime import date
from html import escape

MESES = ["jan.", "fev.", "mar.", "abr.", "mai.", "jun.", "jul.", "ago.", "set.", "out.", "nov.", "dez."]

# Cores só separam os grupos da faixa de partidos: seguem a posição (1º, 2º...) e nunca identificam um partido.
CORES_DA_FAIXA = ("#6250d6", "#1baf7a", "#e34948", "#008300", "#e87ba4")
COR_OUTROS = "#9AA5B1"
LISTRADO = "repeating-linear-gradient(45deg,#9AA5B1 0 4px,#E3E9F0 4px 8px)"

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


def mes_ano(d: date | None) -> str:
    return "sem data" if d is None else f"{MESES[d.month - 1]} de {d.year}"


def data_curta(d: date | None) -> str:
    return "sem data" if d is None else f"{d.day:02d}/{d.month:02d}/{d.year}"


def numero(n: int | None) -> str:
    return "sem dado" if n is None else f"{n:,}".replace(",", ".")


def percentual(p: object) -> str:
    return "sem dado" if p is None else f"{float(str(p)):.1f}%".replace(".", ",")


def reais(valor: object) -> str:
    """Valor abreviado para leitura rápida; o valor exato vai no `title` de quem usa. Vazio é `Sem dado`, nunca zero."""
    if valor is None:
        return "Sem dado"
    v = float(str(valor))
    if v >= 1e9:
        return f"R$ {v / 1e9:.1f} bi".replace(".", ",")
    if v >= 1e6:
        return f"R$ {v / 1e6:.1f} mi".replace(".", ",")
    if v >= 1e3:
        return f"R$ {v / 1e3:.0f} mil"
    return f"R$ {v:.0f}"


def selo(tipo_mandato: str | None, feminino: bool = False) -> str:
    if tipo_mandato not in SELOS:
        return ""
    classe, texto = SELOS[tipo_mandato]
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


def faixa(contagens: dict[str, int], pendentes: int = 0) -> str:
    """Uma barra de 100% com os cinco partidos de mais cadeiras, o resto em Outros, e a legenda com nome e número.

    Do maior para o menor, em qualquer casa. As cores seguem a posição na barra e não identificam partido.
    """
    total = sum(contagens.values()) + pendentes
    if total == 0:
        return '<p class="nota">Sem eleitos registrados.</p>'
    ordem = sorted(contagens.items(), key=lambda kv: (-kv[1], kv[0]))
    grupos = [(nome, qtd, CORES_DA_FAIXA[i]) for i, (nome, qtd) in enumerate(ordem[:5])]
    resto = sum(qtd for _, qtd in ordem[5:])
    if resto:
        grupos.append(("Outros partidos", resto, COR_OUTROS))
    if pendentes:
        grupos.append(("Aguardando 2º turno", pendentes, LISTRADO))
    descricao = ", ".join(f"{nome} {qtd}" for nome, qtd, _ in grupos)
    segmentos = "".join(f'<span style="flex:{qtd} 1 0;background:{cor}"></span>' for _, qtd, cor in grupos)
    legenda = "".join(
        f'<li><span class="ponto" style="background:{cor}"></span><span class="nome">{e(nome)}</span>'
        f'<b>{numero(qtd)}</b><span class="pct">{round(100 * qtd / total)}%</span></li>'
        for nome, qtd, cor in grupos
    )
    return (
        f'<div class="faixa" role="img" aria-label="{e(descricao)}">{segmentos}</div><ul class="legenda">{legenda}</ul>'
        '<p class="nota">Do partido com mais cadeiras para o com menos. As cores só separam os grupos e não indicam partido.</p>'
    )
