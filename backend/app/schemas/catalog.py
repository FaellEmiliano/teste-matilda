"""Machine-ingested records are candidates, never editorially verified claims."""
from typing import Literal
from pydantic import BaseModel, Field


class SourceObservation(BaseModel):
    source: Literal['openalex', 'europe_pmc', 'wikidata', 'editorial_catalog']
    source_url: str
    retrieved_at: str
    from_cache: bool = False
    query: dict[str, str | int] = Field(default_factory=dict)


class CandidateAuthor(BaseModel):
    name: str
    openalex_id: str | None = None
    orcid: str | None = None


class CandidateWork(BaseModel):
    doi: str
    title: str
    year: int | None = None
    openalex_id: str | None = None
    authors: list[CandidateAuthor] = Field(default_factory=list)
    abstract: str | None = None
    topics: list[str] = Field(default_factory=list)
    sources: list[SourceObservation] = Field(default_factory=list)


class IdentityObservation(BaseModel):
    author_name: str
    author_openalex_id: str | None = None
    orcid: str | None = None
    wikidata_id: str | None = None
    status: Literal['documented_woman', 'reported_without_reference', 'unknown', 'conflicting']
    method: Literal['curated_persistent_id', 'wikidata_orcid', 'wikidata_openalex_id', 'unresolved']
    source_urls: list[str] = Field(default_factory=list)
    explanation: str


class CatalogCandidate(BaseModel):
    id: str
    work: CandidateWork
    record_state: Literal['retrieved', 'automatically_extracted']
    verification_status: Literal['pending_review'] = 'pending_review'
    extraction_method: Literal['abstract_excerpt_v1', 'metadata_only_v1']
    excerpt: str | None = None
    excerpt_location: str | None = None
    identities: list[IdentityObservation] = Field(default_factory=list)
    limitations: list[str]


class CandidateConnection(BaseModel):
    candidate: CatalogCandidate
    retrieval_reasons: list[str]
    citation_status: Literal['CITED', 'NOT_FOUND_IN_RETRIEVED_REFERENCES', 'UNKNOWN']
    relation_type: Literal['RELATED_TO'] = 'RELATED_TO'


class DiscoveryRun(BaseModel):
    status: Literal['complete', 'partial', 'unavailable']
    started_at: str
    completed_at: str
    candidates: list[CandidateConnection]
    warnings: list[str]
    sources: list[SourceObservation]
    limits: dict[str, int]
