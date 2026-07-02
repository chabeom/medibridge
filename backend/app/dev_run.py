from __future__ import annotations

import asyncio
import json

from app.agents.orchestrator import MediBridgeOrchestrator
from app.models.schemas import AnalysisRequest, to_plain_dict


async def main() -> None:
    orchestrator = MediBridgeOrchestrator()
    result = await orchestrator.run(AnalysisRequest(input_text="migraine", mode="live", top_k=3))
    print(json.dumps(to_plain_dict(result), indent=2))


if __name__ == "__main__":
    asyncio.run(main())
