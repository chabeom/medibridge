from __future__ import annotations


class ChemblClient:
    async def molecule_targets(self, molecule_name: str) -> list[dict]:
        raise NotImplementedError("ChEMBL integration will be implemented in week 2.")
