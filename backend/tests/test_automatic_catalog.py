"""Synthetic upstream fixtures exercise invariants; no fabricated records ship as science."""
import asyncio
import json
import httpx
import pytest
from app.integrations import discovery_sources
from app.services import automatic_catalog
from app.services.identity_resolution import observations_from_bindings, build_query
from app.schemas.catalog import CandidateAuthor, CandidateWork, SourceObservation
from app.services.storage import get_candidate, list_candidates

ORCID = '0000-0002-1825-0097'
OTHER_ORCID = '0000-0001-2345-6789'


def row(orcid=ORCID, person='Q123', gender='Q6581072', reference='https://institution.example/biography', openalex=None):
    value = {'person':{'value':'http://www.wikidata.org/entity/'+person}, 'gender':{'value':'http://www.wikidata.org/entity/'+gender}}
    if orcid:
        value['orcid']={'value':orcid}
    if openalex:
        value['openalex']={'value':openalex}
    if reference:
        value['referenceUrl']={'value':reference}
    return value


def author(**kwargs):
    return CandidateAuthor(name=kwargs.get('name','Autora da fixture'), openalex_id=kwargs.get('openalex_id','https://openalex.org/A999123'), orcid=kwargs.get('orcid',ORCID))


def oa_work(doi='10.9999/example', identifier='W999123', abstract=True):
    return {'id':'https://openalex.org/'+identifier,'doi':'https://doi.org/'+doi,'title':'Trabalho sintético para teste','publication_year':2024,'authorships':[{'author':{'id':'https://openalex.org/A999123','display_name':'Autora da fixture','orcid':'https://orcid.org/'+ORCID}},{'author':{'id':'https://openalex.org/A999124','display_name':'Outra pessoa'}}],'abstract_inverted_index':{'We':[0],'show':[1],'a':[2],'result.':[3]} if abstract else None,'topics':[{'id':'https://openalex.org/T999','display_name':'Tema fora do catálogo manual','score':0.9}]}


@pytest.mark.parametrize('bindings,status', [([row()],'documented_woman'),([row(reference=None)],'reported_without_reference'),([row(reference='javascript:alert(1)')],'reported_without_reference'),([row(orcid=OTHER_ORCID)],'unknown'),([row(),row(person='Q124')],'conflicting'),([row(),row(gender='Q6581097')],'conflicting'),([],'unknown')])
def test_identity_requires_exact_id_and_explicit_source(bindings,status):
    result=observations_from_bindings(author(),bindings)
    assert result.status==status
    assert not any(url.startswith('javascript:') for url in result.source_urls)


def test_same_name_is_not_an_identity_match():
    assert observations_from_bindings(author(orcid=None,openalex_id=None),[row()]).status=='unknown'


def test_exact_openalex_id_can_resolve_without_orcid():
    result=observations_from_bindings(author(orcid=None),[row(orcid=None,openalex='A999123')])
    assert result.status=='documented_woman'
    assert result.method=='wikidata_openalex_id'


def test_query_rejects_injected_identifiers():
    query=build_query([ORCID, '" } UNION { ?a ?b ?c } #'],['A999123','A123"bad'])
    assert ORCID in query and 'A999123' in query
    assert '?a ?b ?c' not in query and 'A123"bad' not in query
    assert 'DeprecatedRank' in query


def install_transport(monkeypatch,handler):
    original=httpx.AsyncClient
    monkeypatch.setattr(discovery_sources.httpx,'AsyncClient',lambda **kwargs:original(**kwargs,transport=httpx.MockTransport(handler)))


def handler(request):
    if request.url.host=='api.openalex.org':
        return httpx.Response(200,json={'results':[oa_work(),oa_work(doi='10.9999/EXAMPLE'),oa_work(doi='10.9999/no-abstract',identifier='W999125',abstract=False)]})
    if request.url.host=='www.ebi.ac.uk':
        return httpx.Response(200,json={'resultList':{'result':[{'doi':'10.9999/no-abstract','title':'Trabalho sintético para teste','pubYear':'2024','abstractText':'<p>We demonstrate a second result.</p>'}]}})
    if request.url.host=='query.wikidata.org':
        return httpx.Response(200,json={'results':{'bindings':[row()]}})
    raise AssertionError('Unexpected host')


def create(client):
    response=client.post('/api/analyses',json={'doi':'10.1126/science.1231143'})
    assert response.status_code==201
    return response.json()


def test_expansion_persistence_provenance_no_promotion(client,monkeypatch):
    monkeypatch.setenv('OPENALEX_API_KEY','fixture-secret-never-store')
    install_transport(monkeypatch,handler)
    original=create(client)
    response=client.post('/api/analyses/'+original['id']+'/discovery')
    assert response.status_code==200,response.text
    result=response.json();run=result['external_discovery']
    assert run['status']=='complete'
    assert len(run['candidates'])==2
    assert result['contributions']==original['contributions']
    assert result['graph']==original['graph']
    for match in run['candidates']:
        candidate=match['candidate']
        assert candidate['verification_status']=='pending_review'
        assert candidate['record_state']=='automatically_extracted'
        assert candidate['excerpt'] in ('We show a result.','We demonstrate a second result.')
        assert any(identity['status']=='documented_woman' for identity in candidate['identities'])
        assert candidate['work']['sources'] and match['retrieval_reasons']
    assert any(c['candidate']['work']['doi']=='10.9999/no-abstract' and c['candidate']['work']['abstract'] for c in run['candidates'])
    listing=client.get('/api/catalog/candidates').json()
    assert listing['total']==2
    candidate_id=listing['items'][0]['id']
    assert len(client.get('/api/catalog/candidates/'+candidate_id).json()['revisions'])==1
    assert client.get('/api/analyses/'+original['id']).json()['external_discovery']==run
    repeated=client.post('/api/analyses/'+original['id']+'/discovery').json()
    assert any(source['from_cache'] for source in repeated['external_discovery']['sources'])
    assert client.get('/api/catalog/candidates').json()['total']==2
    # First cache transition is a new observation; repeating the cached run is idempotent.
    client.post('/api/analyses/'+original['id']+'/discovery')
    revision_count=len(client.get('/api/catalog/candidates/'+candidate_id).json()['revisions'])
    assert revision_count==2
    exported=client.get('/api/analyses/'+original['id']+'/export?format=markdown').text
    assert 'pendente de revisão' in exported and '10.9999/example' in exported
    assert 'fixture-secret-never-store' not in response.text
    assert 'fixture-secret-never-store' not in json.dumps(client.get('/api/catalog/candidates/'+candidate_id).json())


def test_bounded_pagination_and_404(client):
    assert client.get('/api/catalog/candidates?limit=101').status_code==422
    assert client.get('/api/catalog/candidates?offset=-1').status_code==422
    assert client.get('/api/catalog/candidates/missing').status_code==404
    assert client.post('/api/analyses/missing/discovery').status_code==404


def test_all_sources_unavailable_preserves_editorial_results(client,monkeypatch):
    install_transport(monkeypatch,lambda request:httpx.Response(503,json={'error':'down'}))
    original=create(client)
    result=client.post('/api/analyses/'+original['id']+'/discovery').json()
    assert result['external_discovery']['status']=='unavailable'
    assert result['external_discovery']['candidates']==[]
    assert result['contributions']==original['contributions']
    assert client.get('/api/catalog/candidates').json()['total']==0


def test_malformed_upstream_work_is_skipped(client,monkeypatch):
    def malformed(request):
        if request.url.host=='api.openalex.org':
            invalid=oa_work();invalid['publication_year']={'bad':'data'}
            return httpx.Response(200,json={'results':[invalid,oa_work()]})
        return handler(request)
    install_transport(monkeypatch,malformed)
    result=client.post('/api/analyses/'+create(client)['id']+'/discovery').json()
    assert any('registro incompatível' in warning for warning in result['external_discovery']['warnings'])
    assert result['external_discovery']['candidates']


def test_partial_timeout_preserves_completed_query(client,monkeypatch):
    async def partial(http_client,source,params):
        if source=='europe_pmc':
            await asyncio.sleep(1.1)
        return {'results':[oa_work()]},SourceObservation(source=source,source_url='https://api.openalex.org/works',retrieved_at='2026-10-21T00:00:00+00:00')
    monkeypatch.setattr(automatic_catalog,'query_source',partial)
    monkeypatch.setitem(automatic_catalog.LIMITS,'timeout_seconds',1)
    result=client.post('/api/analyses/'+create(client)['id']+'/discovery').json()['external_discovery']
    assert result['status']=='partial'
    assert len(result['candidates'])==1
    assert any('Tempo limite' in warning for warning in result['warnings'])


def test_dynamic_topics_are_not_limited_to_editorial_vocabulary(client):
    from app.services.concept_analysis import extract_concepts
    concepts=extract_concepts(oa_work(),None)
    assert any(concept.name=='Tema fora do catálogo manual' for concept in concepts)


def test_missing_abstract_stays_metadata_only():
    work=CandidateWork(doi='10.9999/a',title='Teste')
    candidate=automatic_catalog.extract_candidate(work,[])
    assert candidate.record_state=='retrieved'
    assert candidate.excerpt is None
    assert candidate.verification_status=='pending_review'


def test_result_excerpt_is_a_literal_source_passage():
    work=CandidateWork(doi='10.9999/a',title='Teste',abstract='Background context. We demonstrate the measured result. Further context.')
    candidate=automatic_catalog.extract_candidate(work,[])
    assert candidate.excerpt=='We demonstrate the measured result.'
    assert candidate.excerpt in work.abstract
    assert 'marcadores textuais' in candidate.excerpt_location


def test_wrong_doi_in_abstract_enrichment_is_not_merged(client,monkeypatch):
    def wrong_doi(request):
        if request.url.host=='www.ebi.ac.uk':
            if request.url.params.get('query','').startswith('DOI:'):
                return httpx.Response(200,json={'resultList':{'result':[{'doi':'10.9999/unrelated','title':'Wrong paper','abstractText':'This is not the requested source.'}]}})
            return httpx.Response(200,json={'resultList':{'result':[]}})
        return handler(request)
    install_transport(monkeypatch,wrong_doi)
    run=client.post('/api/analyses/'+create(client)['id']+'/discovery').json()['external_discovery']
    assert all(connection['candidate']['work']['doi']!='10.9999/unrelated' for connection in run['candidates'])
    candidate=next(connection['candidate'] for connection in run['candidates'] if connection['candidate']['work']['doi']=='10.9999/no-abstract')
    assert candidate['excerpt'] is None


def test_discovery_rate_limit_retries_then_recovers(client,monkeypatch):
    attempts={}
    def limited(request):
        key=str(request.url)
        attempts[key]=attempts.get(key,0)+1
        if request.url.host=='api.openalex.org' and attempts[key]==1:
            return httpx.Response(429,json={'error':'rate limited'})
        return handler(request)
    install_transport(monkeypatch,limited)
    run=client.post('/api/analyses/'+create(client)['id']+'/discovery').json()['external_discovery']
    assert run['status']=='complete'
    assert any(count==2 for count in attempts.values())


def test_curated_person_without_persistent_id_does_not_match_unknown_author(monkeypatch):
    from app.services import identity_resolution
    monkeypatch.setattr(identity_resolution,'load_json',lambda name:[{'openalex_id':None,'identity_status':'verified','verification_sources':['https://institution.example/person']}])
    work=CandidateWork(doi='10.9999/no-id',title='Teste',authors=[CandidateAuthor(name='Mesmo nome')])
    identities=asyncio.run(identity_resolution.resolve_identities(None,[work],[],[]))
    assert identities[work.doi][0].status=='unknown'
