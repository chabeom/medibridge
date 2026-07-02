from __future__ import annotations

import re

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

        search_terms = self._pubmed_search_terms(profile)
        if not search_terms:
            return [], AgentTrace(
                agent=self.name,
                status="needs_data",
                summary="No PubMed-compatible disease term is available for this request.",
                metadata={
                    "evidence_count": 0,
                    "mode": mode,
                    "cache_hit": False,
                    "canonical_name": profile.disease.canonical_name,
                },
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

        returned_count = len(records)
        records = self._filter_relevant_records(records, search_terms)
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
                    "search_terms": search_terms,
                    "records_returned": returned_count,
                    "records_kept": len(records),
                    "sources": ["PubMed"],
                },
            )

        return [], AgentTrace(
            agent=self.name,
            status="needs_data",
            summary="No disease-specific PubMed records passed the relevance filter.",
            metadata={
                "evidence_count": 0,
                "mode": mode,
                "cache_hit": False,
                "query": query,
                "search_terms": search_terms,
                "records_returned": returned_count,
                "records_kept": 0,
            },
        )

    def _build_pubmed_query(self, profile: DiseaseProfile) -> str:
        search_terms = self._pubmed_search_terms(profile)
        disease_clauses: list[str] = []
        for term in search_terms:
            quoted = self._quote_term(term)
            disease_clauses.append(f"{quoted}[Title/Abstract]")
            disease_clauses.append(f"{quoted}[MeSH Terms]")

        disease_query = " OR ".join(disease_clauses)
        therapy_query = " OR ".join(
            [
                '"drug therapy"[Title/Abstract]',
                '"drug repositioning"[Title/Abstract]',
                'repurposing[Title/Abstract]',
                'treatment[Title/Abstract]',
                'therapeutics[MeSH Terms]',
                '"clinical trial"[Publication Type]',
                '"randomized controlled trial"[Publication Type]',
            ]
        )
        return f"({disease_query}) AND ({therapy_query})"

    def _pubmed_search_terms(self, profile: DiseaseProfile) -> list[str]:
        names = [profile.disease.canonical_name, *profile.disease.synonyms]
        unique_names = []
        for name in names:
            cleaned = " ".join(name.strip().split())
            if not cleaned or self._contains_hangul(cleaned) or not re.search(r"[A-Za-z0-9]", cleaned):
                continue
            if cleaned.lower() not in {item.lower() for item in unique_names}:
                unique_names.append(cleaned)

        return unique_names[:6]

    def _quote_term(self, value: str) -> str:
        value = value.replace('"', '\\"')
        if " " in value:
            return f'"{value}"'
        return value

    def _contains_hangul(self, value: str) -> bool:
        return bool(re.search(r"[가-힣]", value))

    def _filter_relevant_records(self, records: list[dict], search_terms: list[str]) -> list[dict]:
        relevant: list[dict] = []
        for record in records:
            text = self._record_search_text(record)
            if any(self._term_matches_record(term, text) for term in search_terms):
                relevant.append(record)
        return relevant

    def _record_search_text(self, record: dict) -> str:
        parts = [
            str(record.get("title", "")),
            str(record.get("abstract", "")),
            " ".join(str(item) for item in record.get("mesh_terms", [])),
            " ".join(str(item) for item in record.get("keywords", [])),
        ]
        return " ".join(parts).lower()

    def _term_matches_record(self, term: str, record_text: str) -> bool:
        normalized = " ".join(term.lower().split())
        if not normalized:
            return False
        if normalized in record_text:
            return True

        tokens = [item for item in re.split(r"[^a-z0-9]+", normalized) if len(item) >= 4]
        if not tokens:
            return False
        return all(token in record_text for token in tokens)

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
