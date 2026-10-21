from app.schemas import Contribution, Evidence, Researcher, DiscoveryMatch
from .storage import load_json
from .gap_analysis import bibliography_index, classify_citation

def search_contributions(paper):
    contributions = [Contribution(**x) for x in load_json('contributions.json')]
    evidence = [Evidence(**x) for x in load_json('evidence.json')]
    people = {x['id']: Researcher(**x) for x in load_json('researchers.json')}
    index = bibliography_index()
    matches = []
    for contribution in contributions:
        concepts = [c for c in paper.concepts if c.id in contribution.concept_ids]
        sources = [e for e in evidence if e.contribution_id == contribution.id and e.verification_status == 'verified' and e.source_type in ('documental', 'historical')]
        researchers = [people[i] for i in contribution.researcher_ids]
        if contribution.scientific_field == 'Biologia molecular e RNA' and not any(c.id in ('mrna', 'nucleoside') for c in concepts):
            continue
        if not concepts or not sources or contribution.verification_status != 'verified' or any(r.identity_status != 'verified' for r in researchers):
            continue
        names = ', '.join(c.name for c in concepts)
        status = classify_citation(paper, contribution, index)
        limitations = ['A contribuição está documentada; a conexão conceitual com o artigo não comprova influência histórica direta.', 'A autoria é coletiva. A lista de participantes preserva os coautores da publicação associada.']
        if status == 'NOT_FOUND_IN_RETRIEVED_REFERENCES':
            limitations.append('Publicação não localizada apenas nas referências recuperadas; a bibliografia completa não foi auditada.')
        if status == 'UNKNOWN':
            limitations.append('Dados insuficientes para determinar citação; o artigo não pode citar a si próprio.')
        matches.append(DiscoveryMatch(contribution=contribution, researchers=researchers, evidence=sources, matched_concepts=concepts, citation_status=status, explanation=f'O artigo e esta contribuição compartilham os conceitos: {names}. A fonte documenta a contribuição descrita. Essa correspondência é temática; uma citação, quando identificada, é registrada separadamente.', limitations=limitations, relevance=len(concepts)))
    return sorted(matches, key=lambda m: (-m.relevance, m.contribution.id))
