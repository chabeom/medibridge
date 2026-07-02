from __future__ import annotations

from app.models.schemas import DrugCandidate, EvidenceItem


class CitationValidator:
    def validate(self, candidates: list[DrugCandidate], evidence: list[EvidenceItem]) -> list[str]:
        warnings: list[str] = []
        known_ids = {item.id for item in evidence}

        for item in evidence:
            if not item.source or not item.source_id:
                warnings.append(f"Evidence {item.id} is missing source metadata.")

        for candidate in candidates:
            missing = [item_id for item_id in candidate.evidence_ids if item_id not in known_ids]
            if missing:
                warnings.append(f"{candidate.name} references missing evidence ids: {', '.join(missing)}.")

        return warnings
