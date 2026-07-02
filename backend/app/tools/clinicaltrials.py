from __future__ import annotations


class ClinicalTrialsClient:
    async def search(self, condition: str, limit: int = 20) -> list[dict]:
        raise NotImplementedError("ClinicalTrials.gov integration will be implemented in week 2.")
