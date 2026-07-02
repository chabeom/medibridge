from __future__ import annotations

from uuid import uuid4

from app.agents.approval_agent import ApprovalStatusAgent
from app.agents.clinical_agent import ClinicalDesignAgent
from app.agents.critic_agent import CriticAgent
from app.agents.disease_agent import DiseaseAnalystAgent
from app.agents.evidence_agent import EvidenceRetrievalAgent
from app.agents.hypothesis_agent import RepurposingHypothesisAgent
from app.agents.safety_agent import SafetyFeasibilityAgent
from app.models.schemas import AgentTrace, AnalysisRequest, AnalysisResult
from app.services.cache import EvidenceStore
from app.services.citation_validator import CitationValidator
from app.services.normalizer import DiseaseNormalizer
from app.services.scoring import ScoringEngine


DISCLAIMER = (
    "연구지원용 결과입니다. 의료 조언, 진단, 처방 지침, 임상 효능 입증으로 해석하면 안 됩니다."
)


class MediBridgeOrchestrator:
    def __init__(self) -> None:
        self.normalizer = DiseaseNormalizer()
        self.evidence_store = EvidenceStore()
        self.disease_agent = DiseaseAnalystAgent()
        self.evidence_agent = EvidenceRetrievalAgent(self.evidence_store)
        self.hypothesis_agent = RepurposingHypothesisAgent()
        self.approval_agent = ApprovalStatusAgent()
        self.safety_agent = SafetyFeasibilityAgent()
        self.clinical_agent = ClinicalDesignAgent()
        self.critic_agent = CriticAgent()
        self.scoring_engine = ScoringEngine()
        self.citation_validator = CitationValidator()

    async def run(self, request: AnalysisRequest) -> AnalysisResult:
        trace: list[AgentTrace] = []
        request_id = str(uuid4())

        normalized = self.normalizer.normalize(request.input_text)
        trace.append(
            AgentTrace(
                agent="Disease Normalizer",
                status="complete" if not normalized.needs_external_lookup else "needs_data",
                summary=f"Canonical disease name: {normalized.canonical_name}.",
                metadata={"confidence": normalized.confidence, "identifiers": normalized.identifiers},
            )
        )

        profile, step = await self.disease_agent.run(normalized)
        trace.append(step)

        evidence, step = await self.evidence_agent.run(profile, request.mode)
        trace.append(step)

        candidates, step = await self.hypothesis_agent.run(profile, evidence)
        trace.append(step)

        candidates, approval_reviews, step = await self.approval_agent.run(profile, candidates)
        trace.append(step)

        candidates, step = await self.safety_agent.run(candidates)
        trace.append(step)

        candidates = self.scoring_engine.score(candidates, evidence)
        trace.append(
            AgentTrace(
                agent="Scoring Engine",
                status="complete",
                summary="Computed weighted candidate ranking.",
                metadata={"candidate_count": len(candidates)},
            )
        )

        candidates = candidates[: request.top_k]
        clinical_drafts, step = await self.clinical_agent.run(profile, candidates)
        trace.append(step)

        citation_warnings = self.citation_validator.validate(candidates, evidence)
        trace.append(
            AgentTrace(
                agent="Citation Validator",
                status="complete" if not citation_warnings else "warning",
                summary="Validated candidate evidence references.",
                metadata={"warning_count": len(citation_warnings)},
            )
        )

        critic_findings, step = await self.critic_agent.run(evidence, candidates, clinical_drafts, citation_warnings)
        trace.append(step)

        return AnalysisResult(
            request_id=request_id,
            request=request,
            normalized_disease=normalized,
            disease_profile=profile,
            evidence=evidence,
            candidates=candidates,
            approval_reviews=approval_reviews,
            clinical_drafts=clinical_drafts,
            critic_findings=critic_findings,
            citation_warnings=citation_warnings,
            agent_trace=trace,
            disclaimer=DISCLAIMER,
        )
