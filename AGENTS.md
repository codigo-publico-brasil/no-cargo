# AGENTS.md

Quanto menos código e estrutura, melhor. Proponha antes de executar mudanças de arquitetura. Quem faz o merge é uma pessoa.

- **Linhas vermelhas** (README): sem ranking, sem recomendação de voto, sem linguagem avaliativa, mesmo modelo de página para todos os partidos, sem página de pessoa privada. Se um pedido conflitar, pare e diga qual regra.
- O site **só lê o esquema `marts`** da plataforma de dados (`dado-publico-brasil`), em modo somente leitura; nunca importa o código dela. Novas colunas só entram se o contrato do dbt da plataforma as garante.
- Todo dado exibido mostra fonte oficial e data de captura. Nunca invente nem estime dado: faltou, mostre `Sem dado` (nunca zero).
- A página funciona sem JavaScript; o JS só filtra e ordena listas. O site não carrega nada de outro domínio (fontes, scripts, analytics) nem coleta dados de quem visita.
- Testes primeiro; não desative teste. Checks: `uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest`.
- Dependência nova só com ADR. Nunca grave segredo; conexões vão no `.env` (modelo em `.env.example`).
- Pendências ficam em issues do GitHub, não em arquivos `.md`.
- No PR, preencha "autoria da IA"; commits levam o trailer `Co-Authored-By` do agente.
