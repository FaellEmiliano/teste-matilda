# Validação local — 21/10/2026

## Resultado automatizado

- Backend: **38 testes aprovados** (`.venv/bin/python -m pytest backend/tests -q`).
- Navegador Chromium: **4 testes aprovados** (`npm run test:e2e` no frontend).
- Produção: TypeScript e Vite compilados com `npm run build`.

Os testes backend utilizam snapshots reais dos dez DOIs abaixo. API indisponível,
404, 401/403, 429 e falhas de rede são simulados com HTTPX ou substituição do
adaptador externo. Não se usa conteúdo bibliográfico fictício em produção.
A suite testa a rejeição de alegações históricas sem evidência, a exclusão de
candidatos sem documentação, identidade DOI incompatível, fontes, autorias,
direção das citações, nós consolidados e exportações.

| DOI real | Uso |
|---|---|
| 10.1126/science.1225829 | Fonte experimental CRISPR-Cas9 |
| 10.1038/nature09886 | CRISPR; cenário sem resumo no OpenAlex |
| 10.1126/science.1192272 | Processamento de RNA por Csy4 |
| 10.1126/science.1258096 | Revisão de CRISPR-Cas9 |
| 10.1016/j.immuni.2005.06.008 | Modificações de nucleosídeos |
| 10.1038/mt.2008.200 | Pseudouridina em mRNA |
| 10.1056/NEJMoa2034577 | Demonstração de vacinas RNA |
| 10.1056/NEJMoa2035389 | Generalização para outro artigo de vacina RNA |
| 10.1126/science.1231143 | Demonstração de edição genômica |
| 10.1038/171737a0 | Fora da cobertura conceitual atual |

Todos os registros foram recuperados ao vivo do OpenAlex durante a implementação,
com URLs e datas preservadas em `data/openalex_snapshots/`. Os testes repetíveis
usam o cache, sem alegar uma nova consulta externa em cada execução.

## Testes de navegador

1. Importar DOI, investigar CRISPR, selecionar contribuição, conferir participantes
   e DOI de evidência, alternar camadas e lista, baixar Markdown.
2. Investigar RNA em viewport 390 × 844, abrir dossiê sem depender do grafo,
   alternar abas e verificar ausência de rolagem horizontal.
3. Erro de DOI inválido e estado vazio sem inferir inexistência de contribuições.
4. Submeter DOI, iniciar investigação e selecionar contribuição por teclado.

A inspeção visual das capturas identificou uma falha inicial de dimensionamento
dos nós do React Flow. A correção passou a aplicar as mudanças de dimensão e
posição do componente. O teste confirma visibilidade dos nós e presença das
arestas. Capturas finais:

- [Página inicial](screenshots/inicio.png)
- [Investigação com dossiê](screenshots/investigacao.png)
- [Dossiê em celular](screenshots/mobile.png)

## Limites desta validação

Não foram realizados testes com usuários, leitores de tela, avaliação completa
WCAG, teste de carga nem medição de 40 nós no equipamento da apresentação.
Os tempos observados localmente não representam SLA. A revisão final das fontes,
a equipe e o pitch permanecem sob responsabilidade dos participantes.

A versão atual do TestClient gera um aviso de depreciação sobre HTTPX; os testes
passam. Não afeta as requisições da aplicação, feitas pelo adaptador HTTPX.

## Ampliação automática — atualização de 21/10/2026

Validação atual: **59 testes backend aprovados**, **6 testes de navegador
aprovados** e build TypeScript/Vite concluído. Os testes adicionais cobrem:

- ORCID e ID OpenAlex exatos, identidade sem identificador, declarações sem fonte,
  referências com protocolo inválido e identidades conflitantes.
- Ingestão por DOI normalizado, cache com procedência, histórico idempotente,
  limites de paginação e preservação do catálogo editorial.
- Trecho literal de resultados, ausência de resumo, recusa de complementos com
  DOI incompatível, respostas malformadas, retries de 429 e timeout parcial.
- Interface de candidatos, filtro de identidade documentada, fontes, celular e
  tentativa novamente após falha sem perder a investigação original.

O teste real com CRISPR e RNA também foi executado por API e navegador. Cada
cenário retornou oito candidatos. A identificação de Ann M. Arvin por ORCID no
Wikidata demonstrou descoberta fora dos três nomes manuais, mantendo a atribuição
científica pendente. As consultas, datas, fontes e indicações de cache constam em
[automatic-discovery-live-check.json](automatic-discovery-live-check.json).

[Captura da ampliação automática](screenshots/automatic-discovery.png).
As integrações públicas podem mudar; a validação registra uma observação datada.
