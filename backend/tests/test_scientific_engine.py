import json
from pathlib import Path
import pytest
from pydantic import ValidationError
from app.integrations.openalex import normalize_doi, parse_paper
from app.schemas import GraphEdge, Contribution
from app.services.gap_analysis import classify_citation
from app.services.storage import DATA, load_json
from app.services.contribution_search import search_contributions

@pytest.mark.parametrize('value', ['10.1126/science.1225829', ' https://doi.org/10.1126/SCIENCE.1225829 ', 'doi:10.1126/science.1225829', 'http://dx.doi.org/10.1126/science.1225829'])
def test_doi_normalization(value):
    assert normalize_doi(value) == '10.1126/science.1225829'

@pytest.mark.parametrize('value',['','https://evil.test/x','10.123/abc','10.1234/a b','10.1234/a?url=evil','10.1234/a#b'])
def test_invalid_doi(client,value):
    assert client.post('/api/analyses', json={'doi':value}).status_code == 422

@pytest.mark.parametrize('path', sorted((DATA/'openalex_snapshots').glob('*.json')), ids=lambda p:p.stem)
def test_ten_real_dois(client,path):
    raw=json.loads(path.read_text())['data']
    response=client.get('/api/papers/'+raw['doi'].replace('https://doi.org/',''))
    assert response.status_code == 200
    paper=response.json()
    assert paper['openalex_id']==raw['id']
    assert paper['title']==raw['title']
    assert paper['from_cache'] is True
    assert paper['retrieved_at']

@pytest.mark.parametrize('doi,minimum',[('10.1126/science.1231143',3),('10.1056/nejmoa2034577',2)])
def test_full_investigations(client,doi,minimum):
    response=client.post('/api/analyses',json={'doi':doi})
    assert response.status_code==201, response.text
    result=response.json()
    assert len(result['contributions'])>=minimum
    nodes=result['graph']['nodes'];edges=result['graph']['edges']
    ids={n['id'] for n in nodes}
    assert len(nodes)==len(ids)
    assert len(edges)==len({e['id'] for e in edges})
    for edge in edges:
        assert edge['source'] in ids and edge['target'] in ids
        assert edge['relation_type']!='DOCUMENTED_INFLUENCE'
        if edge['relation_type']=='CITES':
            assert edge['source']==result['paper']['id']
            assert edge['target'] in result['paper']['referenced_work_ids']
    for match in result['contributions']:
        assert match['relation_type']=='RELATED_TO'
        assert match['evidence'] and match['limitations']
        assert len(match['contribution']['participants'])>=len(match['researchers'])
        for evidence in match['evidence']:
            assert client.get('/api/evidence/'+evidence['id']).json()['source_url']==evidence['source_url']
    identifier=result['id']
    assert client.get('/api/analyses/'+identifier).json()['id']==identifier
    assert client.get('/api/analyses/'+identifier+'/graph').json()['root_node']==result['paper']['id']
    for format in ('markdown','json'):
        export=client.get(f'/api/analyses/{identifier}/export?format={format}')
        assert export.status_code==200
        assert 'attachment' in export.headers['Content-Disposition']
        assert 'https://doi.org/' in export.text
    assert client.get(f'/api/analyses/{identifier}/export?format=pdf').status_code==422

def get_paper(doi='10.1126/science.1225829'):
    snapshot=json.loads((DATA/'openalex_snapshots'/(doi.replace('/','_')+'.json')).read_text())
    return parse_paper(snapshot['data'],doi,snapshot['retrieved_at'])

def test_gap_all_classifications():
    paper=get_paper();contribution=Contribution(**load_json('contributions.json')[0]);work='https://openalex.org/W123'
    paper.referenced_work_ids=[work]
    assert classify_citation(paper,contribution,{contribution.related_dois[0]:work})=='CITED'
    assert classify_citation(paper,contribution,{contribution.related_dois[0]:'https://openalex.org/W999'})=='NOT_FOUND_IN_RETRIEVED_REFERENCES'
    assert classify_citation(paper,contribution,{})=='UNKNOWN'
    paper.references_status='unavailable'
    assert classify_citation(paper,contribution,{contribution.related_dois[0]:work})=='CITED'
    paper.referenced_work_ids=[]
    assert classify_citation(paper,contribution,{contribution.related_dois[0]:work})=='UNKNOWN'
    contribution.related_dois=[]
    assert classify_citation(paper,contribution,{})=='THEMATIC_ONLY'

def test_citation_matches_known_references(client):
    result=client.post('/api/analyses',json={'doi':'10.1126/science.1231143'}).json()
    assert any(m['citation_status']=='CITED' for m in result['contributions'])

def test_no_coverage(client):
    result=client.post('/api/analyses',json={'doi':'10.1038/171737a0'}).json()
    assert result['contributions']==[]
    assert any('não indica inexistência' in w for w in result['coverage_warnings'])

def test_no_abstract(client):
    result=client.get('/api/papers/10.1038/nature09886').json()
    assert result['abstract'] is None
    assert result['concepts']
    assert any('Resumo indisponível' in w for w in result['limitations'])

def test_wrong_record_identity():
    snapshot=json.loads(next((DATA/'openalex_snapshots').glob('*.json')).read_text())
    with pytest.raises(Exception) as exc:
        parse_paper(snapshot['data'],'10.9999/mismatch',snapshot['retrieved_at'])
    assert exc.value.status_code==502

def test_historical_relation_requires_evidence():
    with pytest.raises(ValidationError):
        GraphEdge(id='1',source='a',target='b',relation_type='DOCUMENTED_INFLUENCE',verification_status='verified',explanation='No source')

def test_insufficient_evidence_excluded(monkeypatch):
    from app.services import contribution_search as module
    real_load=module.load_json
    monkeypatch.setattr(module,'load_json',lambda name: [] if name=='evidence.json' else real_load(name))
    assert search_contributions(get_paper())==[]

def test_unknown_analyses_and_evidence(client):
    assert client.get('/api/analyses/not-found').status_code==404
    assert client.get('/api/evidence/not-found').status_code==404
    assert client.get('/api/health').json()['status']=='ok'
