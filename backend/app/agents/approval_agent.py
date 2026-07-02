from __future__ import annotations

import re

from app.models.schemas import AgentTrace, CandidateApprovalReview, DiseaseProfile, DrugCandidate


STANDARD_THERAPIES_BY_DISEASE: dict[str, set[str]] = {
    "migraine disorders": {
        "almotriptan",
        "amitriptyline",
        "atogepant",
        "botulinum toxin",
        "divalproex",
        "eletriptan",
        "eptinezumab",
        "erenumab",
        "fremanezumab",
        "frovatriptan",
        "galcanezumab",
        "lasmiditan",
        "naratriptan",
        "onabotulinumtoxina",
        "propranolol",
        "rimegepant",
        "rizatriptan",
        "sumatriptan",
        "topiramate",
        "ubrogepant",
        "valproate",
        "zolmitriptan",
    },
    "diabetes mellitus": {
        "acarbose",
        "alogliptin",
        "canagliflozin",
        "dapagliflozin",
        "dulaglutide",
        "empagliflozin",
        "exenatide",
        "glimepiride",
        "glipizide",
        "glyburide",
        "insulin",
        "linagliptin",
        "liraglutide",
        "metformin",
        "pioglitazone",
        "repaglinide",
        "rosiglitazone",
        "saxagliptin",
        "semaglutide",
        "sitagliptin",
    },
    "diabetes mellitus, type 2": {
        "acarbose",
        "alogliptin",
        "canagliflozin",
        "dapagliflozin",
        "dulaglutide",
        "empagliflozin",
        "exenatide",
        "glimepiride",
        "glipizide",
        "glyburide",
        "insulin",
        "linagliptin",
        "liraglutide",
        "metformin",
        "pioglitazone",
        "repaglinide",
        "rosiglitazone",
        "saxagliptin",
        "semaglutide",
        "sitagliptin",
    },
    "hypertension": {
        "amlodipine",
        "atenolol",
        "candesartan",
        "chlorthalidone",
        "enalapril",
        "hydrochlorothiazide",
        "irbesartan",
        "lisinopril",
        "losartan",
        "metoprolol",
        "nifedipine",
        "olmesartan",
        "propranolol",
        "valsartan",
    },
    "asthma": {
        "albuterol",
        "beclomethasone",
        "budesonide",
        "dupilumab",
        "fluticasone",
        "formoterol",
        "mepolizumab",
        "montelukast",
        "omalizumab",
        "prednisone",
        "salmeterol",
        "tiotropium",
    },
    "covid-19": {
        "baricitinib",
        "dexamethasone",
        "molnupiravir",
        "nirmatrelvir",
        "remdesivir",
        "ritonavir",
        "tocilizumab",
    },
    "influenza": {
        "baloxavir",
        "oseltamivir",
        "peramivir",
        "zanamivir",
    },
}


class ApprovalStatusAgent:
    name = "Approval Status Agent"

    async def run(
        self,
        profile: DiseaseProfile,
        candidates: list[DrugCandidate],
    ) -> tuple[list[DrugCandidate], list[CandidateApprovalReview], AgentTrace]:
        standard_therapies = self._standard_therapies_for(profile)
        filtered: list[DrugCandidate] = []
        reviews: list[CandidateApprovalReview] = []

        for candidate in candidates:
            normalized_name = self._normalize_drug_name(candidate.name)
            is_standard = self._matches_standard_therapy(normalized_name, standard_therapies)
            is_reference = "reference" in candidate.candidate_type.lower()

            if is_standard or is_reference:
                candidate.approval_status = "excluded_approved_or_standard"
                candidate.approval_reason = self._excluded_reason(profile, candidate)
                reviews.append(
                    CandidateApprovalReview(
                        candidate_name=candidate.name,
                        status=candidate.approval_status,
                        reason=candidate.approval_reason,
                        evidence_ids=list(candidate.evidence_ids),
                    )
                )
                continue

            candidate.approval_status = "kept_repurposing_candidate"
            candidate.approval_reason = (
                "현재 내부 승인/표준치료 필터에서는 해당 질환의 기존 치료제로 분류되지 않았습니다. "
                "openFDA, Drugs@FDA, DailyMed 연동으로 추가 검증이 필요합니다."
            )
            candidate.warnings.append("승인 적응증 자동 검증은 내부 표준치료 사전 기준의 1차 필터입니다.")
            reviews.append(
                CandidateApprovalReview(
                    candidate_name=candidate.name,
                    status=candidate.approval_status,
                    reason=candidate.approval_reason,
                    evidence_ids=list(candidate.evidence_ids),
                )
            )
            filtered.append(candidate)

        excluded_count = len(candidates) - len(filtered)
        status = "warning" if candidates and not filtered else "complete"
        return filtered, reviews, AgentTrace(
            agent=self.name,
            status=status,
            summary="Filtered candidates that are already approved or standard therapies for the requested disease.",
            metadata={
                "input_candidates": len(candidates),
                "kept_candidates": len(filtered),
                "excluded_candidates": excluded_count,
                "disease": profile.disease.canonical_name,
                "filter_source": "internal_standard_therapy_dictionary",
            },
        )

    def _standard_therapies_for(self, profile: DiseaseProfile) -> set[str]:
        terms = [profile.disease.canonical_name, *profile.disease.synonyms]
        standard_therapies: set[str] = set()
        for term in terms:
            standard_therapies.update(STANDARD_THERAPIES_BY_DISEASE.get(term.lower(), set()))
        return standard_therapies

    def _matches_standard_therapy(self, normalized_name: str, standard_therapies: set[str]) -> bool:
        if normalized_name in standard_therapies:
            return True
        return any(therapy in normalized_name or normalized_name in therapy for therapy in standard_therapies)

    def _normalize_drug_name(self, name: str) -> str:
        lowered = name.lower().replace("®", "").replace("™", "")
        lowered = re.sub(r"[^a-z0-9]+", " ", lowered)
        return " ".join(lowered.split())

    def _excluded_reason(self, profile: DiseaseProfile, candidate: DrugCandidate) -> str:
        return (
            f"{candidate.name}은(는) {profile.disease.canonical_name}에서 이미 승인 또는 표준치료로 쓰이는 약물군에 해당할 가능성이 높아 "
            "재창출 후보가 아니라 기준 치료제/비교군으로 분류했습니다."
        )
