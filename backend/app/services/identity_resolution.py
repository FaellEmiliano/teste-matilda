"""Resolve only exact persistent identifiers. Never match gender by name."""
import re
from app.integrations.discovery_sources import query_source, safe_url
from app.schemas.catalog import IdentityObservation
from app.services.storage import load_json

WOMAN_IDS = {'Q6581072', 'Q1052281'}


def build_query(orcids, openalex_ids=()):
    # Values arrive only from the strict ORCID normalizer, never free user text.
    values = ' '.join('"' + identifier + '"' for identifier in sorted({value for value in orcids if re.fullmatch(r'\d{4}-\d{4}-\d{4}-\d{3}[\dX]', value)}))
    openalex_values = ' '.join('"' + identifier + '"' for identifier in sorted({value for value in openalex_ids if re.fullmatch(r'A\d+', value)}))
    return '''SELECT ?person ?orcid ?openalex ?gender ?referenceUrl ?referenceWork WHERE {
      { VALUES ?orcid { ''' + values + ''' } ?person wdt:P496 ?orcid. }
      UNION
      { VALUES ?openalex { ''' + openalex_values + ''' } ?person wdt:P10283 ?openalex. }
      ?person wdt:P31 wd:Q5; p:P21 ?statement.
      ?statement ps:P21 ?gender; wikibase:rank ?rank.
      FILTER(?rank != wikibase:DeprecatedRank)
      OPTIONAL { ?statement prov:wasDerivedFrom ?reference.
        OPTIONAL { ?reference pr:P854 ?referenceUrl. }
        OPTIONAL { ?reference pr:P248 ?referenceWork. }
      }
    } LIMIT 500'''


def observations_from_bindings(author, bindings):
    matching = [row for row in bindings if isinstance(row, dict) and ((author.orcid is not None and row.get('orcid', {}).get('value') == author.orcid) or (author.openalex_id is not None and row.get('openalex', {}).get('value') == author.openalex_id.rsplit('/', 1)[-1]))]
    method = 'wikidata_orcid' if any(row.get('orcid', {}).get('value') == author.orcid and author.orcid for row in matching) else 'wikidata_openalex_id'
    base = dict(author_name=author.name, author_openalex_id=author.openalex_id, orcid=author.orcid)
    people = {row.get('person', {}).get('value') for row in matching}
    people.discard(None)
    if not matching:
        return IdentityObservation(**base, status='unknown', method='unresolved', explanation='Sem correspondência exata de identificador persistente com informação de identidade utilizável.')
    if len(people) != 1 or any(not re.fullmatch(r'https?://www.wikidata.org/entity/Q\d+', str(person)) for person in people):
        return IdentityObservation(**base, status='conflicting', method=method, explanation='Identificador associado a identidades ambíguas; revisão necessária.')
    person = next(iter(people))
    qid = person.rsplit('/', 1)[-1]
    genders = {row.get('gender', {}).get('value', '').rsplit('/', 1)[-1] for row in matching}
    if not genders or not genders.issubset(WOMAN_IDS):
        # We do not classify other genders or treat them as evidence of absence.
        return IdentityObservation(**base, wikidata_id=qid, status='conflicting' if genders & WOMAN_IDS else 'unknown', method=method, source_urls=['https://www.wikidata.org/wiki/'+qid], explanation='Os dados não permitem confirmar a identificação como mulher para esta investigação.')
    references = set()
    for row in matching:
        for field in ('referenceUrl', 'referenceWork'):
            url = safe_url(row.get(field, {}).get('value'))
            if url:
                references.add(url)
    return IdentityObservation(**base, wikidata_id=qid, status='documented_woman' if references else 'reported_without_reference', method=method, source_urls=['https://www.wikidata.org/wiki/'+qid] + sorted(references), explanation='Identificador persistente corresponde exatamente ao item Wikidata com declaração explícita de gênero e referência.' if references else 'Declaração explícita no Wikidata, mas sem referência documental recuperada; identidade pendente.')


async def resolve_identities(client, works, warnings, sources):
    curated = {row.get('openalex_id'): row for row in load_json('researchers.json') if row.get('identity_status') == 'verified' and row.get('openalex_id') and row.get('verification_sources')}
    authors = [author for work in works for author in work.authors]
    orcids = sorted({a.orcid for a in authors if a.orcid and a.openalex_id not in curated})
    selected = orcids[:40]
    all_openalex_ids = sorted({a.openalex_id.rsplit('/', 1)[-1] for a in authors if a.openalex_id and a.openalex_id not in curated and re.fullmatch(r'https://openalex.org/A\d+', a.openalex_id)})
    openalex_ids = all_openalex_ids[:40]
    if len(all_openalex_ids) > 40:
        warnings.append('Identidades: consulta limitada a 40 IDs OpenAlex por investigação.')
    if len(orcids) > 40:
        warnings.append('Identidades: consulta limitada a 40 ORCIDs por investigação; demais identidades permanecem pendentes.')
    bindings = []
    if selected or openalex_ids:
        from app.integrations.discovery_sources import DiscoverySourceError
        try:
            payload, observation = await query_source(client, 'wikidata', {'query': build_query(selected, openalex_ids), 'format': 'json'})
            sources.append(observation)
            bindings = payload.get('results', {}).get('bindings', [])
            if not isinstance(bindings, list):
                raise DiscoverySourceError('wikidata: resposta inválida.')
        except DiscoverySourceError as exc:
            warnings.append(str(exc))
    else:
        warnings.append('Nenhum identificador persistente novo disponível para consulta ao Wikidata. Não foram usados nomes para inferir identidade.')
    results = {}
    for work in works:
        identities = []
        for author in work.authors:
            known = curated.get(author.openalex_id)
            if known:
                identities.append(IdentityObservation(author_name=author.name, author_openalex_id=author.openalex_id, orcid=author.orcid, status='documented_woman', method='curated_persistent_id', source_urls=known['verification_sources'], explanation='Identificador OpenAlex corresponde exatamente à identidade no catálogo editorial revisado.'))
            else:
                identities.append(observations_from_bindings(author, bindings))
        results[work.doi] = identities
    return results
