from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any

from app.models.schemas import DiseaseProfile, EvidenceItem
from app.tools.pubmed import PubMedClient
from app.tools.scienceon import ScienceOnClient


@dataclass(slots=True)
class EvidenceProviderResult:
    source: str
    evidence: list[EvidenceItem] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str = ""


class PubMedEvidenceProvider:
    source = "PubMed"

    def __init__(self, client: PubMedClient) -> None:
        self.client = client

    async def search(self, profile: DiseaseProfile, limit: int = 8) -> EvidenceProviderResult:
        search_terms = self._search_terms(profile)
        if not search_terms:
            return EvidenceProviderResult(
                source=self.source,
                metadata={
                    "configured": True,
                    "records_returned": 0,
                    "records_kept": 0,
                    "search_terms": [],
                    "skipped_reason": "no_pubmed_compatible_disease_term",
                },
            )

        query = self._build_query(search_terms)
        try:
            records = await self.client.search(query, limit=limit)
        except Exception as exc:
            return EvidenceProviderResult(
                source=self.source,
                error=exc.__class__.__name__,
                metadata={
                    "configured": True,
                    "query": query,
                    "search_terms": search_terms,
                    "records_returned": 0,
                    "records_kept": 0,
                },
            )

        returned_count = len(records)
        records = self._filter_relevant_records(records, search_terms)
        evidence = [self._to_evidence_item(profile, record) for record in records]
        return EvidenceProviderResult(
            source=self.source,
            evidence=evidence,
            metadata={
                "configured": True,
                "query": query,
                "search_terms": search_terms,
                "records_returned": returned_count,
                "records_kept": len(records),
            },
        )

    def _build_query(self, search_terms: list[str]) -> str:
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

    def _search_terms(self, profile: DiseaseProfile) -> list[str]:
        names = [profile.disease.canonical_name, *profile.disease.synonyms]
        unique_names: list[str] = []
        for name in names:
            cleaned = " ".join(name.strip().split())
            if not cleaned or _contains_hangul(cleaned) or not re.search(r"[A-Za-z0-9]", cleaned):
                continue
            if cleaned.lower() not in {item.lower() for item in unique_names}:
                unique_names.append(cleaned)
        return unique_names[:6]

    def _quote_term(self, value: str) -> str:
        value = value.replace('"', '\\"')
        return f'"{value}"' if " " in value else value

    def _filter_relevant_records(self, records: list[dict], search_terms: list[str]) -> list[dict]:
        relevant: list[dict] = []
        for record in records:
            text = self._record_search_text(record)
            if any(_term_matches_record(term, text) for term in search_terms):
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

    def _to_evidence_item(self, profile: DiseaseProfile, record: dict) -> EvidenceItem:
        pmid = str(record.get("pmid", ""))
        abstract = str(record.get("abstract", "")).strip()
        journal = str(record.get("journal", "")).strip()
        year = str(record.get("publication_year", "")).strip()
        doi = str(record.get("doi", "")).strip()
        metadata = {
            "journal": journal,
            "publication_year": year,
            "publication_types": list(record.get("publication_types", [])),
            "mesh_terms": list(record.get("mesh_terms", [])),
            "keywords": list(record.get("keywords", [])),
            "doi": doi,
            "sources": [self.source],
            "source_ids": {self.source: pmid},
        }

        summary_parts = []
        if journal or year:
            summary_parts.append(f"{journal} {year}".strip())
        if abstract:
            summary_parts.append(abstract[:900])

        return EvidenceItem(
            id=f"pubmed-{pmid}",
            disease_name=profile.disease.canonical_name,
            source=self.source,
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


class KoreanPaperEvidenceProvider:
    source = "ScienceON"

    def __init__(self, client: ScienceOnClient) -> None:
        self.client = client

    async def search(self, profile: DiseaseProfile, limit: int = 8) -> EvidenceProviderResult:
        query = self._build_query(profile)
        if not self.client.is_configured():
            return EvidenceProviderResult(
                source=self.source,
                metadata={
                    "configured": False,
                    "query": query,
                    "records_returned": 0,
                    "records_kept": 0,
                    "skipped_reason": "missing_scienceon_api_key_or_url",
                },
            )

        try:
            records = await self.client.search(query, limit=limit)
        except Exception as exc:
            return EvidenceProviderResult(
                source=self.source,
                error=exc.__class__.__name__,
                metadata={"configured": True, "query": query, "records_returned": 0, "records_kept": 0},
            )

        terms = self._relevance_terms(profile)
        returned_count = len(records)
        records = [record for record in records if self._is_relevant(record, terms)]
        evidence = [self._to_evidence_item(profile, record) for record in records]
        return EvidenceProviderResult(
            source=self.source,
            evidence=evidence,
            metadata={
                "configured": True,
                "query": query,
                "records_returned": returned_count,
                "records_kept": len(records),
            },
        )

    def _build_query(self, profile: DiseaseProfile) -> str:
        input_text = profile.disease.input_text.strip()
        if input_text and _contains_hangul(input_text):
            return input_text
        return profile.disease.canonical_name

    def _relevance_terms(self, profile: DiseaseProfile) -> list[str]:
        terms = [profile.disease.input_text, profile.disease.canonical_name, *profile.disease.synonyms]
        unique_terms: list[str] = []
        for term in terms:
            cleaned = " ".join(term.strip().split())
            if cleaned and cleaned.lower() not in {item.lower() for item in unique_terms}:
                unique_terms.append(cleaned)
        return unique_terms

    def _is_relevant(self, record: dict, terms: list[str]) -> bool:
        text = " ".join(
            [
                str(record.get("title", "")),
                str(record.get("abstract", "")),
                " ".join(str(item) for item in record.get("keywords", [])),
            ]
        ).lower()
        return any(_term_matches_record(term, text) for term in terms)

    def _to_evidence_item(self, profile: DiseaseProfile, record: dict) -> EvidenceItem:
        source_id = str(record.get("source_id", "")).strip() or _stable_id(str(record.get("title", "")))
        abstract = str(record.get("abstract", "")).strip()
        journal = str(record.get("journal", "")).strip()
        year = str(record.get("publication_year", "")).strip()
        doi = str(record.get("doi", "")).strip()
        keywords = list(record.get("keywords", []))
        metadata = {
            "journal": journal,
            "publication_year": year,
            "keywords": keywords,
            "authors": str(record.get("authors", "")),
            "doi": doi,
            "source_database": str(record.get("source_database", "ScienceON")),
            "sources": [self.source],
            "source_ids": {self.source: source_id},
        }

        summary_parts = []
        if journal or year:
            summary_parts.append(f"{journal} {year}".strip())
        if abstract:
            summary_parts.append(abstract[:900])

        return EvidenceItem(
            id=f"scienceon-{source_id}",
            disease_name=profile.disease.canonical_name,
            source=self.source,
            source_id=source_id,
            title=str(record.get("title", "Untitled ScienceON record")),
            summary=" / ".join(summary_parts) if summary_parts else "ScienceON metadata record without an abstract.",
            url=str(record.get("url", "")),
            evidence_type="domestic_article",
            targets=keywords[:8],
            drugs=[],
            confidence=self._confidence(record),
            metadata=metadata,
        )

    def _confidence(self, record: dict) -> float:
        score = 0.52
        if record.get("abstract"):
            score += 0.06
        if record.get("doi"):
            score += 0.04
        if record.get("journal"):
            score += 0.03
        return round(min(score, 0.75), 2)


class EvidenceMerger:
    def merge(self, provider_results: list[EvidenceProviderResult]) -> list[EvidenceItem]:
        merged: dict[str, EvidenceItem] = {}
        for result in provider_results:
            for item in result.evidence:
                key = self._key(item)
                if key not in merged:
                    merged[key] = item
                    continue
                self._merge_into(merged[key], item)
        return sorted(merged.values(), key=lambda item: item.confidence, reverse=True)

    def _key(self, item: EvidenceItem) -> str:
        doi = str(item.metadata.get("doi", "")).strip().lower()
        if doi:
            return f"doi:{doi}"

        title = _normalize_title(item.title)
        if len(title) >= 20:
            return f"title:{title}"
        return f"{item.source}:{item.source_id}"

    def _merge_into(self, existing: EvidenceItem, incoming: EvidenceItem) -> None:
        existing_sources = list(existing.metadata.get("sources", [existing.source]))
        incoming_sources = list(incoming.metadata.get("sources", [incoming.source]))
        sources = sorted(set(existing_sources + incoming_sources))

        existing.source = " + ".join(sources)
        existing.confidence = round(min(max(existing.confidence, incoming.confidence) + 0.06, 0.95), 2)
        existing.targets = sorted(set(existing.targets + incoming.targets))[:10]
        existing.drugs = sorted(set(existing.drugs + incoming.drugs))[:12]
        existing.metadata["sources"] = sources
        existing.metadata["cross_validated"] = len(sources) > 1
        source_ids = dict(existing.metadata.get("source_ids", {}))
        source_ids.update(incoming.metadata.get("source_ids", {}))
        existing.metadata["source_ids"] = source_ids
        existing.metadata["merged_evidence_ids"] = sorted(
            set(existing.metadata.get("merged_evidence_ids", [existing.id]) + [incoming.id])
        )


def _contains_hangul(value: str) -> bool:
    return bool(re.search(r"[가-힣]", value))


def _term_matches_record(term: str, record_text: str) -> bool:
    normalized = " ".join(term.lower().split())
    if not normalized:
        return False
    if normalized in record_text:
        return True

    if _contains_hangul(normalized):
        return False

    tokens = [item for item in re.split(r"[^a-z0-9]+", normalized) if len(item) >= 4]
    if not tokens:
        return False
    return all(token in record_text for token in tokens)


def _normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9가-힣]+", " ", title.lower()).strip()


def _stable_id(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:12]
