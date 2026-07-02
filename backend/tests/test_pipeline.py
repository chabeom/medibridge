from __future__ import annotations

import asyncio
import unittest

from app.agents.orchestrator import MediBridgeOrchestrator
from app.models.schemas import AnalysisRequest


class PipelineTest(unittest.TestCase):
    def test_demo_pipeline_returns_ranked_candidates(self) -> None:
        async def run_case():
            orchestrator = MediBridgeOrchestrator()
            return await orchestrator.run(AnalysisRequest(input_text="ALS", top_k=3))

        result = asyncio.run(run_case())

        self.assertEqual(result.normalized_disease.canonical_name, "Amyotrophic Lateral Sclerosis")
        self.assertGreaterEqual(len(result.evidence), 3)
        self.assertGreaterEqual(len(result.candidates), 1)
        self.assertGreater(result.candidates[0].overall_score, 0)
        self.assertEqual(result.citation_warnings, [])

    def test_common_cold_korean_input_returns_demo_candidates(self) -> None:
        async def run_case():
            orchestrator = MediBridgeOrchestrator()
            return await orchestrator.run(AnalysisRequest(input_text="감기", top_k=3))

        result = asyncio.run(run_case())

        self.assertEqual(result.normalized_disease.canonical_name, "Common Cold")
        self.assertGreaterEqual(len(result.evidence), 3)
        self.assertGreaterEqual(len(result.candidates), 1)
        self.assertGreaterEqual(len(result.clinical_drafts), 1)


if __name__ == "__main__":
    unittest.main()
