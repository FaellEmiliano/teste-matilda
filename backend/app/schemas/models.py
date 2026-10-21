from .catalog import DiscoveryRun
from enum import StrEnum
from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator

class Relation(StrEnum):
    CITES = 'CITES'
    AUTHORED_BY = 'AUTHORED_BY'
    ADDRESSES = 'ADDRESSES'
    MADE_CONTRIBUTION = 'MADE_CONTRIBUTION'
    RELATED_TO = 'RELATED_TO'
    SUPPORTED_BY = 'SUPPORTED_BY'
    DOCUMENTED_INFLUENCE = 'DOCUMENTED_INFLUENCE'

class Concept(BaseModel):
    id: str
    name: str
    aliases: list[str] = []
    provenance: list[str] = []

class Author(BaseModel):
    id: str
    name: str

class Paper(BaseModel):
    id: str
    doi: str
    openalex_id: str
    title: str
    abstract: str | None = None
    year: int | None = None
    authors: list[Author] = []
    concepts: list[Concept] = []
    referenced_work_ids: list[str] = []
    references_status: Literal['retrieved_unverified_completeness', 'unavailable']
    source_url: str
    retrieved_at: str
    from_cache: bool = False
    cache_stale: bool = False
    limitations: list[str] = []

class Researcher(BaseModel):
    id: str
    name: str
    research_areas: list[str]
    identity_status: Literal['verified', 'pending']
    verification_sources: list[str]
    openalex_id: str | None = None
    orcid: str | None = None

class Contribution(BaseModel):
    id: str
    title: str
    description: str
    researcher_ids: list[str]
    participants: list[str]
    concept_ids: list[str]
    related_dois: list[str]
    scientific_field: str
    verification_status: Literal['verified', 'pending']

class Evidence(BaseModel):
    id: str
    contribution_id: str
    claim_supported: str
    source_title: str
    source_url: str
    source_type: Literal['documental', 'historical', 'bibliographic', 'thematic']
    excerpt_or_location: str
    verification_status: Literal['verified', 'pending']

class DiscoveryMatch(BaseModel):
    contribution: Contribution
    researchers: list[Researcher]
    evidence: list[Evidence]
    matched_concepts: list[Concept]
    relation_type: Literal['RELATED_TO'] = 'RELATED_TO'
    citation_status: Literal['CITED', 'NOT_FOUND_IN_RETRIEVED_REFERENCES', 'UNKNOWN', 'THEMATIC_ONLY']
    explanation: str
    limitations: list[str]
    relevance: int

class GraphNode(BaseModel):
    id: str
    type: Literal['PAPER', 'RESEARCHER', 'CONCEPT', 'CONTRIBUTION', 'EVIDENCE']
    label: str
    metadata: dict[str, Any] = {}

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    relation_type: Relation
    evidence_ids: list[str] = []
    verification_status: str
    explanation: str

    @model_validator(mode='after')
    def historical_requires_evidence(self):
        if self.relation_type == Relation.DOCUMENTED_INFLUENCE and not self.evidence_ids:
            raise ValueError('Influência documentada exige evidência específica.')
        return self

class Graph(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    root_node: str
    coverage_warnings: list[str]

class Analysis(BaseModel):
    id: str
    root_paper_id: str
    created_at: str
    status: Literal['complete'] = 'complete'
    paper: Paper
    contributions: list[DiscoveryMatch]
    graph: Graph
    coverage_warnings: list[str]
    evidence_summary: dict[str, int]
    external_discovery: DiscoveryRun | None = None

class AnalysisRequest(BaseModel):
    doi: str = Field(min_length=1, max_length=300)
    model_config = {'extra': 'forbid'}
