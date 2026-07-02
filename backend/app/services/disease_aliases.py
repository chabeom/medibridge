from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class DiseaseAlias:
    canonical_name: str
    synonyms: tuple[str, ...]
    identifiers: dict[str, str] = field(default_factory=dict)


_ALIASES: dict[str, DiseaseAlias] = {}


def _register(
    canonical_name: str,
    *aliases: str,
    synonyms: tuple[str, ...] = (),
    identifiers: dict[str, str] | None = None,
) -> None:
    alias = DiseaseAlias(
        canonical_name=canonical_name,
        synonyms=synonyms or (canonical_name,),
        identifiers=identifiers or {},
    )
    for value in (canonical_name, *aliases, *synonyms):
        key = " ".join(value.strip().lower().split())
        if key:
            _ALIASES[key] = alias


_register(
    "Common Cold",
    "감기",
    "일반 감기",
    "common cold",
    synonyms=("Common Cold", "acute viral nasopharyngitis", "upper respiratory tract infection"),
    identifiers={"mesh": "D003139"},
)
_register(
    "Influenza",
    "독감",
    "인플루엔자",
    "flu",
    synonyms=("Influenza", "flu"),
    identifiers={"mesh": "D007251"},
)
_register(
    "COVID-19",
    "코로나",
    "코로나19",
    "covid",
    "covid-19",
    synonyms=("COVID-19", "SARS-CoV-2 infection"),
    identifiers={"mesh": "D000086382"},
)
_register(
    "Diabetes Mellitus",
    "당뇨",
    "당뇨병",
    "diabetes",
    synonyms=("Diabetes Mellitus",),
    identifiers={"mesh": "D003920"},
)
_register(
    "Diabetes Mellitus, Type 2",
    "제2형 당뇨",
    "제2형 당뇨병",
    "2형 당뇨",
    "type 2 diabetes",
    synonyms=("Diabetes Mellitus, Type 2", "type 2 diabetes", "T2D"),
    identifiers={"mesh": "D003924"},
)
_register(
    "Hypertension",
    "고혈압",
    synonyms=("Hypertension", "high blood pressure"),
    identifiers={"mesh": "D006973"},
)
_register(
    "Migraine Disorders",
    "편두통",
    "migraine",
    synonyms=("Migraine Disorders", "migraine"),
    identifiers={"mesh": "D008881"},
)
_register(
    "Dementia",
    "치매",
    synonyms=("Dementia", "cognitive impairment"),
    identifiers={"mesh": "D003704"},
)
_register(
    "Alzheimer Disease",
    "알츠하이머",
    "알츠하이머병",
    "alzheimer",
    "alzheimer disease",
    synonyms=("Alzheimer Disease", "Alzheimer's disease"),
    identifiers={"mesh": "D000544"},
)
_register(
    "Parkinson Disease",
    "파킨슨",
    "파킨슨병",
    "parkinson",
    synonyms=("Parkinson Disease", "Parkinson's disease"),
    identifiers={"mesh": "D010300"},
)
_register(
    "Asthma",
    "천식",
    synonyms=("Asthma",),
    identifiers={"mesh": "D001249"},
)
_register(
    "Pulmonary Disease, Chronic Obstructive",
    "만성폐쇄성폐질환",
    "만성 폐쇄성 폐질환",
    "copd",
    synonyms=("Pulmonary Disease, Chronic Obstructive", "COPD"),
    identifiers={"mesh": "D029424"},
)
_register(
    "Lung Neoplasms",
    "폐암",
    "lung cancer",
    synonyms=("Lung Neoplasms", "lung cancer"),
    identifiers={"mesh": "D008175"},
)
_register(
    "Breast Neoplasms",
    "유방암",
    "breast cancer",
    synonyms=("Breast Neoplasms", "breast cancer"),
    identifiers={"mesh": "D001943"},
)
_register(
    "Colorectal Neoplasms",
    "대장암",
    "결장직장암",
    "colorectal cancer",
    synonyms=("Colorectal Neoplasms", "colorectal cancer"),
    identifiers={"mesh": "D015179"},
)
_register(
    "Stomach Neoplasms",
    "위암",
    "gastric cancer",
    synonyms=("Stomach Neoplasms", "gastric cancer"),
    identifiers={"mesh": "D013274"},
)
_register(
    "Liver Neoplasms",
    "간암",
    "liver cancer",
    "hepatocellular carcinoma",
    synonyms=("Liver Neoplasms", "liver cancer", "hepatocellular carcinoma"),
    identifiers={"mesh": "D008113"},
)
_register(
    "Pancreatic Neoplasms",
    "췌장암",
    "pancreatic cancer",
    synonyms=("Pancreatic Neoplasms", "pancreatic cancer"),
    identifiers={"mesh": "D010190"},
)
_register(
    "Stroke",
    "뇌졸중",
    "stroke",
    synonyms=("Stroke", "cerebrovascular accident"),
    identifiers={"mesh": "D020521"},
)
_register(
    "Arthritis, Rheumatoid",
    "류마티스관절염",
    "류마티스 관절염",
    "rheumatoid arthritis",
    synonyms=("Arthritis, Rheumatoid", "rheumatoid arthritis"),
    identifiers={"mesh": "D001172"},
)
_register(
    "Depression",
    "우울증",
    "depression",
    synonyms=("Depression", "depressive disorder"),
    identifiers={"mesh": "D003863"},
)
_register(
    "Schizophrenia",
    "조현병",
    synonyms=("Schizophrenia",),
    identifiers={"mesh": "D012559"},
)
_register(
    "Amyotrophic Lateral Sclerosis",
    "루게릭병",
    "루게릭",
    "als",
    synonyms=("Amyotrophic Lateral Sclerosis", "ALS"),
    identifiers={"mesh": "D000690"},
)


def find_disease_alias(input_text: str) -> DiseaseAlias | None:
    key = " ".join(input_text.strip().lower().split())
    return _ALIASES.get(key)
