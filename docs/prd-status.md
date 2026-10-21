# PRD v3.0 — situação da implementação

Referência: PRD Matilda Forensics fornecido pela equipe em 21/10/2026,
consolidado em 20/10/2026. Esta matriz descreve a versão local entregue;
não substitui o PRD original nem confirma etapas humanas ainda não realizadas.

## P0

| Requisito | Situação e limite |
|---|---|
| P0-01 / RF-01 — DOI | Implementado: normalização, identidade, metadados reais e erros |
| P0-02 — OpenAlex | Implementado: integração ao vivo e cache datado; chave opcional no backend |
| P0-03 / RF-02 — Conceitos | Implementado com vocabulário específico determinístico e procedência |
| P0-04 / RF-03 — Catálogo | Implementado com 3 pesquisadoras, 6 contribuições e fontes; meta quantitativa pendente |
| P0-05 / RF-04 — Recuperação | Implementado: elegibilidade documental e ranking determinístico |
| P0-06 / RF-05 — Grafo | Implementado: cinco tipos de nó, relações direcionais, IDs estáveis |
| P0-07 — Relações visuais | Implementado: rótulos, setas, tracejado e seleção |
| P0-08 / RF-07 — Dossiês | Implementado: fontes, participantes, localização e limites |
| P0-09 / RF-09 — Cobertura | Implementado: erros, cache, referências parciais e estado vazio |
| P0-10 — Responsividade | Implementado: abas móveis, teclado e alternativa textual |
| RF-08 — Explicações | Implementado com fallback determinístico; sem LLM externo |

## P1

| Requisito | Situação |
|---|---|
| P1-01 / P1-02 / RF-06 — Comparação das redes | Implementado por IDs; estados explícitos e completude não auditada |
| P1-03 — Caminhos | Destaque do caminho conceitual e documentos da contribuição selecionada |
| P1-04 — Busca livre | Pendente; entrada apenas por DOI |
| P1-05 / RF-10 — Exportação | Markdown e JSON implementados |
| P1-06 — Expansão | Pendente; grafo limitado e limite informado |
| P1-07 — Etapas progressivas | Recuperação e investigação são estados reais; não há etapas internas simuladas |

## Definition of Done e pendências de entrega

A jornada integrada foi exercitada nos dois cenários, com testes de dez DOIs
reais, falhas de API simuladas, dossiês, fontes, grafo e lista textual.

Ainda precisam ser realizados pela equipe:

- Revisão especializada das fontes e atribuições antes do pitch.
- Ampliação editorial em direção à meta de 8–12 pesquisadoras e 12–20 contribuições.
- Teste exploratório com usuários e registro do valor percebido.
- Teste de fluidez com pelo menos 40 nós e medição no equipamento da apresentação.
- Ensaio do pitch, verificação no projetor e conferência do regulamento vigente.
- Preenchimento dos quatro integrantes e definição da licença do código.
- Publicação em GitHub após disponibilização de um remoto com acesso.

Não implementados: PDF, contas, projetos salvos, investigação recursiva, bancos
de grafos, busca semântica aberta e atribuição automática de influência histórica.
A entrega não é apresentada como cumprimento integral de todas as metas do PRD.

## Decisões técnicas

O protótipo usa CSS próprio e componentes HTML acessíveis em vez de Tailwind e
uma biblioteca de componentes. Isso preserva o stack central e reduz dependências.
O catálogo é deliberadamente pequeno; nomes e contribuições não foram inventados
para atingir metas de volume. SQLite evita infraestrutura além dos dois processos.


## Ampliação iniciada em 21/10/2026

Ingestão automática entregue: referências/tópicos OpenAlex, resumos Europe PMC,
identidades Wikidata por identificadores exatos, candidatos versionados em SQLite,
fila consultável, interface de inspeção e exportação. Conceitos dinâmicos ampliam
a ficha além do vocabulário editorial. O catálogo editorial continua com 3
pesquisadoras e 6 contribuições; os candidatos não contam como atribuições
verificadas. Detalhes em [automatic-catalog.md](automatic-catalog.md).

A aprovação editorial autenticada, extração por LLM e atribuição por CRediT
permanecem pendentes. Não há inferência de gênero pelo nome ou promoção automática
de resumos a afirmações históricas verificadas.
