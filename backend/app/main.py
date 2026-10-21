import logging
import os
import time
from datetime import datetime, timezone
from uuid import uuid4
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from app.integrations.openalex import retrieve_paper
from app.schemas import Analysis, AnalysisRequest, Paper, Graph, Evidence
from app.services.contribution_search import search_contributions
from app.services.graph_builder import build_graph
from app.services.storage import load_json, save_analysis, get_analysis

load_dotenv(Path(__file__).resolve().parents[2] / '.env')
logging.basicConfig(level=logging.INFO)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
log = logging.getLogger('matilda')
app = FastAPI(title='Matilda Forensics', version='0.1.0', description='Investigação documental de contribuições científicas. Relação temática não comprova influência histórica.')
app.add_middleware(CORSMiddleware, allow_origins=os.getenv('MATILDA_CORS_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(','), allow_methods=['GET', 'POST'], allow_headers=['Content-Type'])

@app.get('/api/health')
def health():
    return {'status':'ok', 'service':'matilda-forensics'}

@app.get('/api/papers/{doi:path}', response_model=Paper)
async def paper(doi: str):
    return await retrieve_paper(doi)

@app.post('/api/analyses', response_model=Analysis, status_code=201)
async def create_analysis(request: AnalysisRequest):
    started = time.monotonic()
    try:
        paper = await retrieve_paper(request.doi)
        matches = search_contributions(paper)
        warnings = list(paper.limitations)
        warnings.append('Catálogo inicial: 3 pesquisadoras e 6 contribuições em RNA e CRISPR; não representa toda a ciência.')
        if not matches:
            warnings.append('Não foram encontradas contribuições verificadas neste catálogo. Isso não indica inexistência de contribuições femininas.')
        graph = build_graph(paper, matches, warnings)
        analysis = Analysis(id=str(uuid4()), root_paper_id=paper.id, created_at=datetime.now(timezone.utc).isoformat(), paper=paper, contributions=matches, graph=graph, coverage_warnings=warnings, evidence_summary={'contributions':len(matches), 'documents':len({e.id for m in matches for e in m.evidence})})
        save_analysis(analysis)
        log.info('analysis_complete id=%s seconds=%.3f candidates=%d verified=%d warnings=%d', analysis.id, time.monotonic()-started, len(matches), len(matches), len(warnings))
        return analysis
    except HTTPException as exc:
        log.warning('analysis_failed status=%d seconds=%.3f', exc.status_code, time.monotonic()-started)
        raise

def find_analysis(identifier):
    result = get_analysis(identifier)
    if not result:
        raise HTTPException(404, 'Investigação não encontrada ou expirada (retenção: 7 dias).')
    return Analysis.model_validate(result)

@app.get('/api/analyses/{identifier}', response_model=Analysis)
def analysis(identifier: str):
    return find_analysis(identifier)

@app.get('/api/analyses/{identifier}/graph', response_model=Graph)
def graph(identifier: str):
    return find_analysis(identifier).graph

@app.get('/api/evidence/{identifier}', response_model=Evidence)
def evidence(identifier: str):
    for entry in load_json('evidence.json'):
        if entry['id'] == identifier:
            return entry
    raise HTTPException(404, 'Evidência não encontrada.')

@app.get('/api/analyses/{identifier}/export')
def export(identifier: str, format: str = 'markdown'):
    result = find_analysis(identifier)
    if format == 'json':
        return Response(result.model_dump_json(indent=2), media_type='application/json', headers={'Content-Disposition':f'attachment; filename="matilda-{identifier}.json"'})
    if format != 'markdown':
        raise HTTPException(422, 'Formato suportado: markdown ou json.')
    lines = ['# Matilda Forensics', '', result.paper.title, 'DOI: https://doi.org/'+result.paper.doi, 'Fonte: '+result.paper.source_url, 'Metadados recuperados em: '+result.paper.retrieved_at, 'Cache: '+str(result.paper.from_cache), '']
    for match in result.contributions:
        lines += ['## '+match.contribution.title, match.contribution.description, '', 'Pesquisadoras: '+', '.join(r.name for r in match.researchers), 'Participantes da publicação: '+', '.join(match.contribution.participants), 'Relação: '+match.relation_type, 'Comparação bibliográfica: '+match.citation_status, match.explanation]
        for evidence in match.evidence:
            lines += ['Fonte: '+evidence.source_title, evidence.source_url, 'Localização: '+evidence.excerpt_or_location, 'Afirmação sustentada: '+evidence.claim_supported]
        lines += ['Limitações:'] + ['- '+w for w in match.limitations] + ['']
    lines += ['## Cobertura e limitações'] + ['- '+w for w in result.coverage_warnings]
    return Response('\n'.join(lines), media_type='text/markdown; charset=utf-8', headers={'Content-Disposition':f'attachment; filename="matilda-{identifier}.md"'})
