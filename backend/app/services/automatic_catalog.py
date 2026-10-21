"""Discover publications and persist source-grounded candidates without promotion."""
import asyncio
import hashlib
import logging
import re
import time
import httpx
from app.integrations.discovery_sources import (
    DiscoverySourceError, now, query_source, parse_openalex_work, parse_epmc_work,
    topic_ids, epmc_search_term,
)
from app.schemas.catalog import CatalogCandidate, CandidateConnection, DiscoveryRun, IdentityObservation
from app.services.identity_resolution import resolve_identities
from app.services.storage import cached, upsert_candidate

log = logging.getLogger('matilda.catalog')
LIMITS = {'candidates': 8, 'references': 6, 'topics': 2, 'orcid_identities': 40, 'openalex_identities': 40, 'abstract_enrichments': 3, 'timeout_seconds': 18}


def extract_candidate(work, identities):
    # Copy text rather than letting a model invent a claim. No individual task is inferred.
    excerpt = None
    if work.abstract:
        sentences = re.split(r'(?<=[.!?])\s+', work.abstract)
        result_sentences = [sentence for sentence in sentences if re.search(r'\b(we (show|report|demonstrate|found|find|identify|present)|our (results|findings|study)|demonstramos|mostramos|identificamos)\b', sentence, re.I)]
        excerpt = ' '.join((result_sentences or sentences)[:2])[:1500]
    return CatalogCandidate(
        id='auto-'+hashlib.sha256(work.doi.encode()).hexdigest()[:24], work=work,
        record_state='automatically_extracted' if excerpt else 'retrieved',
        extraction_method='abstract_excerpt_v1' if excerpt else 'metadata_only_v1',
        excerpt=excerpt, excerpt_location=('Resumo: frases com marcadores textuais de resultados; até duas frases, 1500 caracteres.' if result_sentences else 'Resumo: início; até duas frases, 1500 caracteres. Pode conter apenas contexto.') if excerpt else None,
        identities=identities,
        limitations=['Candidato recuperado automaticamente, sem revisão editorial da atribuição científica.',
                    'Trecho do resumo não identifica o papel individual de cada coautor nem comprova influência histórica.',
                    'A busca é limitada e não representa cobertura exaustiva do assunto.'] + ([] if excerpt else ['Resumo indisponível; somente metadados recuperados.']),
    )


async def discover_catalog(paper):
    started_at = now()
    started = time.monotonic()
    warnings, sources = [], []
    works, reasons = {}, {}
    completed_batches = []
    identities = {}
    failed = False
    cache = cached(paper.doi)
    raw = cache[0] if cache else {}

    def ingest(work, reason):
        if not work or work.doi == paper.doi:
            return
        if work.doi in works:
            previous = works[work.doi]
            previous.sources.extend(s for s in work.sources if s not in previous.sources)
            if not previous.abstract and work.abstract:
                previous.abstract = work.abstract
            # Persistent-ID matches only; never merge different author names heuristically.
            if not previous.authors:
                previous.authors = work.authors
            if not previous.openalex_id:
                previous.openalex_id = work.openalex_id
        elif len(works) < LIMITS['candidates']:
            works[work.doi] = work
        if work.doi in works:
            reasons.setdefault(work.doi, [])
            if reason not in reasons[work.doi]:
                reasons[work.doi].append(reason)

    def decode_work(source, row, observation):
        nonlocal failed
        try:
            return parse_openalex_work(row, observation) if source == 'openalex' else parse_epmc_work(row, observation)
        except (ValueError, TypeError, KeyError, AttributeError):
            failed = True
            warnings.append(source + ': registro incompatível ignorado.')
            return None

    async def search(source, params, reason):
        nonlocal failed
        try:
            payload, observation = await query_source(client, source, params)
            sources.append(observation)
            rows = payload.get('results') if source == 'openalex' else (payload.get('resultList') or {}).get('result')
            if not isinstance(rows, list):
                raise DiscoverySourceError(source + ': lista de resultados inválida.')
            if source == 'europe_pmc' and params.get('query', '').startswith('DOI:'):
                expected = params['query'][4:].lower()
                rows = [row for row in rows if isinstance(row, dict) and str(row.get('doi', '')).lower() == expected]
            batch = (source, rows, observation, reason)
            completed_batches.append(batch)
            return batch
        except DiscoverySourceError as exc:
            failed = True
            warnings.append(str(exc))
            return source, [], None, reason

    try:
        async with asyncio.timeout(LIMITS['timeout_seconds']):
            async with httpx.AsyncClient(timeout=httpx.Timeout(5), follow_redirects=False, headers={'User-Agent':'MatildaForensics/0.2 (academic evidence discovery)'}) as client:
                queries = []
                refs = [ref.rsplit('/', 1)[-1] for ref in paper.referenced_work_ids[:LIMITS['references']]]
                if refs:
                    queries.append(search('openalex', {'filter':'openalex_id:'+'|'.join(refs)+',has_doi:true', 'per-page':6}, 'Identificador nas referências recuperadas do artigo.'))
                for topic in topic_ids(raw)[:LIMITS['topics']]:
                    queries.append(search('openalex', {'filter':'topics.id:'+topic+',has_doi:true', 'per-page':4, 'sort':'cited_by_count:desc'}, 'Tópico OpenAlex compartilhado: '+topic+'.'))
                term = epmc_search_term(raw)
                if term:
                    queries.append(search('europe_pmc', {'query':'TITLE_ABS:"'+term+'" AND HAS_DOI:Y', 'format':'json', 'resultType':'core', 'pageSize':4}, 'Termo dos metadados pesquisado no Europe PMC: '+term+'.'))
                if not queries:
                    warnings.append('Metadados insuficientes para gerar consultas externas.')
                # Preserve priority: references, topics, then complementary biomedical retrieval.
                results = await asyncio.gather(*queries)
                for source, rows, observation, reason in results:
                    for row in rows:
                        if not isinstance(row, dict):
                            continue
                        work = decode_work(source, row, observation)
                        ingest(work, reason)
                missing = [w for w in works.values() if not w.abstract][:LIMITS['abstract_enrichments']]
                enrichments = await asyncio.gather(*(search('europe_pmc', {'query':'DOI:'+work.doi, 'format':'json', 'resultType':'core', 'pageSize':1}, 'Resumo complementar recuperado por DOI exato.') for work in missing))
                for work, (_, rows, observation, _) in zip(missing, enrichments):
                    for row in rows:
                        enriched = decode_work('europe_pmc', row, observation)
                        if enriched and enriched.doi == work.doi:
                            ingest(enriched, 'Resumo complementar recuperado por DOI exato.')
                identities = await resolve_identities(client, list(works.values()), warnings, sources)
    except TimeoutError:
        failed = True
        warnings.append('Tempo limite da ampliação atingido; os resultados já recuperados foram preservados.')
    except (ValueError, TypeError, KeyError, AttributeError):
        failed = True
        warnings.append('Uma fonte retornou dados incompatíveis; investigação automática parcial.')
    # A timeout must preserve successful queries even if their siblings timed out.
    for source, rows, observation, reason in completed_batches:
        for row in rows:
            if isinstance(row, dict):
                work = decode_work(source, row, observation)
                ingest(work, reason)
    if any(warning.startswith('wikidata:') for warning in warnings):
        failed = True
    candidates = []
    for work in works.values():
        people = identities.get(work.doi) or [IdentityObservation(author_name=a.name, author_openalex_id=a.openalex_id, orcid=a.orcid, status='unknown', method='unresolved', explanation='Resolução de identidade não concluída; sem inferência por nome.') for a in work.authors]
        candidate = extract_candidate(work, people)
        upsert_candidate(candidate)
        citation = 'CITED' if work.openalex_id and work.openalex_id in paper.referenced_work_ids else 'NOT_FOUND_IN_RETRIEVED_REFERENCES' if work.openalex_id and paper.referenced_work_ids else 'UNKNOWN'
        candidates.append(CandidateConnection(candidate=candidate, retrieval_reasons=reasons[work.doi], citation_status=citation))
    warnings.append('Candidatos automáticos não foram adicionados ao catálogo editorial verificado nem ao grafo de contribuições verificadas.')
    warnings.append('Busca por tópicos prioriza trabalhos mais citados e pode reproduzir vieses de visibilidade; não é uma ordenação por mérito ou completude.')
    status = 'unavailable' if not candidates and failed else 'partial' if failed else 'complete'
    log.info('catalog_discovery status=%s seconds=%.3f candidates=%d warnings=%d', status, time.monotonic()-started, len(candidates), len(warnings))
    return DiscoveryRun(status=status, started_at=started_at, completed_at=now(), candidates=candidates, warnings=list(dict.fromkeys(warnings)), sources=sources, limits=LIMITS)
