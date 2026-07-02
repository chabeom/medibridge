from __future__ import annotations

from app.models.schemas import AgentTrace, DiseaseProfile, DrugCandidate, EvidenceItem
from app.services.demo_data import DEMO_DISEASES


class RepurposingHypothesisAgent:
    name = "Repurposing Hypothesis Agent"

    async def run(
        self,
        profile: DiseaseProfile,
        evidence: list[EvidenceItem],
    ) -> tuple[list[DrugCandidate], AgentTrace]:
        demo = DEMO_DISEASES.get(profile.disease.canonical_name.lower())
        if not demo:
            return [], AgentTrace(
                agent=self.name,
                status="needs_data",
                summary="No candidate seeds are available for this disease yet.",
                metadata={"candidate_count": 0},
            )

        candidates: list[DrugCandidate] = []
        for seed in demo["candidate_seeds"]:
            chemistry = dict(seed["chemistry"])
            chemistry["feasibility"] = seed["feasibility"]
            chemistry["novelty"] = seed["novelty"]
            chemistry["safety_risk"] = seed["safety_risk"]

            candidates.append(
                DrugCandidate(
                    name=str(seed["name"]),
                    rationale=str(seed["rationale"]),
                    mechanism=str(seed["mechanism"]),
                    candidate_type=str(seed["candidate_type"]),
                    evidence_ids=list(seed["evidence_ids"]),
                    targets=list(seed["targets"]),
                    safety_summary=str(seed["safety_summary"]),
                    chemistry=chemistry,
                )
            )

        return candidates, AgentTrace(
            agent=self.name,
            status="complete",
            summary="Generated mechanism-backed repurposing hypotheses from cached evidence.",
            metadata={"candidate_count": len(candidates), "evidence_count": len(evidence)},
        )
