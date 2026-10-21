# PRD — Expansão progressiva do motor de busca

**Produto:** Matilda Forensics  
**Etapa:** próxima implementação após a descoberta automática inicial  
**Estado:** especificação aprovada para implementação  
**Idioma:** português brasileiro

## 1. Resumo

Expandir a investigação iniciada por DOI para que o Matilda procure literatura
relacionada em várias direções, acompanhe resultados progressivamente por até
dois minutos e, quando houver texto aberto autorizado, encontre passagens que
documentem contribuições e participantes. A busca deverá funcionar em diferentes
áreas científicas e manter separados fatos bibliográficos, declarações de fontes,
extrações automáticas e relações temáticas.

O catálogo curado atual permanece disponível como fonte editorial. Publicações e
afirmações encontradas pelo novo motor entram como candidatos pendentes; a
automação não os converte em contribuições historicamente verificadas.

## 2. Problema e resultado esperado

A descoberta atual é limitada a um pequeno conjunto de referências, tópicos e
fontes públicas, roda em uma única execução curta e extrai texto apenas de
resumos. Isso encontra candidatos úteis, mas não investiga a literatura em
profundidade nem localiza evidências dentro de documentos.

Após esta etapa, uma pessoa deverá conseguir partir de um artigo de qualquer
área coberta pelas fontes, acompanhar a expansão por referências e trabalhos
que o citam, ver por que cada candidato apareceu e abrir uma passagem exata que
sustenta a descrição recuperada. Se a cobertura ou a evidência forem
insuficientes, a interface deverá deixar isso claro.

## 3. Usuários e jornada

Público: estudantes, docentes e pesquisadores que investigam antecedentes e
participação científica a partir de um artigo.

1. O usuário importa um artigo por DOI e inicia a investigação existente.
2. Seleciona **Investigar mais profundamente**.
3. A interface mostra progresso real, fontes consultadas e resultados parciais.
4. O usuário explora candidatos ordenados, motivos de recuperação e relações
   bibliográficas.
5. Abre um candidato para consultar publicação, participantes identificados,
   passagens e documento de origem.
6. Exporta os resultados com fontes e limitações preservadas.

## 4. Requisitos funcionais

### RF-01 — Busca progressiva e expansão bibliográfica

- Executar em segundo plano por até 120 segundos, com profundidade máxima de
  dois saltos e no máximo 60 trabalhos únicos por investigação.
- Expandir por referências e trabalhos citantes, além de buscas por tópicos e
  termos textuais. Dividir o orçamento entre essas estratégias para que a
  primeira lista de referências não consuma toda a busca.
- Deduplicar por DOI normalizado e IDs persistentes OpenAlex; aceitar trabalhos
  sem DOI quando identificáveis por OpenAlex ou arXiv.
- Consultar OpenAlex como fonte bibliográfica principal, Crossref para metadados
  complementares e Europe PMC para literatura biomédica. Preservar cobertura
  multidisciplinar e registrar a fonte de cada observação.
- Ordenar resultados por correspondência textual e conceitual, proximidade
  bibliográfica e qualidade da evidência. Contagem de citações não poderá ser o
  principal sinal de relevância.
- Entregar até dez resultados iniciais e oferecer paginação dos demais, junto
  com motivos de recuperação e limitações.

### RF-02 — Recuperação de texto aberto e passagens

- Recuperar resumos e tentar obter texto completo apenas em fontes abertas e
  permitidas para o uso pretendido.
- Usar Europe PMC para XML biomédico e Unpaywall para localizar versões abertas,
  incluindo repositórios legais; registrar licença e versão encontrada quando
  disponíveis.
- Validar DOI/IDs, hosts permitidos, redirecionamentos, tipo e tamanho do
  conteúdo. Não contornar paywalls nem redistribuir documentos protegidos.
- Identificar passagens com texto literal e localização, como seção, página,
  parágrafo ou identificador do trecho. Preservar a URL e a versão do documento.
- Mostrar claramente se o resultado veio de resumo, texto completo ou apenas
  metadados. Ausência de texto aberto não interrompe a busca bibliográfica.

### RF-03 — Extração estruturada opcional por IA

- Suportar um provedor OpenAI opcional, configurado exclusivamente no backend;
  a busca pública e a extração determinística permanecem utilizáveis sem chave.
- Solicitar estrutura com contribuição ou resultado descrito, participantes
  explicitamente documentados, passagem literal, localização, publicação e
  relação proposta com o artigo investigado.
- Validar formato, identidade do documento e presença literal das passagens na
  versão recuperada. Rejeitar citações inexistentes, participantes sem suporte
  e relações que excedam a fonte.
- Limitar a IA a cinco publicações por investigação. Usar fallback determinístico
  quando o provedor estiver ausente, falhar, exceder orçamento ou retornar saída
  inválida. Registrar método usado em cada candidato.
- Aplicar teto padrão de custo estimado de US$ 0,10 por investigação. Se o modelo
  não tiver preço configurado, não chamar o provedor. Chaves e dados de
  autenticação nunca aparecem em logs ou respostas.

### RF-04 — Atribuição e identidade

- Preservar coautorias completas que a fonte fornecer; não dividir
  automaticamente crédito coletivo.
- Só registrar contribuição individual quando uma fonte específica declarar
  esse papel, por exemplo uma declaração CRediT ou passagem equivalente.
- Resolver identidade por ORCID ou identificadores persistentes OpenAlex em
  fontes explícitas. Estados desconhecidos ou conflitantes continuam visíveis;
  nomes não podem ser usados para inferir gênero.
- Identificar toda extração automática como pendente de revisão. O mecanismo não
  detecta apagamento, intenção discriminatória ou influência histórica por
  similaridade temática.

### RF-05 — Revisão, catálogo e rastreabilidade

- Manter candidatos automáticos separados das contribuições editoriais
  verificadas e do grafo de evidências revisadas.
- Guardar versões da publicação, hash e data da fonte, trecho, localização,
  método de extração, modelo quando utilizado, identidade e estado de revisão.
- Não incluir fluxo de aprovação autenticada nesta etapa. A fila existente
  continua sendo o ponto de inspeção e os candidatos permanecem pendentes.
- Adicionar candidatos ao grafo exploratório com rótulo próprio, sem criar
  arestas históricas verificadas a partir de resultados automáticos.

### RF-06 — Progresso, controle e interface

- Exibir estados reais: recuperação bibliográfica, expansão, busca de texto,
  extração e conclusão parcial/final. Mostrar candidatos enquanto chegam.
- Permitir cancelamento. Respeitar o limite de uma investigação ativa por
  análise, até duas execuções concorrentes no serviço e fila de até dez tarefas.
- Em reinício do backend, marcar tarefas interrompidas, preservar resultados já
  coletados e permitir nova execução sem duplicar registros.
- Distinguir no painel candidatos automáticos, estado de identidade, origem e
  evidências; preservar alternativa em lista acessível por teclado e telas
  móveis.

### RF-07 — Exportação

Markdown e JSON deverão incluir candidatos, justificativas de recuperação,
arestas bibliográficas, passagens e localizações, fontes, método de extração,
estado de revisão e avisos de cobertura. A exportação não poderá omitir o caráter
pendente de uma atribuição automática.

## 5. Contratos de API

Manter compatibilidade com os endpoints atuais. Acrescentar:

| Endpoint | Comportamento |
|---|---|
| `POST /api/analyses/{id}/investigations` | Enfileira execução e responde `202` com ID e estado inicial |
| `GET /api/investigations/{id}` | Retorna estado, progresso, resultados parciais, fontes e avisos |
| `POST /api/investigations/{id}/cancel` | Solicita cancelamento e informa o estado resultante |

Resultados finais e parciais deverão reutilizar os schemas Pydantic existentes
quando compatível, estendendo-os de forma aditiva para páginas, passagens,
estado do trabalho e método de extração. Falhas de uma fonte não descartam
resultados válidos de outras fontes.

## 6. Restrições não funcionais e operação

- Usar tarefas assíncronas locais e SQLite; não introduzir infraestrutura
  distribuída nesta etapa.
- Reutilizar timeouts, retries limitados, cache com procedência e allowlist de
  hosts. Aplicar limites de bytes e orçamento por fonte e por investigação.
- Registrar duração, fontes, falhas, candidatos, documentos acessados, uso de
  IA e custo estimado sem registrar segredos.
- Respeitar licenças, termos das APIs e limites de requisição. Configurar
  `OPENAI_API_KEY`, modelo e preços somente no backend; custo padrão permitido
  por execução: US$ 0,10.
- Preservar comportamento atual quando os novos recursos estiverem indisponíveis.

## 7. Fora do escopo

- Aprovação editorial autenticada ou promoção automática a contribuição
  verificada.
- Identificação de apropriação indevida, intenção discriminatória ou causalidade
  histórica.
- Raspagem de Google ou de páginas sem permissão, contorno de paywall e
  redistribuição de texto protegido.
- Cobertura universal de artigos ou garantia de encontrar toda contribuição
  feminina relacionada.
- Contas de usuário, colaboração, banco de grafos dedicado ou serviço de filas
  distribuído.

## 8. Plano de implementação

1. **Busca progressiva:** tarefas e estados, expansão bibliográfica, limites,
   ranking, paginação e resultados parciais.
2. **Documentos e evidências:** texto aberto, versões, passagens localizadas,
   orçamento opcional de IA e fallback determinístico.
3. **Exploração e integridade:** persistência de revisões, camada visual de
   candidatos, cancelamento, exportações e observabilidade.

Se houver risco ao fluxo atual, priorizar DOI, descoberta existente e dossiês;
entregar a expansão por etapas sem interromper esse caminho.

## 9. Testes e critérios de aceite

- Investigar artigos de duas áreas existentes e um artigo de física/ciência da
  computação fora dos cenários editoriais; os resultados devem explicar por que
  cada candidato apareceu.
- Confirmar profundidade, teto de 60 trabalhos, deduplicação por DOI/OpenAlex,
  artigos sem DOI, ciclos e paginação.
- Simular falha, timeout, `429`, cancelamento e reinício. Resultados parciais
  válidos devem permanecer acessíveis e uma nova execução não deve duplicá-los.
- Testar artigos sem resumo/texto aberto, documento grande, host não permitido,
  redirecionamento inválido e fonte com metadados incompletos.
- Testar IA ausente, dentro do orçamento, no teto de custo, sem preço conhecido,
  com JSON inválido, trecho fabricado, citação que não aparece no documento e
  coautoria sem papel individual explícito.
- Testar IDs conflitantes, ORCID ausente, pessoa sem declaração explícita e
  metadados que não autorizem classificar identidade; nunca inferir pelo nome.
- Verificar que cada afirmação extraída expõe fonte e passagem literal, ou fica
  identificada como metadado/tema sem comprovação individual.
- Comparar manualmente os dez primeiros resultados em artigos de áreas distintas
  e registrar relevância e limitações; não afirmar cobertura universal.
- Confirmar uso por teclado, alternativa textual ao grafo, painel móvel e
  exportações completas.

**Aceite central:** todo candidato apresentado como contribuição documentada
deve apontar para um documento acessível e uma passagem literal verificável,
identificar o método de extração e declarar a incerteza que permanece. Se não
houver essa evidência, o sistema deve rotulá-lo apenas como resultado
bibliográfico, metadado ou relação temática.

## 10. Premissas aprovadas

- A busca pública funciona sem serviço pago de IA.
- A execução é progressiva, com duração máxima de dois minutos e até 60
  trabalhos únicos.
- IA é opcional, limitada a cinco publicações e US$ 0,10 estimado por execução.
- Texto completo só é obtido em fontes abertas e respeitando a licença; resumo é
  o fallback.
- Candidatos e extrações automáticas não recebem aprovação científica
  automática.
- Os identificadores persistentes e passagens das fontes prevalecem sobre
  correspondências por nome ou explicações geradas.
