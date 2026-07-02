from __future__ import annotations

import asyncio
import unittest

from app.agents.evidence_agent import EvidenceRetrievalAgent
from app.agents.hypothesis_agent import RepurposingHypothesisAgent
from app.models.schemas import DiseaseProfile, EvidenceItem, NormalizedDisease
from app.services.cache import EvidenceStore
from app.tools.pubmed import PubMedClient


SAMPLE_PUBMED_XML = """
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>123456</PMID>
      <Article>
        <Journal>
          <JournalIssue>
            <PubDate>
              <Year>2024</Year>
            </PubDate>
          </JournalIssue>
          <Title>Example Journal</Title>
        </Journal>
        <ArticleTitle>Drug repurposing for example disease</ArticleTitle>
        <Abstract>
          <AbstractText Label="BACKGROUND">Example disease has limited treatment options.</AbstractText>
          <AbstractText Label="METHODS">A candidate drug was evaluated in a small trial.</AbstractText>
        </Abstract>
        <PublicationTypeList>
          <PublicationType>Clinical Trial</PublicationType>
        </PublicationTypeList>
        <ChemicalList>
          <Chemical>
            <RegistryNumber>0</RegistryNumber>
            <NameOfSubstance>Erenumab</NameOfSubstance>
          </Chemical>
        </ChemicalList>
      </Article>
      <MeshHeadingList>
        <MeshHeading>
          <DescriptorName>Example Disease</DescriptorName>
        </MeshHeading>
      </MeshHeadingList>
      <KeywordList>
        <Keyword>repurposing</Keyword>
      </KeywordList>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>
"""


class FakePubMedClient:
    def __init__(self) -> None:
        self.queries: list[str] = []

    async def search(self, query: str, limit: int = 20) -> list[dict]:
        self.queries.append(query)
        return [
            {
                "pmid": "123456",
                "title": "Drug repurposing for example disease",
                "abstract": "Example disease has limited treatment options.",
                "journal": "Example Journal",
                "publication_year": "2024",
                "publication_types": ["Clinical Trial"],
                "mesh_terms": ["Example Disease"],
                "keywords": ["repurposing"],
                "url": "https://pubmed.ncbi.nlm.nih.gov/123456/",
                "evidence_type": "clinical_trial",
                "confidence": 0.78,
            }
        ]


class PubMedIntegrationTest(unittest.TestCase):
    def test_pubmed_client_parses_efetch_xml(self) -> None:
        client = PubMedClient(api_key="", email="", tool="medibridge")

        records = client._parse_articles(SAMPLE_PUBMED_XML)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["pmid"], "123456")
        self.assertEqual(records[0]["title"], "Drug repurposing for example disease")
        self.assertEqual(records[0]["publication_year"], "2024")
        self.assertEqual(records[0]["evidence_type"], "clinical_trial")
        self.assertEqual(records[0]["drugs"], ["Erenumab"])
        self.assertIn("BACKGROUND", records[0]["abstract"])
        self.assertGreater(records[0]["confidence"], 0.6)

    def test_evidence_agent_uses_pubmed_when_cache_misses(self) -> None:
        async def run_case():
            store = EvidenceStore()
            fake_client = FakePubMedClient()
            agent = EvidenceRetrievalAgent(store, pubmed_client=fake_client)
            profile = DiseaseProfile(
                disease=NormalizedDisease(
                    input_text="example disease",
                    canonical_name="Example Disease",
                    synonyms=["Example Syndrome"],
                    confidence=0.45,
                    needs_external_lookup=True,
                ),
                unmet_need="External disease profile lookup is required.",
                mechanisms=[],
                targets=[],
                biomarkers=[],
                patient_subgroups=[],
            )

            evidence, trace = await agent.run(profile, mode="demo")
            cached = store.find_by_disease("Example Disease")
            return evidence, trace, cached, fake_client.queries

        evidence, trace, cached, queries = asyncio.run(run_case())

        self.assertEqual(trace.status, "complete")
        self.assertEqual(trace.metadata["sources"], ["PubMed"])
        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0].source, "PubMed")
        self.assertEqual(evidence[0].source_id, "123456")
        self.assertEqual(len(cached), 1)
        self.assertEqual(len(queries), 1)
        self.assertIn('"Example Disease"', queries[0])

    def test_hypothesis_agent_builds_candidates_from_pubmed_drugs(self) -> None:
        async def run_case():
            agent = RepurposingHypothesisAgent()
            profile = DiseaseProfile(
                disease=NormalizedDisease(
                    input_text="example disease",
                    canonical_name="Example Disease",
                    synonyms=[],
                    confidence=0.45,
                    needs_external_lookup=True,
                ),
                unmet_need="External disease profile lookup is required.",
                mechanisms=[],
                targets=[],
                biomarkers=[],
                patient_subgroups=[],
            )
            evidence = [
                EvidenceItem(
                    id="pubmed-1",
                    disease_name="Example Disease",
                    source="PubMed",
                    source_id="1",
                    title="Erenumab treatment for example disease",
                    summary="A clinical trial evaluated erenumab for symptom prevention.",
                    url="https://pubmed.ncbi.nlm.nih.gov/1/",
                    evidence_type="clinical_trial",
                    targets=["Calcitonin Gene-Related Peptide"],
                    drugs=["Erenumab"],
                    confidence=0.78,
                )
            ]
            return await agent.run(profile, evidence)

        candidates, trace = asyncio.run(run_case())

        self.assertEqual(trace.status, "complete")
        self.assertEqual(trace.metadata["generation_mode"], "literature_heuristic")
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].name, "Erenumab")
        self.assertEqual(candidates[0].evidence_ids, ["pubmed-1"])
        self.assertEqual(candidates[0].candidate_type, "literature-derived repurposing hypothesis")


if __name__ == "__main__":
    unittest.main()
