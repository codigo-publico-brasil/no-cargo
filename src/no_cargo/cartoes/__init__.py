"""Cartões de compartilhamento (Open Graph, 1200 x 630): um por pessoa e um por estado, na marca.

As cores são as de `static/tokens.css`; as fontes (Fraunces e Inter, licença OFL) ficam em `cartoes/fontes/`,
porque o Pillow lê TrueType e o site serve as mesmas famílias em woff2. Não usa rede nem navegador.
"""

from functools import cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

LARGURA, ALTURA = 1200, 630
FONTES = Path(__file__).parent / "fontes"
SIMBOLO = Path(__file__).parent.parent / "static" / "og.png"  # o símbolo sai do cartão padrão
FUNDO = (12, 31, 24)  # --hero-bg
TEXTO = (246, 243, 234)  # --hero-ink
APAGADO = (169, 189, 178)  # --hero-muted
VERDE, AMARELO, AZUL = (11, 93, 59), (242, 194, 48), (27, 58, 138)  # --green, --yellow, --brand-blue
MARGEM = 84


@cache
def _fonte(familia: str, tamanho: int, peso: int) -> ImageFont.FreeTypeFont:
    fonte = ImageFont.truetype(str(FONTES / f"{familia}.ttf"), tamanho)
    if familia == "Fraunces":
        fonte.set_variation_by_axes(
            [min(max(tamanho, 9), 144), peso, 0, 0]
        )  # opsz (automático, como no site), wght
    else:
        fonte.set_variation_by_axes([32, peso])  # opsz, wght
    return fonte


@cache
def _simbolo() -> Image.Image:
    with Image.open(SIMBOLO) as og:
        return og.convert("RGB").crop((84, 96, 180, 192)).copy()


def _retrato(foto: Path, diametro: int) -> Image.Image | None:
    """A foto recortada em quadrado; arquivo ausente ou ilegível não derruba o site: o cartão sai sem foto."""
    try:
        with Image.open(foto) as origem:
            return ImageOps.fit(
                origem.convert("RGB"), (diametro, diametro), Image.Resampling.LANCZOS, centering=(0.5, 0.3)
            )
    except (OSError, ValueError):
        return None


def _quebrar(
    desenho: ImageDraw.ImageDraw, texto: str, fonte: ImageFont.FreeTypeFont, largura: int
) -> list[str]:
    """Quebra o texto em linhas que cabem em `largura`."""
    linhas: list[str] = []
    atual = ""
    for palavra in texto.split():
        tentativa = f"{atual} {palavra}".strip()
        if desenho.textlength(tentativa, font=fonte) <= largura or not atual:
            atual = tentativa
        else:
            linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas


def _cabecalho_e_rodape(imagem: Image.Image, desenho: ImageDraw.ImageDraw, endereco: str) -> None:
    imagem.paste(_simbolo().resize((72, 72), Image.Resampling.LANCZOS), (MARGEM, 60))
    desenho.text((MARGEM + 90, 96), "No Cargo", font=_fonte("Fraunces", 44, 600), fill=TEXTO, anchor="lm")
    desenho.text((LARGURA - MARGEM, 96), endereco, font=_fonte("Inter", 24, 400), fill=APAGADO, anchor="rm")
    for i, cor in enumerate((VERDE, AMARELO, AZUL)):  # a faixa de cores da marca
        desenho.rectangle((i * LARGURA // 3, ALTURA - 18, (i + 1) * LARGURA // 3, ALTURA), fill=cor)


def _fita(desenho: ImageDraw.ImageDraw, x: int, y: int, texto: str) -> None:
    fonte = _fonte("Inter", 26, 600)
    largura = int(desenho.textlength(texto, font=fonte)) + 40
    desenho.rounded_rectangle((x, y, x + largura, y + 48), radius=24, outline=APAGADO, width=2)
    desenho.text((x + 20, y + 24), texto, font=fonte, fill=TEXTO, anchor="lm")


def cartao(
    titulo: str,
    linhas: list[str],
    etiqueta: str,
    saida: Path,
    foto: Path | None = None,
    endereco: str = "nocargo.codigopublicobrasil.com.br",
) -> None:
    """Escreve o cartão em `saida` (JPEG). Com `foto`, a pessoa aparece à esquerda, em círculo."""
    imagem = Image.new("RGB", (LARGURA, ALTURA), FUNDO)
    desenho = ImageDraw.Draw(imagem)
    _cabecalho_e_rodape(imagem, desenho, endereco)
    x = MARGEM
    retrato = _retrato(foto, 300) if foto is not None else None
    if retrato is not None:
        diametro = retrato.width
        mascara = Image.new("L", (diametro, diametro), 0)
        ImageDraw.Draw(mascara).ellipse((0, 0, diametro - 1, diametro - 1), fill=255)
        imagem.paste(retrato, (MARGEM, 220), mascara)
        desenho.ellipse(
            (MARGEM - 4, 216, MARGEM + diametro + 3, 220 + diametro + 3), outline=AMARELO, width=4
        )
        x = MARGEM + diametro + 60
    largura = LARGURA - x - MARGEM
    tamanho = 72
    fonte = _fonte("Fraunces", tamanho, 600)
    partes = _quebrar(desenho, titulo, fonte, largura)
    while len(partes) > 2 and tamanho > 44:  # nomes longos encolhem em vez de cortar
        tamanho -= 6
        fonte = _fonte("Fraunces", tamanho, 600)
        partes = _quebrar(desenho, titulo, fonte, largura)
    y = 215
    for parte in partes[:3]:
        desenho.text((x, y), parte, font=fonte, fill=TEXTO)
        y += int(tamanho * 1.12)
    y += 14
    for linha in linhas:
        desenho.text((x, y), linha, font=_fonte("Inter", 32, 400), fill=APAGADO)
        y += 46
    _fita(desenho, x, ALTURA - 18 - 48 - 44, etiqueta)
    saida.parent.mkdir(parents=True, exist_ok=True)
    imagem.save(saida, "JPEG", quality=72, optimize=True, progressive=True)
