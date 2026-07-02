from __future__ import annotations

from app.models.schemas import AgentTrace, ClinicalProtocolDraft, DiseaseProfile, DrugCandidate


DISEASE_DISPLAY_NAMES: dict[str, str] = {}


class ClinicalDesignAgent:
    name = "Clinical Design Agent"

    async def run(
        self,
        profile: DiseaseProfile,
        candidates: list[DrugCandidate],
    ) -> tuple[list[ClinicalProtocolDraft], AgentTrace]:
        drafts: list[ClinicalProtocolDraft] = []
        display_disease = DISEASE_DISPLAY_NAMES.get(profile.disease.canonical_name, profile.disease.canonical_name)
        primary_endpoint = profile.biomarkers[0] if profile.biomarkers else "질환 특이 검증 endpoint"
        secondary = profile.biomarkers[1:] or ["안전성 및 내약성", "환자 보고 결과"]
        subgroup = profile.patient_subgroups[0] if profile.patient_subgroups else profile.disease.canonical_name

        for candidate in candidates[:3]:
            drafts.append(
                ClinicalProtocolDraft(
                    candidate_name=candidate.name,
                    indication=display_disease,
                    phase="1b/2a상 가설 검증 연구",
                    population=f"표준치료 검토 후 {subgroup}에 해당하는 성인 환자",
                    primary_endpoint=f"기저치 대비 {primary_endpoint} 변화",
                    secondary_endpoints=secondary[:3],
                    inclusion_criteria=[
                        f"{display_disease} 진단이 확인된 환자",
                        "해당되는 경우 표준치료가 안정적으로 유지된 환자",
                        "기저 질병 활성도 또는 진행 지표를 측정할 수 있는 환자",
                    ],
                    exclusion_criteria=[
                        "후보 약물 또는 동일 계열 약물에 금기가 있는 환자",
                        "안전성 해석을 어렵게 하는 중증 조절 불량 동반질환이 있는 환자",
                        "충분한 washout 없이 최근 시험약에 노출된 환자",
                    ],
                    safety_monitoring=[
                        "이상반응 및 중대한 이상반응 모니터링",
                        "후보 약물 라벨에 기반한 실험실 안전성 검사",
                        "약물 상호작용 및 투약 중단 기준 검토",
                    ],
                )
            )

        return drafts, AgentTrace(
            agent=self.name,
            status="complete",
            summary="Drafted early clinical feasibility outlines for top candidates.",
            metadata={"draft_count": len(drafts)},
        )
