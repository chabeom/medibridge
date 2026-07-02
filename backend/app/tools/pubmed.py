from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

import httpx
from dotenv import load_dotenv


class PubMedClient:
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def __init__(
        self,
        api_key: str | None = None,
        email: str | None = None,
        tool: str | None = None,
        timeout_seconds: float = 12.0,
    ) -> None:
        env_path = Path(__file__).resolve().parents[3] / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        else:
            load_dotenv()

        self.api_key = api_key or os.getenv("NCBI_API_KEY", "")
        self.email = email or os.getenv("NCBI_EMAIL", "")
        self.tool = tool or os.getenv("NCBI_TOOL", "medibridge")
        self.timeout_seconds = timeout_seconds

    async def search(self, query: str, limit: int = 20) -> list[dict]:
        pmids = await self._search_pmids(query=query, limit=limit)
        if not pmids:
            return []

        xml_text = await self._fetch_pubmed_xml(pmids)
        return self._parse_articles(xml_text)

    async def _search_pmids(self, query: str, limit: int) -> list[str]:
        params = self._base_params()
        params.update(
            {
                "db": "pubmed",
                "term": query,
                "retmode": "json",
                "retmax": str(limit),
                "sort": "relevance",
            }
        )

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(f"{self.base_url}/esearch.fcgi", params=params)
            response.raise_for_status()

        data = response.json()
        ids = data.get("esearchresult", {}).get("idlist", [])
        return [str(item) for item in ids]

    async def _fetch_pubmed_xml(self, pmids: list[str]) -> str:
        params = self._base_params()
        params.update(
            {
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "xml",
            }
        )

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(f"{self.base_url}/efetch.fcgi", params=params)
            response.raise_for_status()

        return response.text

    def _base_params(self) -> dict[str, str]:
        params = {"tool": self.tool}
        if self.email:
            params["email"] = self.email
        if self.api_key:
            params["api_key"] = self.api_key
        return params

    def _parse_articles(self, xml_text: str) -> list[dict[str, Any]]:
        root = ElementTree.fromstring(xml_text)
        records: list[dict[str, Any]] = []

        for article in root.findall(".//PubmedArticle"):
            pmid = self._text(article.find(".//PMID"))
            if not pmid:
                continue

            title = self._text(article.find(".//ArticleTitle")) or "Untitled PubMed record"
            abstract = self._abstract_text(article)
            pub_types = [self._text(item) for item in article.findall(".//PublicationType")]
            pub_types = [item for item in pub_types if item]
            mesh_terms = [self._text(item) for item in article.findall(".//MeshHeading/DescriptorName")]
            mesh_terms = [item for item in mesh_terms if item]
            keywords = [self._text(item) for item in article.findall(".//KeywordList/Keyword")]
            keywords = [item for item in keywords if item]
            chemicals = [self._text(item) for item in article.findall(".//Chemical/NameOfSubstance")]
            chemicals = [item for item in chemicals if item]
            doi = self._article_id(article, "doi")

            records.append(
                {
                    "pmid": pmid,
                    "title": self._clean_text(title),
                    "abstract": self._clean_text(abstract),
                    "journal": self._text(article.find(".//Journal/Title")),
                    "publication_year": self._publication_year(article),
                    "publication_types": pub_types,
                    "mesh_terms": mesh_terms,
                    "keywords": keywords,
                    "drugs": chemicals,
                    "doi": doi,
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    "evidence_type": self._evidence_type(pub_types),
                    "confidence": self._confidence(pub_types, abstract),
                }
            )

        return records

    def _abstract_text(self, article: ElementTree.Element) -> str:
        sections: list[str] = []
        for item in article.findall(".//Abstract/AbstractText"):
            text = self._text(item)
            if not text:
                continue
            label = item.attrib.get("Label")
            sections.append(f"{label}: {text}" if label else text)
        return " ".join(sections)

    def _publication_year(self, article: ElementTree.Element) -> str:
        year = self._text(article.find(".//JournalIssue/PubDate/Year"))
        if year:
            return year

        medline_date = self._text(article.find(".//JournalIssue/PubDate/MedlineDate"))
        match = re.search(r"\d{4}", medline_date)
        return match.group(0) if match else ""

    def _article_id(self, article: ElementTree.Element, id_type: str) -> str:
        for item in article.findall(".//ArticleIdList/ArticleId"):
            if item.attrib.get("IdType", "").lower() == id_type.lower():
                return self._text(item)
        return ""

    def _evidence_type(self, publication_types: list[str]) -> str:
        lowered = " ".join(publication_types).lower()
        if "randomized controlled trial" in lowered:
            return "randomized_controlled_trial"
        if "clinical trial" in lowered:
            return "clinical_trial"
        if "meta-analysis" in lowered:
            return "meta_analysis"
        if "review" in lowered:
            return "review"
        return "publication"

    def _confidence(self, publication_types: list[str], abstract: str) -> float:
        lowered = " ".join(publication_types).lower()
        score = 0.5
        if abstract:
            score += 0.08
        if "randomized controlled trial" in lowered:
            score += 0.26
        elif "clinical trial" in lowered:
            score += 0.2
        elif "meta-analysis" in lowered:
            score += 0.22
        elif "review" in lowered:
            score += 0.12
        return round(min(score, 0.9), 2)

    def _text(self, element: ElementTree.Element | None) -> str:
        if element is None:
            return ""
        return self._clean_text(" ".join(element.itertext()))

    def _clean_text(self, value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()
