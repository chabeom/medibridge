from __future__ import annotations

from app.models.schemas import EvidenceItem
from app.services.demo_data import DEMO_DISEASES


class EvidenceStore:
    """Cache-first evidence store.

    The MVP uses in-memory demo data. The same interface will be backed by
    PostgreSQL + pgvector in the next iteration.
    """

    def __init__(self) -> None:
        self._evidence_by_disease: dict[str, list[EvidenceItem]] = {}
        self._seed_demo_data()

    def _seed_demo_data(self) -> None:
        for disease in DEMO_DISEASES.values():
            canonical = str(disease["canonical_name"]).lower()
            self._evidence_by_disease[canonical] = list(disease["evidence"])

    def find_by_disease(self, canonical_name: str) -> list[EvidenceItem]:
        return list(self._evidence_by_disease.get(canonical_name.lower(), []))

    def save_many(self, canonical_name: str, evidence: list[EvidenceItem]) -> None:
        key = canonical_name.lower()
        existing = {item.id: item for item in self._evidence_by_disease.get(key, [])}
        for item in evidence:
            existing[item.id] = item
        self._evidence_by_disease[key] = list(existing.values())
