from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

import httpx
from dotenv import load_dotenv


class ScienceOnClient:
    default_base_url = "https://openapi.ndsl.kr/itemsearch.do"

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        ticket: str | None = None,
        timeout_seconds: float = 12.0,
    ) -> None:
        env_path = Path(__file__).resolve().parents[3] / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        else:
            load_dotenv()

        self.api_key = api_key or os.getenv("SCIENCEON_API_KEY", "") or os.getenv("SCIENCEON_SERVICE_KEY", "")
        self.base_url = base_url or os.getenv("SCIENCEON_API_URL", self.default_base_url)
        self.ticket = ticket or os.getenv("SCIENCEON_TICKET", "ARTI")
        self.key_param = os.getenv("SCIENCEON_KEY_PARAM", "keyValue")
        self.query_param = os.getenv("SCIENCEON_QUERY_PARAM", "query")
        self.ticket_param = os.getenv("SCIENCEON_TICKET_PARAM", "target")
        self.search_field_param = os.getenv("SCIENCEON_SEARCH_FIELD_PARAM", "searchField")
        self.limit_param = os.getenv("SCIENCEON_LIMIT_PARAM", "displayCount")
        self.start_param = os.getenv("SCIENCEON_START_PARAM", "startPosition")
        self.timeout_seconds = timeout_seconds
        self.enabled = os.getenv("SCIENCEON_ENABLED", "true").lower() not in {"0", "false", "no", "off"}

    def is_configured(self) -> bool:
        return bool(self.enabled and self.api_key and self.base_url)

    async def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        if not self.is_configured() or not query.strip():
            return []

        params = self._base_params(query=query, limit=limit)
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()

        return self._parse_response(response.text, response.headers.get("content-type", ""))

    def _base_params(self, query: str, limit: int) -> dict[str, str]:
        params = {
            self.key_param: self.api_key,
            self.query_param: query,
            self.limit_param: str(limit),
            self.start_param: "1",
            "returnType": os.getenv("SCIENCEON_RETURN_TYPE", "json"),
            "sortby": os.getenv("SCIENCEON_SORT", "pubyear"),
        }
        if self.ticket_param:
            params[self.ticket_param] = self.ticket
        if self.search_field_param:
            params[self.search_field_param] = os.getenv("SCIENCEON_SEARCH_FIELD", "BI")
        return params

    def _parse_response(self, text: str, content_type: str = "") -> list[dict[str, Any]]:
        if "json" in content_type.lower():
            try:
                return self._parse_json(json.loads(text))
            except json.JSONDecodeError:
                pass

        try:
            return self._parse_json(json.loads(text))
        except json.JSONDecodeError:
            return self._parse_xml(text)

    def _parse_json(self, data: Any) -> list[dict[str, Any]]:
        records = self._collect_record_dicts(data)
        return [record for record in (self._normalize_record(item) for item in records) if record.get("title")]

    def _collect_record_dicts(self, value: Any) -> list[dict[str, Any]]:
        if isinstance(value, list):
            dict_items = [item for item in value if isinstance(item, dict)]
            if dict_items and any(self._looks_like_record(item) for item in dict_items):
                return dict_items

            records: list[dict[str, Any]] = []
            for item in dict_items:
                records.extend(self._collect_record_dicts(item))
            return records

        if not isinstance(value, dict):
            return []

        for key in ("item", "items", "record", "records", "result", "results", "data", "documents"):
            child = value.get(key)
            if child is not None:
                records = self._collect_record_dicts(child)
                if records:
                    return records

        return [value] if self._looks_like_record(value) else []

    def _looks_like_record(self, value: dict[str, Any]) -> bool:
        lowered_keys = {str(key).lower() for key in value}
        return bool(lowered_keys & {"title", "titl", "artititle", "kor_title", "eng_title", "subject", "paper_title"})

    def _parse_xml(self, text: str) -> list[dict[str, Any]]:
        try:
            root = ElementTree.fromstring(text)
        except ElementTree.ParseError:
            return []

        nodes = root.findall(".//item") or root.findall(".//record") or root.findall(".//result")
        records: list[dict[str, Any]] = []
        for node in nodes:
            raw: dict[str, str] = {}
            for child in list(node):
                tag = child.tag.split("}")[-1]
                raw[tag] = self._clean_text(" ".join(child.itertext()))
            record = self._normalize_record(raw)
            if record.get("title"):
                records.append(record)
        return records

    def _normalize_record(self, raw: dict[str, Any]) -> dict[str, Any]:
        lower = {str(key).lower(): value for key, value in raw.items()}

        title = self._first_text(lower, "title", "titl", "artititle", "paper_title", "kor_title", "eng_title")
        abstract = self._first_text(lower, "abstract", "abs", "summary", "description", "kor_abstract", "eng_abstract")
        journal = self._first_text(lower, "journal", "journalname", "source", "pubname", "publisher", "pub_name")
        year = self._first_text(lower, "year", "pubyear", "publicationyear", "pub_year", "date")
        doi = self._first_text(lower, "doi")
        source_id = self._first_text(lower, "id", "cn", "controlno", "docid", "artiid", "articleid")
        url = self._first_text(lower, "url", "link", "detailurl", "landingurl")
        keywords = self._keywords(self._first_value(lower, "keyword", "keywords", "kwd", "subject"))

        return {
            "source_id": source_id,
            "title": title,
            "abstract": abstract,
            "journal": journal,
            "publication_year": self._year(year),
            "doi": doi,
            "url": url,
            "keywords": keywords,
            "authors": self._first_text(lower, "author", "authors", "creator"),
            "source_database": self._first_text(lower, "db", "database", "provider") or "ScienceON",
        }

    def _first_value(self, data: dict[str, Any], *keys: str) -> Any:
        for key in keys:
            value = data.get(key)
            if value:
                return value
        return ""

    def _first_text(self, data: dict[str, Any], *keys: str) -> str:
        return self._clean_text(str(self._first_value(data, *keys)))

    def _keywords(self, value: Any) -> list[str]:
        if isinstance(value, list):
            return [self._clean_text(str(item)) for item in value if self._clean_text(str(item))]
        text = self._clean_text(str(value))
        if not text:
            return []
        return [item.strip() for item in re.split(r"[;,|]", text) if item.strip()]

    def _year(self, value: str) -> str:
        match = re.search(r"\d{4}", value)
        return match.group(0) if match else ""

    def _clean_text(self, value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()
