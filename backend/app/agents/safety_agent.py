from __future__ import annotations

from app.models.schemas import AgentTrace, DrugCandidate


class SafetyFeasibilityAgent:
    name = "Safety and Feasibility Agent"

    async def run(self, candidates: list[DrugCandidate]) -> tuple[list[DrugCandidate], AgentTrace]:
        for candidate in candidates:
            chemistry = candidate.chemistry
            molecular_weight = float(chemistry.get("molecular_weight", 0))
            logp = float(chemistry.get("logp", 0))
            hbd = int(chemistry.get("hbd", 0))
            hba = int(chemistry.get("hba", 0))

            rule_flags: list[str] = []
            if molecular_weight > 500:
                rule_flags.append("분자량이 Lipinski 기준보다 큽니다")
            if logp > 5:
                rule_flags.append("logP가 Lipinski 기준보다 큽니다")
            if hbd > 5:
                rule_flags.append("수소결합 공여체 수가 Lipinski 기준보다 많습니다")
            if hba > 10:
                rule_flags.append("수소결합 수용체 수가 Lipinski 기준보다 많습니다")

            if rule_flags:
                candidate.warnings.extend(rule_flags)
            candidate.feasibility_notes.append("공개 라벨, 금기사항, 이상반응 검토가 필요합니다.")
            candidate.feasibility_notes.append("기초 물성 값은 1차 실현 가능성 신호이며, 완전한 ADMET 입증은 아닙니다.")

        return candidates, AgentTrace(
            agent=self.name,
            status="complete",
            summary="Added first-pass safety and chemistry feasibility notes.",
            metadata={"reviewed_candidates": len(candidates)},
        )
