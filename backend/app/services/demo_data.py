from __future__ import annotations

from app.models.schemas import EvidenceItem


DEMO_DISEASES = {
    "amyotrophic lateral sclerosis": {
        "canonical_name": "Amyotrophic Lateral Sclerosis",
        "synonyms": ["ALS", "Lou Gehrig disease", "motor neuron disease", "루게릭병"],
        "identifiers": {"mesh": "D000690"},
        "unmet_need": (
            "근위축성 측삭경화증은 질병 진행을 늦추는 치료 옵션이 제한적인 진행성 신경퇴행성 질환입니다. "
            "따라서 질환 기전, 바이오마커, 기존 약물 작용기전을 연결한 근거 기반 재창출 가설이 필요합니다."
        ),
        "mechanisms": [
            "글루타메이트 흥분독성",
            "산화 스트레스",
            "신경염증",
            "단백질 응집",
            "운동신경세포 퇴행",
        ],
        "targets": ["SOD1", "TARDBP", "FUS", "C9orf72", "글루타메이트 신호", "미세아교세포 활성"],
        "biomarkers": ["ALSFRS-R", "신경섬유 경쇄", "강제폐활량"],
        "patient_subgroups": ["SOD1 변이 ALS", "C9orf72 관련 ALS", "빠른 진행 환자군"],
        "evidence": [
            EvidenceItem(
                id="demo-als-001",
                disease_name="Amyotrophic Lateral Sclerosis",
                source="demo",
                source_id="DEMO-ALS-PATHWAY-001",
                title="ALS 질환 생물학 데모 근거",
                summary=(
                    "ALS 진행은 흥분독성, 산화 스트레스, 신경염증, 운동신경세포 취약성과 연결될 수 있습니다."
                ),
                url="https://example.org/demo/als-pathway",
                evidence_type="disease_biology",
                targets=["글루타메이트 신호", "미세아교세포 활성"],
                confidence=0.72,
            ),
            EvidenceItem(
                id="demo-als-002",
                disease_name="Amyotrophic Lateral Sclerosis",
                source="demo",
                source_id="DEMO-ALS-TRIAL-001",
                title="ALS 임상 가능성 데모 근거",
                summary=(
                    "ALSFRS-R, 생존, 호흡기능, 신경섬유 경쇄는 초기 임상 설계에서 검토할 수 있는 주요 endpoint입니다."
                ),
                url="https://example.org/demo/als-clinical",
                evidence_type="clinical_design",
                targets=["ALSFRS-R", "신경섬유 경쇄"],
                confidence=0.68,
            ),
            EvidenceItem(
                id="demo-als-003",
                disease_name="Amyotrophic Lateral Sclerosis",
                source="demo",
                source_id="DEMO-ALS-DRUG-001",
                title="신경염증 조절 재창출 데모 근거",
                summary=(
                    "기존 면역조절제와 스트레스 반응 조절 약물은 확정 치료제가 아니라 검토 가능한 재창출 가설로 다룹니다."
                ),
                url="https://example.org/demo/als-repurposing",
                evidence_type="repurposing_hypothesis",
                targets=["미세아교세포 활성", "산화 스트레스"],
                drugs=["Masitinib", "Pioglitazone", "Edaravone"],
                confidence=0.61,
            ),
        ],
        "candidate_seeds": [
            {
                "name": "Masitinib",
                "candidate_type": "investigational repurposing hypothesis",
                "mechanism": "티로신 키나아제 및 신경염증 조절",
                "targets": ["미세아교세포 활성"],
                "evidence_ids": ["demo-als-001", "demo-als-003"],
                "rationale": (
                    "ALS 병태생리에 염증성 교세포 활성화가 포함되며, Masitinib은 면역조절 기전과 연결될 수 있어 "
                    "재창출 가설 후보로 우선 검토할 수 있습니다."
                ),
                "safety_summary": "이상반응, 투약 중단 위험, 기존 임상시험 이력에 대한 세밀한 검토가 필요합니다.",
                "chemistry": {"molecular_weight": 498.6, "logp": 4.1, "hbd": 2, "hba": 6, "tpsa": 84.0},
                "feasibility": 0.68,
                "novelty": 0.62,
                "safety_risk": 0.46,
            },
            {
                "name": "Pioglitazone",
                "candidate_type": "mechanism-based repurposing hypothesis",
                "mechanism": "PPAR-gamma 경로 조절 및 항염증 효과",
                "targets": ["산화 스트레스", "미세아교세포 활성"],
                "evidence_ids": ["demo-als-001", "demo-als-003"],
                "rationale": (
                    "대사 경로와 염증 경로가 ALS의 스트레스 생물학과 일부 겹칠 수 있어, 비교적 접근성이 높은 "
                    "기전 기반 재창출 가설로 검토할 수 있습니다."
                ),
                "safety_summary": "약물 계열에서 알려진 위험을 대상 환자군 특성과 함께 검토해야 합니다.",
                "chemistry": {"molecular_weight": 356.4, "logp": 3.3, "hbd": 1, "hba": 4, "tpsa": 84.0},
                "feasibility": 0.58,
                "novelty": 0.55,
                "safety_risk": 0.42,
            },
            {
                "name": "Edaravone",
                "candidate_type": "approved comparator or reference candidate",
                "mechanism": "자유라디칼 제거 및 산화 스트레스 조절",
                "targets": ["산화 스트레스"],
                "evidence_ids": ["demo-als-001", "demo-als-002"],
                "rationale": (
                    "산화 스트레스 축과 임상 설계 비교를 위한 기준 후보로 사용할 수 있습니다. 다만 새로운 재창출 "
                    "주장이라기보다는 비교 기준에 가깝습니다."
                ),
                "safety_summary": "기존 허가 라벨과 투여 경로 제약을 함께 검토해야 합니다.",
                "chemistry": {"molecular_weight": 174.2, "logp": 1.2, "hbd": 1, "hba": 2, "tpsa": 36.0},
                "feasibility": 0.75,
                "novelty": 0.18,
                "safety_risk": 0.28,
            },
        ],
    }
    ,
    "common cold": {
        "canonical_name": "Common Cold",
        "synonyms": [
            "감기",
            "common cold",
            "acute viral nasopharyngitis",
            "viral upper respiratory infection",
            "URI",
            "rhinovirus infection",
        ],
        "identifiers": {"mesh": "D003139"},
        "unmet_need": (
            "감기는 대개 자연 회복되지만 환자 수가 매우 많고, 병원체별 특이 치료 옵션이 제한적입니다. "
            "따라서 안전한 증상 완화와 숙주 반응 조절 전략을 근거 기반으로 검토할 필요가 있습니다."
        ),
        "mechanisms": [
            "리노바이러스 및 계절성 호흡기 바이러스 감염",
            "비강 상피 염증",
            "숙주 인터페론 반응",
            "점액 과다분비",
            "상기도 증상 부담",
        ],
        "targets": [
            "ICAM-1 매개 바이러스 진입",
            "비강 상피 염증",
            "콧물 경로",
            "숙주 항바이러스 반응",
            "바이러스 복제",
        ],
        "biomarkers": [
            "증상 중증도 점수",
            "증상 해소까지의 시간",
            "바이러스량",
            "비강 분비물 점수",
        ],
        "patient_subgroups": [
            "초기 단순 바이러스성 상기도 감염 성인",
            "콧물 증상이 두드러지는 환자군",
            "리노바이러스 양성 확인 환자군",
        ],
        "evidence": [
            EvidenceItem(
                id="demo-cold-001",
                disease_name="Common Cold",
                source="demo",
                source_id="DEMO-COLD-PATHWAY-001",
                title="감기 질환 생물학 데모 근거",
                summary=(
                    "감기는 리노바이러스 감염, 상피 염증, 점액 분비, 숙주 인터페론 반응을 중심으로 "
                    "가설을 세울 수 있는 바이러스성 상기도 증후군입니다."
                ),
                url="https://example.org/demo/common-cold-pathway",
                evidence_type="disease_biology",
                targets=["비강 상피 염증", "숙주 항바이러스 반응"],
                confidence=0.7,
            ),
            EvidenceItem(
                id="demo-cold-002",
                disease_name="Common Cold",
                source="demo",
                source_id="DEMO-COLD-CLINICAL-001",
                title="감기 임상 endpoint 데모 근거",
                summary=(
                    "증상 중증도, 증상 해소까지의 시간, 비강 분비물, 바이러스량은 초기 임상 가능성 평가에 "
                    "사용할 수 있는 endpoint입니다."
                ),
                url="https://example.org/demo/common-cold-clinical",
                evidence_type="clinical_design",
                targets=["증상 중증도 점수", "증상 해소까지의 시간", "바이러스량"],
                confidence=0.66,
            ),
            EvidenceItem(
                id="demo-cold-003",
                disease_name="Common Cold",
                source="demo",
                source_id="DEMO-COLD-DRUG-001",
                title="증상 및 숙주 반응 조절 재창출 데모 근거",
                summary=(
                    "승인된 증상 조절 약물과 광범위 숙주 반응/항바이러스 가설을 검토할 수 있습니다. "
                    "단, 증상 완화와 질병 경과 변경 주장은 명확히 구분해야 합니다."
                ),
                url="https://example.org/demo/common-cold-repurposing",
                evidence_type="repurposing_hypothesis",
                targets=["콧물 경로", "숙주 항바이러스 반응", "바이러스 복제"],
                drugs=["Ipratropium bromide", "Nitazoxanide", "Zinc acetate"],
                confidence=0.58,
            ),
        ],
        "candidate_seeds": [
            {
                "name": "Ipratropium bromide",
                "candidate_type": "symptom-control reference candidate",
                "mechanism": "비강 내 항콜린 작용을 통한 콧물 증상 완화",
                "targets": ["콧물 경로"],
                "evidence_ids": ["demo-cold-002", "demo-cold-003"],
                "rationale": (
                    "감기는 증상 부담이 크고 콧물은 측정 가능한 초기 endpoint이므로, Ipratropium bromide를 "
                    "실용적인 증상 조절 기준 후보로 검토할 수 있습니다. 이는 항바이러스 치료 주장이 아니라 "
                    "증상 완화 가설입니다."
                ),
                "safety_summary": "비강 건조, 코피, 항콜린성 주의사항, 투여 경로별 내약성을 검토해야 합니다.",
                "chemistry": {"molecular_weight": 332.5, "logp": 2.7, "hbd": 1, "hba": 4, "tpsa": 52.0},
                "feasibility": 0.78,
                "novelty": 0.32,
                "safety_risk": 0.22,
            },
            {
                "name": "Nitazoxanide",
                "candidate_type": "broad antiviral repurposing hypothesis",
                "mechanism": "숙주 지향 및 광범위 항바이러스 경로 조절",
                "targets": ["숙주 항바이러스 반응", "바이러스 복제"],
                "evidence_ids": ["demo-cold-001", "demo-cold-003"],
                "rationale": (
                    "초기 바이러스성 상기도 감염이 확인된 환자군에서는 광범위 항바이러스 재창출 가설로 검토할 수 "
                    "있습니다. 다만 감기의 원인 바이러스가 다양하므로 근거 강도 평가는 신중해야 합니다."
                ),
                "safety_summary": "임상 설계 전 위장관 내약성, 약물 상호작용, 기존 사용 이력을 검토해야 합니다.",
                "chemistry": {"molecular_weight": 307.3, "logp": 2.1, "hbd": 1, "hba": 7, "tpsa": 123.0},
                "feasibility": 0.55,
                "novelty": 0.64,
                "safety_risk": 0.35,
            },
            {
                "name": "Zinc acetate",
                "candidate_type": "supportive-care comparator or hypothesis",
                "mechanism": "국소 항바이러스 및 숙주 반응 보조 기전 가설",
                "targets": ["숙주 항바이러스 반응"],
                "evidence_ids": ["demo-cold-001", "demo-cold-002", "demo-cold-003"],
                "rationale": (
                    "증상 지속 기간과 초기 사용 조건을 중심으로 한 보조요법 가설 또는 비교 후보로 활용할 수 있습니다. "
                    "확정적인 질병 경과 변경 주장으로 해석하면 안 됩니다."
                ),
                "safety_summary": "오심, 미각 이상, 제형, 효능 과장 위험을 함께 검토해야 합니다.",
                "chemistry": {"molecular_weight": 183.5, "logp": 0.0, "hbd": 0, "hba": 4, "tpsa": 80.0},
                "feasibility": 0.7,
                "novelty": 0.24,
                "safety_risk": 0.2,
            },
        ],
    },
}


def build_synonym_index() -> dict[str, str]:
    index: dict[str, str] = {}
    for key, disease in DEMO_DISEASES.items():
        index[key] = key
        index[disease["canonical_name"].lower()] = key
        for synonym in disease["synonyms"]:
            index[synonym.lower()] = key
    return index
