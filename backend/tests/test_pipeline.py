from __future__ import annotations

import asyncio
import unittest

from app.agents.orchestrator import MediBridgeOrchestrator
from app.models.schemas import AnalysisRequest
from app.services.demo_data import DEMO_DISEASES


class FakePubMedClient:
    async def search(self, query: str, limit: int = 20) -> list[dict]:
        return [
            {
                "pmid": "1001",
                "title": "Zolmitriptan treatment for migraine",
                "abstract": "A clinical trial evaluated zolmitriptan for acute migraine treatment.",
                "journal": "Example Journal",
                "publication_year": "2025",
                "publication_types": ["Clinical Trial"],
                "mesh_terms": ["Migraine Disorders", "Serotonin 5-HT1 Receptor Agonists"],
                "keywords": ["migraine", "treatment"],
                "drugs": ["Zolmitriptan"],
                "url": "https://pubmed.ncbi.nlm.nih.gov/1001/",
                "evidence_type": "clinical_trial",
                "confidence": 0.78,
            },
            {
                "pmid": "1002",
                "title": "Erenumab prevention in migraine",
                "abstract": "A preventive therapy study evaluated erenumab in migraine.",
                "journal": "Example Journal",
                "publication_year": "2024",
                "publication_types": ["Randomized Controlled Trial"],
                "mesh_terms": ["Migraine Disorders", "Calcitonin Gene-Related Peptide"],
                "keywords": ["migraine", "prevention"],
                "drugs": ["Erenumab"],
                "url": "https://pubmed.ncbi.nlm.nih.gov/1002/",
                "evidence_type": "randomized_controlled_trial",
                "confidence": 0.84,
            },
        ]


class PipelineTest(unittest.TestCase):
    def test_live_pipeline_returns_literature_candidates(self) -> None:
        async def run_case():
            orchestrator = MediBridgeOrchestrator()
            orchestrator.evidence_agent._pubmed_client = FakePubMedClient()
            return await orchestrator.run(AnalysisRequest(input_text="migraine", mode="live", top_k=3))

        result = asyncio.run(run_case())

        self.assertEqual(result.normalized_disease.canonical_name, "Migraine Disorders")
        self.assertEqual(len(result.evidence), 2)
        self.assertGreaterEqual(len(result.candidates), 2)
        self.assertGreaterEqual(len(result.clinical_drafts), 2)
        self.assertTrue(all(candidate.candidate_type == "literature-derived repurposing hypothesis" for candidate in result.candidates))
        self.assertEqual(result.citation_warnings, [])

    def test_no_default_demo_cache_is_seeded(self) -> None:
        orchestrator = MediBridgeOrchestrator()

        self.assertEqual(DEMO_DISEASES, {})
        self.assertEqual(orchestrator.evidence_store.find_by_disease("any disease"), [])


if __name__ == "__main__":
    unittest.main()
