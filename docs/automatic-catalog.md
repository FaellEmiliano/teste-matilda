# Ampliação automática do catálogo

A versão 0.2 acrescenta um fluxo executável de descoberta e ingestão. A lista
manual de pessoas e conceitos deixa de ser o limite da busca externa. O catálogo
editorial original continua fornecendo contribuições já revisadas; as novas
publicações entram como **candidatos**, sem atribuição individual automática.

## Usar na aplicação

1. Importe um DOI e investigue o artigo.
2. Clique em **Ampliar descoberta automaticamente**.
3. Consulte publicações, trechos literais de resumos, autoria e motivos de busca.
4. Use o filtro de identidade documentada para encontrar trabalhos com ao menos
   uma mulher associada por identificador persistente e fonte explícita.
5. Abra as fontes e o registro JSON com histórico. A fila completa está em
   `/api/catalog/candidates`.

Não há promoção automática de candidatos a contribuição verificada. Esta etapa
entrega a descoberta, a extração conservadora e a fila de inspeção; a interface de
aprovação editorial com autenticação ainda não foi implementada.

## Fontes implementadas

| Integração | Consulta e papel |
|---|---|
| OpenAlex | Até seis referências do artigo e até dois tópicos atribuídos ao próprio registro; busca de trabalhos e metadados |
| Europe PMC | Busca por termo derivado das palavras-chave/título; complemento de até três resumos por DOI exato |
| Wikidata | ORCID (`P496`) ou ID OpenAlex (`P10283`) exatos, com declaração explícita de gênero (`P21`) e referência |

O caminho de descoberta não usa uma lista fixa de nomes ou áreas. Os conceitos da
ficha também incorporam até três tópicos dinâmicos do OpenAlex com score ≥ 0,5,
identificados como atribuições da base, cuja relevância não foi auditada.
A extração editorial antiga por aliases continua sendo usada apenas para ligar
os exemplos revisados às suas contribuições.

Não há busca no Google, raspagem de páginas, embeddings ou LLM externo nesta
entrega. Crossref, Unpaywall e consulta direta ao serviço ORCID são etapas futuras.
ORCID é usado como identificador presente nos metadados bibliográficos; não se
atribui ao próprio ORCID uma informação de gênero que ele não forneceu.

## Identidade sem inferência por nome

Um nome nunca serve como chave para classificar gênero. As identidades do
catálogo original podem ser reutilizadas por ID OpenAlex exato; novas identidades
são consultadas no Wikidata por ORCID ou ID OpenAlex. O resultado preserva método,
item Wikidata e URLs das fontes.

- `documented_woman`: declaração explícita compatível com mulher e referência
  recuperada, ou identidade previamente revisada por ID exato.
- `reported_without_reference`: declaração explícita, sem referência recuperada.
- `conflicting`: identificadores ambíguos ou declarações incompatíveis.
- `unknown`: dados insuficientes; não significa que a pessoa não seja mulher.

Declarações depreciadas são excluídas. Os valores de mulher e mulher trans são
aceitos. A presença de referência no Wikidata é uma observação do dado publicado,
não uma revisão independente da referência pela aplicação. Divergências da
fonte ou possíveis erros de desambiguação do OpenAlex continuam exigindo revisão.
A pesquisa é limitada a 40 ORCIDs e 40 IDs OpenAlex por execução; o limite é
informado, preservando todos os coautores recuperados no candidato.

## Extração e integridade

`abstract_excerpt_v1` seleciona até duas frases literais do resumo, priorizando
marcadores textuais como “we show” ou “we demonstrate”. Sem esses marcadores,
copia o início e informa que o trecho pode conter apenas contexto. O limite é
1500 caracteres. Isto é extração de texto, não identificação automática de uma
contribuição individual. Sem resumo, o registro fica em `metadata_only_v1`.

Todos os candidatos têm `verification_status=pending_review`. O sistema não
reescreve o trecho como descoberta histórica nem deriva o papel de cada coautor.
A autoria integral recebida é preservada, sem completar participantes ausentes
com nomes inventados. Resultados sem DOI válido são ignorados. O artigo de
entrada não vira candidato a si próprio. Resumos complementares exigem DOI exato.

A comparação bibliográfica usa o ID OpenAlex do trabalho e todas as referências
do artigo: `CITED`, `NOT_FOUND_IN_RETRIEVED_REFERENCES` ou `UNKNOWN`.
A relação de recuperação continua sendo `RELATED_TO`. Ausência de citação não
comprova exclusão; proximidade temática não comprova influência.

## Persistência e procedência

SQLite recebe automaticamente três tabelas adicionais, sem apagar o banco atual:

- `external_cache`: respostas públicas por hash da fonte e parâmetros, TTL 24h.
- `catalog_candidates`: registro atual, consolidado por DOI normalizado.
- `catalog_revisions`: versões por hash do conteúdo, com momento de observação.

O mesmo DOI mantém o mesmo identificador. Repetir uma observação idêntica não
cria revisão duplicada. Uma mudança de origem, conteúdo ou indicação de cache
pode criar nova revisão auditável. Candidatos e histórico persistem além da
retenção de sete dias das investigações, para formar o catálogo acumulado.
Não há edição ou aprovação de registros pela API pública atual.

Cada fonte registra endpoint, parâmetros sem credenciais, data e uso de cache.
As respostas e o catálogo nunca incluem a chave OpenAlex. Links de identidade
aceitam somente HTTP/HTTPS e são apresentados como links, não buscados pela API.
Os domínios consultados pelo servidor são fixos.

## API

| Endpoint | Uso |
|---|---|
| `POST /api/analyses/{id}/discovery` | Executa a ampliação; retorna Analysis com `external_discovery` |
| `GET /api/catalog/candidates?offset=0&limit=30` | Fila persistente, com paginação limitada a 100 itens |
| `GET /api/catalog/candidates/{id}` | Registro e hashes das revisões |

A ampliação também passa a integrar as exportações Markdown e JSON da análise.
O grafo de contribuições revisadas permanece separado dos candidatos pendentes.

## Limites operacionais

Teto de oito candidatos por execução e 18 segundos. As requisições têm timeout
de cinco segundos; 429/502/503/504 recebem uma repetição com pausa de 300 ms.
Respostas são limitadas a 6 MB antes do processamento JSON. Consultas independentes
são concorrentes; resultados concluídos sobrevivem ao timeout de outras fontes.

`complete` significa que as consultas planejadas concluíram, não que a ciência
foi coberta integralmente ou que todas as identidades foram resolvidas. `partial`
informa falhas ou timeout; `unavailable` indica falha sem candidatos recuperados.
Referências têm prioridade no limite de candidatos; tópicos usam número de
citações como ordenação e podem reproduzir vieses. Europe PMC cobre principalmente
biomedicina, enquanto OpenAlex é mais amplo. Não há investigação recursiva.

## Conferência real

Em 21/10/2026, os cenários CRISPR e RNA recuperaram oito candidatos cada. O fluxo
identificou **Ann M. Arvin**, ausente do catálogo manual, por ORCID no Wikidata,
como coautora de `10.1126/scitranslmed.abe0948`. Isso confirma o caminho técnico de
descoberta de uma nova identidade, não uma atribuição individual revisada.
Katalin Karikó também apareceu em uma publicação de 2015 fora das seis entradas
editoriais. As observações e consultas estão em
[automatic-discovery-live-check.json](automatic-discovery-live-check.json), com
cache explicitamente identificado. São resultados datados, não garantia de que
APIs ou índices permanecerão iguais.

## Próximas etapas

1. Aprovação editorial autenticada, preservando trecho, fonte e autor da revisão.
2. Extração estruturada opcional por LLM, validada contra trechos efetivos e schema.
3. Declarações CRediT e texto aberto autorizado para atribuições mais específicas.
4. Recuperação semântica e avaliação de pertinência em artigos fora dos exemplos.
5. Expansão paginada, controle de orçamento e curadoria de vieses de recuperação.
