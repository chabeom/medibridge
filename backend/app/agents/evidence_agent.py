from __future__ import annotations

from app.models.schemas import AgentTrace, DiseaseProfile, EvidenceItem
from app.services.cache import EvidenceStore
from app.tools.pubmed import PubMedClient


class EvidenceRetrievalAgent:
    name = "Evidence Retrieval Agent"

    def __init__(self, evidence_store: EvidenceStore, pubmed_client: PubMedClient | None = None) -> None:
        self._evidence_store = evidence_store
        self._pubmed_client = pubmed_client or PubMedClient()

    async def run(self, profile: DiseaseProfile, mode: str) -> tuple[list[EvidenceItem], AgentTrace]:
        cached = self._evidence_store.find_by_disease(profile.disease.canonical_name)

        if cached:
            return cached, AgentTrace(
                agent=self.name,
                status="complete",
                summary="Loaded cached evidence from the evidence store.",
                metadata={"evidence_count": len(cached), "mode": mode, "cache_hit": True},
            )

        query = self._build_pubmed_query(profile)
        try:
            records = await self._pubmed_client.search(query, limit=8)
        except Exception as exc:
            return [], AgentTrace(
                agent=self.name,
                status="needs_data",
                summary="PubMed retrieval failed. Cached evidence was not available.",
                metadata={
                    "evidence_count": 0,
                    "mode": mode,
                    "cache_hit": False,
                    "query": query,
                    "error": exc.__class__.__name__,
                },
            )

        evidence = [self._to_evidence_item(profile, record) for record in records]
        if evidence:
            self._evidence_store.save_many(profile.disease.canonical_name, evidence)
            return evidence, AgentTrace(
                agent=self.name,
                status="complete",
                summary="Retrieved evidence from PubMed and saved it to the evidence store.",
                metadata={
                    "evidence_count": len(evidence),
                    "mode": mode,
                    "cache_hit": False,
                    "query": query,
                    "sources": ["PubMed"],
                },
            )

        return [], AgentTrace(
            agent=self.name,
            status="needs_data",
            summary="No cached evidence or PubMed records found for this disease.",
            metadata={"evidence_count": 0, "mode": mode, "cache_hit": False, "query": query},
        )

    def _build_pubmed_query(self, profile: DiseaseProfile) -> str:
        names = [profile.disease.canonical_name, *profile.disease.synonyms]
        unique_names = []
        for name in names:
            cleaned = " ".join(name.strip().split())
            if cleaned and cleaned.lower() not in {item.lower() for item in unique_names}:
                unique_names.append(cleaned)

        disease_terms = " OR ".join(self._quote_term(name) for name in unique_names[:4])
        return f"({disease_terms}) AND (drug therapy OR treatment OR clinical trial OR repurposing OR review)"

    def _quote_term(self, value: str) -> str:
        if " " in value:
            return f'"{value}"'
        return value

    def _to_evidence_item(self, profile: DiseaseProfile, record: dict) -> EvidenceItem:
        pmid = str(record.get("pmid", ""))
        abstract = str(record.get("abstract", "")).strip()
        journal = str(record.get("journal", "")).strip()
        year = str(record.get("publication_year", "")).strip()
        metadata = {
            "journal": journal,
            "publication_year": year,
            "publication_types": list(record.get("publication_types", [])),
            "mesh_terms": list(record.get("mesh_terms", [])),
            "keywords": list(record.get("keywords", [])),
        }

        summary_parts = []
        if journal or year:
            summary_parts.append(f"{journal} {year}".strip())
        if abstract:
            summary_parts.append(abstract[:900])

        return EvidenceItem(
            id=f"pubmed-{pmid}",
            disease_name=profile.disease.canonical_name,
            source="PubMed",
            source_id=pmid,
            title=str(record.get("title", "Untitled PubMed record")),
            summary=" / ".join(summary_parts) if summary_parts else "PubMed metadata record without an abstract.",
            url=str(record.get("url", f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/")),
            evidence_type=str(record.get("evidence_type", "publication")),
            targets=list(record.get("mesh_terms", []))[:8],
            drugs=list(record.get("drugs", []))[:12],
            confidence=float(record.get("confidence", 0.5)),
            metadata=metadata,
        )
