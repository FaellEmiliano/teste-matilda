"""Bounded access to fixed public academic endpoints, with provenance-aware cache."""
import asyncio
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from urllib.parse import urlparse
import httpx
from fastapi import HTTPException
from app.integrations.openalex import normalize_doi, abstract_text
from app.schemas.catalog import CandidateAuthor, CandidateWork, SourceObservation
from app.services.storage import external_cached, save_external_cache

ENDPOINTS = {
    'openalex': 'https://api.openalex.org/works',
    'europe_pmc': 'https://www.ebi.ac.uk/europepmc/webservices/rest/search',
    'wikidata': 'https://query.wikidata.org/sparql',
}


def now():
    return datetime.now(timezone.utc).isoformat()


def safe_url(value):
    if not isinstance(value, str):
        return None
    parsed = urlparse(value)
    return value if parsed.scheme in ('http', 'https') and parsed.hostname and not parsed.username else None


def orcid_id(value):
    if not isinstance(value, str):
        return None
    value = re.sub(r'^https?://orcid.org/', '', value.strip())
    return value if re.fullmatch(r'\d{4}-\d{4}-\d{4}-\d{3}[\dX]', value) else None


class DiscoverySourceError(Exception):
    pass


async def query_source(client, source, params):
    endpoint = ENDPOINTS[source]
    key = hashlib.sha256(json.dumps([source, params], sort_keys=True).encode()).hexdigest()
    cached = external_cached(key)
    if cached:
        return cached[0], SourceObservation(source=source, source_url=endpoint, retrieved_at=cached[1], from_cache=True, query=params)
    actual_params = dict(params)
    if source == 'openalex' and os.getenv('OPENALEX_API_KEY'):
        actual_params['api_key'] = os.environ['OPENALEX_API_KEY']
    if source == 'openalex' and os.getenv('OPENALEX_MAILTO'):
        actual_params['mailto'] = os.environ['OPENALEX_MAILTO']
    try:
        for attempt in range(2):
            response = await client.get(endpoint, params=actual_params, headers={'Accept': 'application/sparql-results+json' if source == 'wikidata' else 'application/json'})
            if response.status_code in (429, 502, 503, 504) and attempt == 0:
                await asyncio.sleep(0.3)
                continue
            response.raise_for_status()
            if len(response.content) > 6_000_000:
                raise DiscoverySourceError(source + ': resposta excedeu o limite de tamanho.')
            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError('Expected an object')
            retrieved_at = now()
            save_external_cache(key, payload, retrieved_at)
            return payload, SourceObservation(source=source, source_url=endpoint, retrieved_at=retrieved_at, query=params)
    except (httpx.HTTPError, ValueError, TypeError):
        # Do not expose upstream URLs: they can include API credentials.
        raise DiscoverySourceError(source + ': consulta indisponível ou resposta inválida.') from None


def parse_openalex_work(raw, source):
    try:
        doi = normalize_doi(raw.get('doi') or '')
    except HTTPException:
        return None
    if not re.fullmatch(r'https://openalex.org/W\d+', raw.get('id', '')) or not raw.get('title'):
        return None
    authors = []
    for item in raw.get('authorships') or []:
        author = item.get('author') or {}
        if author.get('display_name'):
            identifier = author.get('id')
            authors.append(CandidateAuthor(name=author['display_name'], openalex_id=identifier if isinstance(identifier, str) and re.fullmatch(r'https://openalex.org/A\d+', identifier) else None, orcid=orcid_id(author.get('orcid'))))
    return CandidateWork(doi=doi, title=raw['title'], openalex_id=raw['id'], year=raw.get('publication_year'), authors=authors, abstract=abstract_text(raw.get('abstract_inverted_index')), topics=[t['display_name'] for t in raw.get('topics') or [] if t.get('display_name')], sources=[source])


def parse_epmc_work(raw, source):
    from html import unescape
    try:
        doi = normalize_doi(raw.get('doi') or '')
    except HTTPException:
        return None
    if not raw.get('title'):
        return None
    # The adapter strips markup; excerpts are plain text, never rendered as HTML.
    abstract = unescape(re.sub(r'<[^>]+>', ' ', raw.get('abstractText') or '')).strip() or None
    authors = []
    for author in (raw.get('authorList') or {}).get('author', []):
        name = author.get('fullName') or author.get('collectiveName')
        if not name:
            continue
        ids = (author.get('authorId') or {}).get('value')
        kind = (author.get('authorId') or {}).get('type')
        authors.append(CandidateAuthor(name=name, orcid=orcid_id(ids) if kind == 'ORCID' else None))
    year = str(raw.get('pubYear') or '')
    return CandidateWork(doi=doi, title=raw['title'], year=int(year) if year.isdigit() else None, authors=authors, abstract=abstract, sources=[source])


def topic_ids(raw):
    return [t['id'].rsplit('/', 1)[-1] for t in (raw.get('topics') or [])[:2] if re.fullmatch(r'https://openalex.org/T\d+', t.get('id', ''))]


def epmc_search_term(raw):
    # Queries derive from the input record; there is no domain or researcher list.
    keywords = [x.get('display_name', '') for x in (raw.get('keywords') or [])[:3]]
    terms = keywords or [raw.get('title') or '']
    return ' '.join(re.findall(r'[\w-]+', terms[0], flags=re.UNICODE)[:6])[:120]
