# Método científico e editorial

## O que é verificado

O catálogo inicial reúne três pesquisadoras e seis contribuições específicas:
Katalin Karikó (dois trabalhos sobre RNA), Jennifer Doudna e Emmanuelle Charpentier
(quatro trabalhos de CRISPR, com diferentes participações). A revisão de 2014
é identificada como síntese, sem ser apresentada como descoberta experimental.

A fonte primária de cada afirmação é uma publicação com DOI real. Os títulos,
identificadores e participantes foram confrontados com os registros OpenAlex
recuperados em 21/10/2026. Os resumos disponíveis foram lidos para formular
alegações restritas aos resultados relatados. Duas publicações não têm resumo no
OpenAlex (2005 e 2011); os resumos foram conferidos adicionalmente no Europe PMC
e preservados em `data/primary-source-*.json`. A localização no artigo original
consta do dossiê. A revisão editorial é inicial e assistida por
IA; não constitui revisão por especialistas independentes. Antes do pitch,
a equipe deve ler os originais e conferir cada atribuição e localização.

`verification_status=verified` significa que o catálogo liga uma afirmação
específica a documento identificável revisado na preparação, não que a aplicação
validou automaticamente o texto completo. Registros pendentes ou sem evidência
adequada ficam fora da recuperação. Uma fonte biográfica não substitui o artigo
que sustenta a contribuição.

As identidades são curadas com fontes oficiais do Nobel e IDs OpenAlex.
O registro da API oficial do Nobel documenta gênero explicitamente quando
disponível em `data/identity-verification.json`.
Não há inferência de gênero por nomes. Os demais participantes são preservados
como coautores; o catálogo reduzido de mulheres não implica participação
exclusiva dessas pessoas nem classificação dos demais autores.

## Correspondência conceitual

Um vocabulário explícito de seis conceitos reconhece frases e aliases, com
limites de palavras e normalização de acentos. Título, resumo, tópicos e
palavras-chave são registrados separadamente como procedência. Não há
similaridade vetorial, LLM ou extração irrestrita de tópicos nesta versão.
Contribuições de RNA exigem correspondência específica com mRNA ou modificação
de nucleosídeos; imunogenicidade isolada não é elegível.

O ranking conta conceitos correspondentes, desempata por ID e filtra primeiro
pela existência de evidência documental e identidade revisada. A pontuação
interna não é uma probabilidade de influência e não aparece como confiança.
Todas as conexões recuperadas entre contribuição e conceito são `RELATED_TO`.

## Comparação bibliográfica

- `CITED`: ID do trabalho associado encontrado em `referenced_works`.
- `NOT_FOUND_IN_RETRIEVED_REFERENCES`: identificadores conhecidos não localizados
  no conjunto retornado. O conjunto tem completude não auditada.
- `UNKNOWN`: referências indisponíveis, identidade bibliográfica incompleta ou
  comparação do artigo com ele próprio.
- `THEMATIC_ONLY`: contribuição sem publicação associada identificável.

Estes estados são independentes do tipo de relação conceitual. Uma contribuição
pode ser temática e ter uma publicação citada. Nenhum estado comprova influência
histórica, intenção, exclusão ou discriminação. Arestas `DOCUMENTED_INFLUENCE`
exigem evidência no esquema; nenhuma é criada pelo motor atual.

## Fontes e atualização

- `data/contributions.json`: descrições factuais e todos os participantes.
- `data/evidence.json`: afirmação, DOI, título e localização específica.
- `data/researchers.json`: identidade, área e fonte oficial.
- `data/openalex_snapshots/`: respostas reais, URL e momento da coleta. São
  cache identificado, jamais apresentadas como novas consultas.
- `data/source-verification.json`: URLs e registro da conferência de fontes.

`python scripts/prepare_catalog.py` atualiza os dez snapshots com a API pública.
`python scripts/build_catalog.py` reconstrói o catálogo editorial a partir das
alegações explícitas e metadados existentes. Revisar o diff antes de aceitar
alterações de autoria ou de atribuição. Os snapshots usados como índice
bibliográfico são parte do catálogo e precisam acompanhar novos DOIs curados.

## Limites

O catálogo fica abaixo da meta de 8–12 pesquisadoras e 12–20 contribuições do
PRD. Não há cobertura geral, investigação histórica automática, análise de PDFs,
pesquisa recursiva, verificação de conteúdo integral ou inferência de injustiça.
A ausência de resultado informa apenas o limite deste catálogo.


## Recuperação automática adicional

A ampliação agora descobre publicações a partir dos metadados do artigo, sem
limitação às áreas ou nomes editoriais. Os conceitos dinâmicos atribuídos pelo
OpenAlex são identificados como tal. Candidatos automáticos são mantidos em um
catálogo separado de observações pendentes de revisão, com identidade por fontes
explícitas, excertos literais e histórico. Os estados de revisão editorial acima
não são concedidos a esses registros. Consulte [o método da ampliação](automatic-catalog.md).
