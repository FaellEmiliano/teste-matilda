from hashlib import sha256
from app.schemas import Graph, GraphNode, GraphEdge
from .gap_analysis import bibliography_index
from .storage import load_json

REFERENCE_LIMIT = 12

def build_graph(paper, matches, warnings):
    nodes = {}
    edges = {}
    def node(identifier, kind, label, **metadata):
        if identifier not in nodes:
            nodes[identifier] = GraphNode(id=identifier, type=kind, label=label, metadata=metadata)
        return identifier
    def edge(source, target, relation, explanation, evidence=None, status='verified'):
        key = sha256(f'{source}|{relation}|{target}'.encode()).hexdigest()[:24]
        edges[key] = GraphEdge(id=key, source=source, target=target, relation_type=relation, evidence_ids=evidence or [], verification_status=status, explanation=explanation)
    root = node(paper.id, 'PAPER', paper.title, doi=paper.doi, root=True)
    known_researchers = {r['openalex_id']: r for r in load_json('researchers.json') if r.get('openalex_id')}
    for author in paper.authors[:12]:
        node(author.id, 'RESEARCHER', author.name, catalog_id=known_researchers.get(author.id, {}).get('id'), curated_identity=author.id in known_researchers)
        edge(root, author.id, 'AUTHORED_BY', 'Autoria recuperada do OpenAlex.')
    for concept in paper.concepts:
        target = node('concept:'+concept.id, 'CONCEPT', concept.name, provenance=concept.provenance)
        edge(root, target, 'ADDRESSES', 'Termos identificados em: ' + ', '.join(concept.provenance), status='thematic')
    index = bibliography_index()
    relevant_ids = {index.get(doi) for m in matches for doi in m.contribution.related_dois}
    # Prefer relevant references while preserving a bounded graph.
    selected_refs = sorted(paper.referenced_work_ids, key=lambda ref: ref not in relevant_ids)[:REFERENCE_LIMIT]
    for ref in selected_refs:
        node(ref, 'PAPER', 'Referência '+ref.rsplit('/', 1)[-1], reference=True)
        edge(root, ref, 'CITES', 'Identificador presente em referenced_works do OpenAlex.')
    for match in matches:
        contribution = match.contribution
        cid = node('contribution:'+contribution.id, 'CONTRIBUTION', contribution.title, contribution_id=contribution.id)
        for concept in match.matched_concepts:
            edge(cid, 'concept:'+concept.id, 'RELATED_TO', match.explanation, status='thematic')
        for researcher in match.researchers:
            rid = node(researcher.openalex_id or 'researcher:'+researcher.id, 'RESEARCHER', researcher.name, catalog_id=researcher.id, curated_identity=True)
            edge(rid, cid, 'MADE_CONTRIBUTION', 'Participação coletiva documentada na publicação associada.', [e.id for e in match.evidence])
        for evidence in match.evidence:
            # A DOI source can be both an evidence node and a paper; each has a distinct meaning.
            eid = node(evidence.id, 'EVIDENCE', evidence.source_title, source_url=evidence.source_url, contribution_id=contribution.id)
            edge(cid, eid, 'SUPPORTED_BY', evidence.claim_supported, [evidence.id])
        for doi in contribution.related_dois:
            pid = index.get(doi)
            if pid and pid in nodes and pid != root:
                nodes[pid].label = match.evidence[0].source_title
    if len(paper.referenced_work_ids) > REFERENCE_LIMIT:
        warnings.append(f'Grafo limitado a {REFERENCE_LIMIT} de {len(paper.referenced_work_ids)} referências. A comparação usa todos os identificadores recuperados.')
    if len(paper.authors) > 12:
        warnings.append('Grafo limitado a 12 autores do artigo; a ficha bibliográfica preserva a lista completa.')
    return Graph(nodes=list(nodes.values()), edges=list(edges.values()), root_node=root, coverage_warnings=warnings)
