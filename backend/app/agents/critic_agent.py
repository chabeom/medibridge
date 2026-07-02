from __future__ import annotations

from app.models.schemas import AgentTrace, ClinicalProtocolDraft, CriticFinding, DrugCandidate, EvidenceItem


class CriticAgent:
    name = "Critic Agent"

    async def run(
        self,
        evidence: list[EvidenceItem],
        candidates: list[DrugCandidate],
        clinical_drafts: list[ClinicalProtocolDraft],
        citation_warnings: list[str],
    ) -> tuple[list[CriticFinding], AgentTrace]:
        findings: list[CriticFinding] = []

        if len(evidence) < 3:
            findings.append(
                CriticFinding(
                    severity="high",
                    category="evidence_gap",
                    message="후보 우선순위를 신뢰도 높게 판단하기에는 근거 수가 부족합니다.",
                )
            )

        for candidate in candidates:
            if candidate.overall_score < 60:
                findings.append(
                    CriticFinding(
                        severity="medium",
                        category="candidate_confidence",
                        message=f"{candidate.name}의 신뢰도 점수가 낮아 탐색적 가설로만 해석해야 합니다.",
                        evidence_ids=candidate.evidence_ids,
                    )
                )
            if "reference" in candidate.candidate_type:
                findings.append(
                    CriticFinding(
                        severity="low",
                        category="novelty",
                        message=f"{candidate.name}은 비교 기준으로는 유용하지만 새로운 재창출 주장으로는 차별성이 약합니다.",
                        evidence_ids=candidate.evidence_ids,
                    )
                )
            if "literature-derived" in candidate.candidate_type:
                findings.append(
                    CriticFinding(
                        severity="medium",
                        category="candidate_confidence",
                        message=(
                            f"{candidate.name}은(는) PubMed 문헌에서 자동 추출된 후보입니다. "
                            "약물명/약물군 혼동, 기존 표준치료와 재창출 가설의 구분, 적응증 외삽 가능성을 추가 검증해야 합니다."
                        ),
                        evidence_ids=candidate.evidence_ids,
                    )
                )

        for warning in citation_warnings:
            findings.append(
                CriticFinding(
                    severity="high",
                    category="citation",
                    message=warning,
                )
            )

        if not clinical_drafts:
            findings.append(
                CriticFinding(
                    severity="medium",
                    category="clinical_design",
                    message="임상 설계 초안이 생성되지 않아 endpoint와 대상 환자군 검토가 불완전합니다.",
                )
            )

        return findings, AgentTrace(
            agent=self.name,
            status="complete",
            summary="Reviewed evidence gaps, novelty, citation integrity, and clinical design readiness.",
            metadata={"finding_count": len(findings)},
        )
