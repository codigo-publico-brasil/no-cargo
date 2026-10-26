"""A cor de cada partido: a cor de marca que o próprio partido usa, nunca uma cor escolhida por este projeto.

Fonte: Wikidata, propriedade `cor` (P465) de cada partido, consultada em 25/10/2026. Partido sem cor
registrada na fonte aparece em cinza e a legenda diz isso; nenhuma cor é inventada. Dois partidos podem ter
a mesma cor de marca (PSTU e PCB, ambos vermelho puro): a legenda, com nome e número, separa os dois.

Para conferir ou corrigir uma cor, troque o valor abaixo e cite a fonte no PR.
"""

import unicodedata

SEM_COR = "#B4BCC6"  # partido sem cor registrada na fonte
OUTROS = "#9AA5B1"  # grupo "Outros partidos", quando uma casa tem partidos demais para a legenda

# sigla normalizada (maiúsculas, sem acento, espaço ou hífen) -> cor de marca
CORES = {
    "AGIR": "#0066BB",
    "AVANTE": "#ED5F36",
    "CIDADANIA": "#B43104",
    "DC": "#293490",
    "DEMOCRATA": "#002E68",
    "MDB": "#2E8B57",
    "MOBILIZA": "#DA010A",
    "NOVO": "#FF8511",
    "PCB": "#FF0000",
    "PCDOB": "#DA251C",
    "PCO": "#9F030A",
    "PDT": "#ED1C24",
    "PL": "#0F0073",
    "PODE": "#2E9AFE",
    "PP": "#3A5AA7",
    "PRTB": "#2CB53F",
    "PSB": "#FFBF00",
    "PSD": "#70C846",
    "PSDB": "#084B8A",
    "PSOL": "#FFEE57",
    "PSTU": "#FF0000",
    "PT": "#DA1208",
    "PV": "#006600",
    "REDE": "#088A68",
    "REPUBLICANOS": "#4DBCE7",
    "SOLIDARIEDADE": "#D86425",
    "UNIAO": "#40CCFF",
}


def chave(sigla: str) -> str:
    """`PC do B` e `PCdoB` viram `PCDOB`; `UNIÃO` vira `UNIAO`."""
    sem_acento = "".join(c for c in unicodedata.normalize("NFD", sigla) if not unicodedata.combining(c))
    return "".join(c for c in sem_acento.upper() if c.isalnum())


def cor_do_partido(sigla: str) -> str | None:
    return CORES.get(chave(sigla))
