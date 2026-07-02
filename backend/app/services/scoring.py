from __future__ import annotations

from app.models.schemas import DrugCandidate, EvidenceItem


class ScoringEngine:
    def score(self, candidates: list[DrugCandidate], evidence: list[EvidenceItem]) -> list[DrugCandidate]:
        evidence_by_id = {item.id: item for item in evidence}

        for candidate in candidates:
            linked_evidence = [evidence_by_id[item_id] for item_id in candidate.evidence_ids if item_id in evidence_by_id]
            evidence_confidence = sum(item.confidence for item in linked_evidence) / max(len(linked_evidence), 1)
            target_overlap = len({target.lower() for target in candidate.targets})
            feasibility = float(candidate.chemistry.get("feasibility", 0.55))
            novelty = float(candidate.chemistry.get("novelty", 0.5))
            safety_risk = float(candidate.chemistry.get("safety_risk", 0.5))

            biological = min(25.0, 10.0 + target_overlap * 4.0 + evidence_confidence * 6.0)
            evidence_strength = min(20.0, len(linked_evidence) * 6.0 + evidence_confidence * 8.0)
            clinical = min(20.0, feasibility * 20.0)
            safety = max(0.0, 15.0 - safety_risk * 10.0)
            novelty_score = min(10.0, novelty * 10.0)
            citation = min(10.0, evidence_confidence * 10.0)

            candidate.score_breakdown = {
                "biological_plausibility": round(biological, 2),
                "evidence_strength": round(evidence_strength, 2),
                "clinical_feasibility": round(clinical, 2),
                "safety_feasibility": round(safety, 2),
                "novelty": round(novelty_score, 2),
                "citation_confidence": round(citation, 2),
            }
            candidate.overall_score = round(sum(candidate.score_breakdown.values()), 2)

        return sorted(candidates, key=lambda item: item.overall_score, reverse=True)
