export interface Concept {
  id: string;
  name: string;
  aliases: string[];
  provenance: string[];
}
export interface Paper {
  id: string;
  doi: string;
  openalex_id: string;
  title: string;
  abstract: string | null;
  year: number | null;
  authors: { id: string; name: string }[];
  concepts: Concept[];
  referenced_work_ids: string[];
  references_status: string;
  source_url: string;
  retrieved_at: string;
  from_cache: boolean;
  cache_stale: boolean;
  limitations: string[];
}
export interface Evidence {
  id: string;
  contribution_id: string;
  claim_supported: string;
  source_title: string;
  source_url: string;
  source_type: string;
  excerpt_or_location: string;
  verification_status: string;
}
export interface Researcher {
  id: string;
  name: string;
  openalex_id: string | null;
  research_areas: string[];
  identity_status: string;
  verification_sources: string[];
}
export interface Match {
  contribution: {
    id: string;
    title: string;
    description: string;
    researcher_ids: string[];
    participants: string[];
    concept_ids: string[];
    related_dois: string[];
    scientific_field: string;
    verification_status: string;
  };
  researchers: Researcher[];
  evidence: Evidence[];
  matched_concepts: Concept[];
  relation_type: string;
  citation_status: string;
  explanation: string;
  limitations: string[];
  relevance: number;
}
export interface GraphNode {
  id: string;
  type: "PAPER" | "RESEARCHER" | "CONCEPT" | "CONTRIBUTION" | "EVIDENCE";
  label: string;
  metadata: Record<string, unknown>;
}
export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  relation_type: string;
  evidence_ids: string[];
  verification_status: string;
  explanation: string;
}
export interface Analysis {
  external_discovery?: AutomaticDiscoveryResult | null;
  id: string;
  created_at: string;
  paper: Paper;
  contributions: Match[];
  coverage_warnings: string[];
  evidence_summary: Record<string, number>;
  graph: {
    nodes: GraphNode[];
    edges: GraphEdge[];
    root_node: string;
    coverage_warnings: string[];
  };
}

export interface AutomaticCandidate {
  candidate: {
    id: string;
    work: {
      doi: string;
      title: string;
      year: number | null;
      authors: {
        name: string;
        openalex_id: string | null;
        orcid: string | null;
      }[];
      topics: string[];
      sources: {
        source: string;
        source_url: string;
        retrieved_at: string;
        from_cache: boolean;
      }[];
    };
    record_state: "retrieved" | "automatically_extracted";
    verification_status: "pending_review";
    extraction_method: string;
    excerpt: string | null;
    excerpt_location: string | null;
    identities: {
      author_name: string;
      status:
        | "documented_woman"
        | "reported_without_reference"
        | "unknown"
        | "conflicting";
      method: string;
      explanation: string;
      source_urls: string[];
    }[];
    limitations: string[];
  };
  retrieval_reasons: string[];
  citation_status: string;
  relation_type: "RELATED_TO";
}
export interface AutomaticDiscoveryResult {
  status: "complete" | "partial" | "unavailable";
  started_at: string;
  completed_at: string;
  candidates: AutomaticCandidate[];
  warnings: string[];
  sources: {
    source: string;
    source_url: string;
    retrieved_at: string;
    from_cache: boolean;
  }[];
  limits: Record<string, number>;
}
