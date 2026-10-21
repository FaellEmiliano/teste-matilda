"""Build the small editorial catalog from explicit claims and retrieved metadata."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
def write(name, value):
    (DATA / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
concepts = [
 ('crispr','CRISPR', ['crispr','crisprs','clustered regularly interspaced short palindromic repeats']),
 ('cas9','Cas9', ['cas9','crispr-cas9','crispr/cas']),
 ('genome-editing','Edição genômica',['genome editing','genome engineering','gene editing','edição genômica','genomic manipulation']),
 ('mrna','RNA mensageiro',['mrna','messenger rna','rna mensageiro']),
 ('nucleoside','Modificação de nucleosídeos',['pseudouridine','nucleoside modification','modified nucleosides','modified nucleotides','nucleoside-modified','nucleoside modification']),
 ('rna-immunity','Reconhecimento imune de RNA',['toll-like','immunogenicity','immunogenic','rna recognition','interferon-alpha']),
]
write('concepts.json',[{'id':i,'name':n,'aliases':list(dict.fromkeys(a))} for i,n,a in concepts])
researchers=[
 {'id':'kariko','name':'Katalin Karikó','openalex_id':'https://openalex.org/A5030598859','research_areas':['RNA mensageiro','Imunologia'],'identity_status':'verified','verification_sources':['https://www.nobelprize.org/prizes/medicine/2023/kariko/facts/']},
 {'id':'doudna','name':'Jennifer A. Doudna','openalex_id':'https://openalex.org/A5067184382','research_areas':['CRISPR','Bioquímica'],'identity_status':'verified','verification_sources':['https://www.nobelprize.org/prizes/chemistry/2020/doudna/facts/']},
 {'id':'charpentier','name':'Emmanuelle Charpentier','openalex_id':'https://openalex.org/A5074743574','research_areas':['CRISPR','Microbiologia'],'identity_status':'verified','verification_sources':['https://www.nobelprize.org/prizes/chemistry/2020/charpentier/facts/']},
]
for researcher, nobel_id in zip(researchers, ['1024', '992', '991']):
    researcher['verification_sources'].append('https://api.nobelprize.org/2.1/laureate/' + nobel_id)
write('researchers.json',researchers)
rows=[
 ('rna-2005','Modificações de nucleosídeos e reconhecimento imune de RNA','O trabalho de Karikó, Buckstein, Ni e Weissman investiga a supressão do reconhecimento de RNA por receptores Toll-like a partir de modificações de nucleosídeos.',['kariko'],['mrna','nucleoside','rna-immunity'],'10.1016/j.immuni.2005.06.008','Biologia molecular e RNA','Título e resumo da publicação, Immunity 23(2), 165–175.'),
 ('rna-2008','Pseudouridina: tradução e estabilidade de mRNA','Em experimentos com células, lisados e camundongos, a equipe observou maior capacidade de tradução e menor imunogenicidade de mRNAs contendo pseudouridina, nas condições estudadas.',['kariko'],['mrna','nucleoside','rna-immunity'],'10.1038/mt.2008.200','Biologia molecular e RNA','Resumo: comparação de mRNA com pseudouridina e mRNA não modificado; Molecular Therapy 16, 1833–1840.'),
 ('crispr-2011','Maturação de RNA CRISPR com tracrRNA e RNase III','Deltcheva e colaboradores, incluindo Emmanuelle Charpentier, documentaram a participação de um pequeno RNA transcrito em trans e da RNase III na maturação de RNAs CRISPR.',['charpentier'],['crispr'],'10.1038/nature09886','Genética e edição genômica','Título e resumo; Nature 471, 602–607. A contribuição é coletiva.'),
 ('crispr-2012','Cas9 programável guiada por dois RNAs','Jínek e colaboradores, incluindo Doudna e Charpentier, demonstraram a clivagem de DNA por Cas9 guiada por crRNA e tracrRNA e por um RNA quimérico, indicando potencial para edição genômica programável.',['doudna','charpentier'],['crispr','cas9','genome-editing'],'10.1126/science.1225829','Genética e edição genômica','Resumo: mecanismo de dois RNAs e RNA quimérico; Science 337(6096), 816–821.'),
 ('crispr-2010','Processamento específico de pre-crRNA por Csy4','Haurwitz e colaboradores, incluindo Jennifer Doudna, identificaram Csy4 como endorribonuclease responsável pelo processamento de transcritos CRISPR em Pseudomonas aeruginosa e descreveram seu reconhecimento de RNA.',['doudna'],['crispr'],'10.1126/science.1192272','Genética e edição genômica','Resumo: identificação de Csy4 e estrutura cristalográfica de 1,8 Å; Science 329(5997), 1355–1358.'),
 ('crispr-2014','Síntese dos mecanismos e aplicações de CRISPR-Cas9','Doudna e Charpentier revisaram a história, o mecanismo e as aplicações da tecnologia CRISPR-Cas9. Esta contribuição é uma síntese científica, não uma nova descoberta experimental.',['doudna','charpentier'],['crispr','cas9','genome-editing'],'10.1126/science.1258096','Genética e edição genômica','Resumo e revisão; Science 346(6213), 1258096.'),
]
contributions=[]; evidence=[]
for identifier,title,description,people,concept_ids,doi,field,location in rows:
    raw=json.loads((DATA/'openalex_snapshots'/(doi.replace('/','_')+'.json')).read_text())['data']
    contributions.append({'id':identifier,'title':title,'description':description,'researcher_ids':people,'participants':[a['author']['display_name'] for a in raw['authorships']],'concept_ids':concept_ids,'related_dois':[doi],'scientific_field':field,'verification_status':'verified'})
    evidence.append({'id':'evidence-'+identifier,'contribution_id':identifier,'claim_supported':description,'source_title':raw['title'],'source_url':'https://doi.org/'+doi,'source_type':'documental','excerpt_or_location':location,'verification_status':'verified'})
write('contributions.json',contributions); write('evidence.json',evidence)
