from __future__ import annotations

from app.models.schemas import AgentTrace, DiseaseProfile, EvidenceItem
from app.services.cache import EvidenceStore


class EvidenceRetrievalAgent:
    name = "Evidence Retrieval Agent"

    def __init__(self, evidence_store: EvidenceStore) -> None:
        self._evidence_store = evidence_store

    async def run(self, profile: DiseaseProfile, mode: str) -> tuple[list[EvidenceItem], AgentTrace]:
        cached = self._evidence_store.find_by_disease(profile.disease.canonical_name)

        if cached:
            return cached, AgentTrace(
                agent=self.name,
                status="complete",
                summary="Loaded cached evidence from the evidence store.",
                metadata={"evidence_count": len(cached), "mode": mode, "cache_hit": True},
            )

        return [], AgentTrace(
            agent=self.name,
            status="needs_data",
            summary="No cached evidence found. Public API retrieval will be used in the next iteration.",
            metadata={"evidence_count": 0, "mode": mode, "cache_hit": False},
        )
