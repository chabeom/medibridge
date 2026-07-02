from __future__ import annotations


class PubMedClient:
    async def search(self, query: str, limit: int = 20) -> list[dict]:
        raise NotImplementedError("PubMed integration will be implemented in week 2.")
