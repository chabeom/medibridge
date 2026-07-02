from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any


@dataclass(slots=True)
class AnalysisRequest:
    input_text: str
    mode: str = "demo"
    top_k: int = 5


@dataclass(slots=True)
class NormalizedDisease:
    input_text: str
    canonical_name: str
    synonyms: list[str]
    identifiers: dict[str, str] = field(default_factory=dict)
    confidence: float = 0.0
    needs_external_lookup: bool = False


@dataclass(slots=True)
class DiseaseProfile:
    disease: NormalizedDisease
    unmet_need: str
    mechanisms: list[str]
    targets: list[str]
    biomarkers: list[str]
    patient_subgroups: list[str]


@dataclass(slots=True)
class EvidenceItem:
    id: str
    disease_name: str
    source: str
    source_id: str
    title: str
    summary: str
    url: str
    evidence_type: str
    targets: list[str] = field(default_factory=list)
    drugs: list[str] = field(default_factory=list)
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class DrugCandidate:
    name: str
    rationale: str
    mechanism: str
    candidate_type: str
    evidence_ids: list[str]
    targets: list[str] = field(default_factory=list)
    safety_summary: str = ""
    feasibility_notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    chemistry: dict[str, Any] = field(default_factory=dict)
    score_breakdown: dict[str, float] = field(default_factory=dict)
    overall_score: float = 0.0
    approval_status: str = "unchecked"
    approval_reason: str = ""


@dataclass(slots=True)
class CandidateApprovalReview:
    candidate_name: str
    status: str
    reason: str
    evidence_ids: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ClinicalProtocolDraft:
    candidate_name: str
    indication: str
    phase: str
    population: str
    primary_endpoint: str
    secondary_endpoints: list[str]
    inclusion_criteria: list[str]
    exclusion_criteria: list[str]
    safety_monitoring: list[str]


@dataclass(slots=True)
class CriticFinding:
    severity: str
    category: str
    message: str
    evidence_ids: list[str] = field(default_factory=list)


@dataclass(slots=True)
class AgentTrace:
    agent: str
    status: str
    summary: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AnalysisResult:
    request_id: str
    request: AnalysisRequest
    normalized_disease: NormalizedDisease
    disease_profile: DiseaseProfile
    evidence: list[EvidenceItem]
    candidates: list[DrugCandidate]
    approval_reviews: list[CandidateApprovalReview]
    clinical_drafts: list[ClinicalProtocolDraft]
    critic_findings: list[CriticFinding]
    citation_warnings: list[str]
    agent_trace: list[AgentTrace]
    disclaimer: str


def to_plain_dict(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, list):
        return [to_plain_dict(item) for item in value]
    if isinstance(value, dict):
        return {key: to_plain_dict(item) for key, item in value.items()}
    return value
