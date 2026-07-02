from __future__ import annotations

from app.models.schemas import NormalizedDisease
from app.services.demo_data import DEMO_DISEASES, build_synonym_index


class DiseaseNormalizer:
    def __init__(self) -> None:
        self._synonym_index = build_synonym_index()

    def normalize(self, input_text: str) -> NormalizedDisease:
        cleaned = " ".join(input_text.strip().split())
        key = self._synonym_index.get(cleaned.lower())

        if key:
            disease = DEMO_DISEASES[key]
            return NormalizedDisease(
                input_text=input_text,
                canonical_name=str(disease["canonical_name"]),
                synonyms=list(disease["synonyms"]),
                identifiers=dict(disease["identifiers"]),
                confidence=0.94,
                needs_external_lookup=False,
            )

        return NormalizedDisease(
            input_text=input_text,
            canonical_name=cleaned,
            synonyms=[cleaned],
            identifiers={},
            confidence=0.45,
            needs_external_lookup=True,
        )
