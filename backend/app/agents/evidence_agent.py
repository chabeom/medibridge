from __future__ import annotations

import asyncio

from app.models.schemas import AgentTrace, DiseaseProfile, EvidenceItem
from app.services.cache import EvidenceStore
from app.services.evidence_providers import (
    EvidenceMerger,
    EvidenceProviderResult,
    KoreanPaperEvidenceProvider,
    PubMedEvidenceProvider,
)
from app.tools.pubmed import PubMedClient
from app.tools.scienceon import ScienceOnClient


class EvidenceRetrievalAgent:
    name = "Evidence Retrieval Agent"

    def __init__(
        self,
        evidence_store: EvidenceStore,
        pubmed_client: PubMedClient | None = None,
        scienceon_client: ScienceOnClient | None = None,
    ) -> None:
        self._evidence_store = evidence_store
        self._pubmed_client = pubmed_client or PubMedClient()
        self._scienceon_client = scienceon_client or ScienceOnClient()
        self._pubmed_provider = PubMedEvidenceProvider(self._pubmed_client)
        self._korean_provider = KoreanPaperEvidenceProvider(self._scienceon_client)
        self._merger = EvidenceMerger()

    async def run(self, profile: DiseaseProfile, mode: str) -> tuple[list[EvidenceItem], AgentTrace]:
        cached = self._evidence_store.find_by_disease(profile.disease.canonical_name)

        if cached:
            return cached, AgentTrace(
                agent=self.name,
                status="complete",
                summary="Loaded cached evidence from the evidence store.",
                metadata={"evidence_count": len(cached), "mode": mode, "cache_hit": True},
            )

        self._pubmed_provider.client = self._pubmed_client
        self._korean_provider.client = self._scienceon_client

        raw_results = await asyncio.gather(
            self._pubmed_provider.search(profile, limit=8),
            self._korean_provider.search(profile, limit=8),
            return_exceptions=True,
        )
        provider_results = [self._coerce_provider_result(item) for item in raw_results]
        evidence = self._merger.merge(provider_results)

        metadata = self._metadata(provider_results, evidence, mode)
        if evidence:
            self._evidence_store.save_many(profile.disease.canonical_name, evidence)
            return evidence, AgentTrace(
                agent=self.name,
                status="complete",
                summary="Retrieved evidence from PubMed and domestic paper providers, then merged duplicates.",
                metadata=metadata,
            )

        return [], AgentTrace(
            agent=self.name,
            status="needs_data",
            summary="No disease-specific evidence passed provider relevance filters.",
            metadata=metadata,
        )

    def _coerce_provider_result(self, value: EvidenceProviderResult | BaseException) -> EvidenceProviderResult:
        if isinstance(value, EvidenceProviderResult):
            return value
        return EvidenceProviderResult(
            source="unknown",
            error=value.__class__.__name__,
            metadata={"configured": False, "records_returned": 0, "records_kept": 0},
        )

    def _metadata(
        self,
        provider_results: list[EvidenceProviderResult],
        evidence: list[EvidenceItem],
        mode: str,
    ) -> dict:
        provider_metadata = {result.source: result.metadata | ({"error": result.error} if result.error else {}) for result in provider_results}
        sources = sorted({source for item in evidence for source in str(item.source).split(" + ")})
        pubmed = provider_metadata.get("PubMed", {})
        scienceon = provider_metadata.get("ScienceON", {})

        return {
            "evidence_count": len(evidence),
            "mode": mode,
            "cache_hit": False,
            "sources": sources,
            "provider_metadata": provider_metadata,
            "query": pubmed.get("query", ""),
            "search_terms": pubmed.get("search_terms", []),
            "records_returned": pubmed.get("records_returned", 0),
            "records_kept": pubmed.get("records_kept", 0),
            "domestic_records_returned": scienceon.get("records_returned", 0),
            "domestic_records_kept": scienceon.get("records_kept", 0),
            "cross_validated_count": sum(1 for item in evidence if item.metadata.get("cross_validated")),
        }
