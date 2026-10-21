import asyncio
import logging
import os
import re
from datetime import datetime, timezone
from urllib.parse import unquote, quote
import httpx
from fastapi import HTTPException
from app.schemas import Paper, Author
from app.services.concept_analysis import extract_concepts
from app.services.storage import cached, save_cache

log = logging.getLogger('matilda.openalex')

def normalize_doi(value):
    value = unquote(value.strip()).lower()
    value = re.sub(r'^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)', '', value)
    if len(value) > 250 or not re.fullmatch(r'10\.\d{4,9}/[^\s<>"?#]+', value):
        raise HTTPException(422, 'DOI inválido. Use, por exemplo, 10.1126/science.1225829.')
    return value

def abstract_text(index):
    if not isinstance(index, dict) or not index:
        return None
    words = {}
    for word, positions in index.items():
        for position in positions:
            if isinstance(position, int) and 0 <= position < 100000:
                words[position] = word
    return ' '.join(words[p] for p in sorted(words)) or None

def parse_paper(raw, doi, retrieved_at, from_cache=False, stale=False):
    returned = raw.get('doi')
    if not returned or normalize_doi(returned) != doi or not re.fullmatch(r'https://openalex.org/W\d+', raw.get('id', '')):
        raise HTTPException(502, 'A base retornou uma identidade bibliográfica incompatível com o DOI.')
    title = raw.get('title') or raw.get('display_name')
    if not title:
        raise HTTPException(502, 'O registro retornado não possui título.')
    abstract = abstract_text(raw.get('abstract_inverted_index'))
    warnings = ['O OpenAlex não garante a completude das referências. Ausência no conjunto recuperado não prova omissão.', 'Conceitos extraídos por correspondência determinística de termos; nenhuma influência histórica é inferida.']
    if not abstract:
        warnings.append('Resumo indisponível. A análise conceitual está limitada ao título, tópicos e palavras-chave.')
    references = list(dict.fromkeys(x for x in raw.get('referenced_works', []) if re.fullmatch(r'https://openalex.org/W\d+', x)))
    if not references:
        warnings.append('Referências indisponíveis; comparação bibliográfica inconclusiva.')
    if from_cache:
        warnings.append('Metadados de cache identificado, recuperados em ' + retrieved_at + '.')
    if stale:
        warnings.append('API indisponível: utilizando cache anterior ao prazo de atualização.')
    authors = []
    for item in raw.get('authorships') or []:
        author = item.get('author') or {}
        if author.get('id') and author.get('display_name'):
            authors.append(Author(id=author['id'], name=author['display_name']))
    return Paper(id=raw['id'], openalex_id=raw['id'], doi=doi, title=title, abstract=abstract, year=raw.get('publication_year'), authors=authors, concepts=extract_concepts(raw, abstract), referenced_work_ids=references, references_status='retrieved_unverified_completeness' if references else 'unavailable', source_url=raw['id'], retrieved_at=retrieved_at, from_cache=from_cache, cache_stale=stale, limitations=warnings)

async def fetch_remote(doi):
    params = {}
    if os.getenv('OPENALEX_API_KEY'):
        params['api_key'] = os.environ['OPENALEX_API_KEY']
    if os.getenv('OPENALEX_MAILTO'):
        params['mailto'] = os.environ['OPENALEX_MAILTO']
    async with httpx.AsyncClient(timeout=httpx.Timeout(6), follow_redirects=False) as client:
        for attempt in range(2):
            response = await client.get('https://api.openalex.org/works/https://doi.org/' + quote(doi, safe=''), params=params)
            if response.status_code in (429, 502, 503, 504) and attempt == 0:
                await asyncio.sleep(0.5)
                continue
            if response.status_code == 404:
                raise HTTPException(404, 'Artigo não encontrado no OpenAlex para este DOI.')
            if response.status_code == 429:
                raise HTTPException(503, 'Limite de consultas do OpenAlex atingido. Tente novamente em instantes.')
            if response.status_code in (401, 403):
                raise HTTPException(503, 'O OpenAlex recusou a consulta. Verifique a chave de API no backend.')
            response.raise_for_status()
            return response.json()

async def retrieve_paper(value):
    doi = normalize_doi(value)
    cache = cached(doi)
    if cache and cache[2] < int(os.getenv('MATILDA_CACHE_TTL', '86400')):
        return parse_paper(cache[0], doi, cache[1], True)
    try:
        async with asyncio.timeout(15):
            raw = await fetch_remote(doi)
        retrieved_at = datetime.now(timezone.utc).isoformat()
        paper = parse_paper(raw, doi, retrieved_at)
        save_cache(doi, raw, retrieved_at)
        return paper
    except HTTPException as exc:
        if exc.status_code in (404, 422):
            raise
        error = exc
    except (httpx.HTTPError, TimeoutError, ValueError, KeyError, TypeError) as exc:
        log.warning('academic_retrieval_failed error=%s', type(exc).__name__)
        error = HTTPException(503, 'Não foi possível consultar o OpenAlex. Verifique a conexão e tente novamente.')
    if cache:
        return parse_paper(cache[0], doi, cache[1], True, True)
    raise error
