import httpx
import pytest
from fastapi import HTTPException
from app.integrations import openalex

@pytest.mark.parametrize('status,expected',[(404,404),(429,503),(401,503),(403,503),(500,503)])
def test_remote_errors(client,monkeypatch,status,expected):
    original=httpx.AsyncClient
    attempts=[]
    def handler(request):
        attempts.append(request)
        return httpx.Response(status,json={'error':'upstream'})
    monkeypatch.setattr(openalex.httpx,'AsyncClient',lambda **kwargs: original(**kwargs, transport=httpx.MockTransport(handler)))
    response=client.post('/api/analyses',json={'doi':'10.9999/not-in-cache'})
    assert response.status_code==expected
    assert len(attempts)==(2 if status==429 else 1)
    assert 'api_key' not in response.text

def test_stale_cache_fallback(client,monkeypatch):
    monkeypatch.setenv('MATILDA_CACHE_TTL','0')
    async def fail(doi):
        raise HTTPException(503,'temporarily unavailable')
    monkeypatch.setattr(openalex,'fetch_remote',fail)
    paper=client.get('/api/papers/10.1126/science.1225829').json()
    assert paper['from_cache'] and paper['cache_stale']
    assert any('cache anterior' in w for w in paper['limitations'])

def test_network_timeout(client,monkeypatch):
    async def timeout(doi):
        raise httpx.ReadTimeout('timeout')
    monkeypatch.setattr(openalex,'fetch_remote',timeout)
    response=client.post('/api/analyses',json={'doi':'10.9999/no-cache'})
    assert response.status_code==503

def test_not_found_does_not_silently_use_old_cache(client,monkeypatch):
    monkeypatch.setenv('MATILDA_CACHE_TTL','0')
    async def missing(doi):
        raise HTTPException(404,'Artigo não encontrado')
    monkeypatch.setattr(openalex,'fetch_remote',missing)
    assert client.get('/api/papers/10.1126/science.1225829').status_code==404
