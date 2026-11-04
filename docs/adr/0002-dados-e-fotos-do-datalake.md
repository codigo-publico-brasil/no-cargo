# 0002. Dados e fotos lidos do datalake público, sem arquivo local

## Contexto
A plataforma de dados publica o datalake (Parquet, `catalogo.duckdb` e `manifesto.json`) em https://datalake.codigopublicobrasil.com.br, e é a única publicação (ADR 0038 da plataforma). As fotos oficiais do TSE ficam no mesmo lugar, em `<foto_caminho>`. Até aqui o site lia um warehouse local e copiava as fotos para o `dist/`.

## Decisão
- A geração anexa o `catalogo.duckdb` do datalake em modo somente leitura, pela extensão `httpfs` do DuckDB (já faz parte do DuckDB; não é dependência nova do projeto). Nada é lido de disco. O endereço base vem de `NO_CARGO_DATALAKE` e o padrão é o do datalake.
- O site deixa de copiar fotos. As páginas apontam para `<datalake>/<foto_caminho>`, e os cartões de compartilhamento leem a foto do datalake na hora da geração (em paralelo, sem guardá-la; lida uma a uma, a geração passava de 10 minutos).
- O site continua lendo só o esquema `marts` (mais `metadata.capturas`, que dá a URL da fonte de cada captura).
- Um teste de CI confere, no `manifesto.json`, que as colunas de que o site depende existem.

## Consequências
- Exceção à regra de não carregar nada de outro domínio: o navegador busca as fotos do TSE em `datalake.codigopublicobrasil.com.br`, da mesma organização e já atrás da Cloudflare, como o próprio site. O datalake não recebe cookie nem dado do visitante além do que o protocolo HTTP envia. As fotos do cadastro da Câmara e do Senado já eram buscadas nos sites dessas casas. A página "Como calculamos" diz isso.
- A geração precisa de rede e depende de o datalake estar no ar. O datalake aponta sempre para o dado atual, sem versão por data: o teste do manifesto é o que pega uma mudança antes de ir ao ar.
- As páginas ficam leves (sem milhares de fotos no `dist/`), e a hospedagem do site não guarda binários de fotos.
