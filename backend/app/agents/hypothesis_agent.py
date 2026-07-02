from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass

from app.models.schemas import AgentTrace, DiseaseProfile, DrugCandidate, EvidenceItem
from app.services.demo_data import DEMO_DISEASES


@dataclass(slots=True)
class CandidateMention:
    name: str
    evidence_ids: set[str]
    contexts: list[str]
    confidence_total: float = 0.0
    mention_count: int = 0


class RepurposingHypothesisAgent:
    name = "Repurposing Hypothesis Agent"
    max_literature_candidates = 5

    blocked_terms = {
        "adolescent",
        "adult",
        "aged",
        "analgesics",
        "animals",
        "biomarkers",
        "case reports",
        "child",
        "clinical trial",
        "controlled clinical trial",
        "drug therapy",
        "female",
        "humans",
        "male",
        "middle aged",
        "migraine",
        "patients",
        "placebo",
        "placebos",
        "review",
        "tablets",
        "treatment",
        "young adult",
    }
    broad_class_terms = (
        "agents",
        "agonists",
        "analgesics",
        "antagonists",
        "antibodies",
        "anti-inflammatory agents",
        "benzenesulfonamides",
        "enzymes",
        "inhibitors",
        "non-steroidal anti-inflammatory agents",
        "peptides",
        "piperidines",
        "pyridines",
        "receptors",
        "tablets",
        "tryptamines",
        "oxazolidinones",
    )

    treatment_patterns = (
        re.compile(r"\b[A-Z][A-Za-z-]*(?:mab|nib|parib|tinib|zumab|ximab|umab|cept|vir|statin|triptan|gepant|ditan)\b"),
        re.compile(r"\b(?:[A-Z][A-Za-z]+(?:ine|one|olol|azole|afil|pril|sartan|xaban|gliflozin|cycline|mycin|platin|toxina?))\b"),
        re.compile(r"\b(?:topiramate|propranolol|amitriptyline|valproate|erenumab|fremanezumab|galcanezumab|eptinezumab|rimegepant|ubrogepant|atogepant|lasmiditan|sumatriptan|rizatriptan|zolmitriptan|botulinum toxin|onabotulinumtoxina)\b", re.IGNORECASE),
    )

    async def run(
        self,
        profile: DiseaseProfile,
        evidence: list[EvidenceItem],
    ) -> tuple[list[DrugCandidate], AgentTrace]:
        demo = DEMO_DISEASES.get(profile.disease.canonical_name.lower())
        if not demo:
            candidates = self._build_literature_candidates(profile, evidence)
            if candidates:
                return candidates, AgentTrace(
                    agent=self.name,
                    status="complete",
                    summary="Generated literature-derived repurposing hypotheses from retrieved evidence.",
                    metadata={
                        "candidate_count": len(candidates),
                        "evidence_count": len(evidence),
                        "generation_mode": "literature_heuristic",
                    },
                )

            return [], AgentTrace(
                agent=self.name,
                status="needs_data",
                summary="No candidate seeds or literature-derived drug mentions are available for this disease yet.",
                metadata={"candidate_count": 0, "evidence_count": len(evidence)},
            )

        candidates: list[DrugCandidate] = []
        for seed in demo["candidate_seeds"]:
            chemistry = dict(seed["chemistry"])
            chemistry["feasibility"] = seed["feasibility"]
            chemistry["novelty"] = seed["novelty"]
            chemistry["safety_risk"] = seed["safety_risk"]

            candidates.append(
                DrugCandidate(
                    name=str(seed["name"]),
                    rationale=str(seed["rationale"]),
                    mechanism=str(seed["mechanism"]),
                    candidate_type=str(seed["candidate_type"]),
                    evidence_ids=list(seed["evidence_ids"]),
                    targets=list(seed["targets"]),
                    safety_summary=str(seed["safety_summary"]),
                    chemistry=chemistry,
                )
            )

        return candidates, AgentTrace(
            agent=self.name,
            status="complete",
            summary="Generated mechanism-backed repurposing hypotheses from cached evidence.",
            metadata={"candidate_count": len(candidates), "evidence_count": len(evidence)},
        )

    def _build_literature_candidates(
        self,
        profile: DiseaseProfile,
        evidence: list[EvidenceItem],
    ) -> list[DrugCandidate]:
        mentions: dict[str, CandidateMention] = {}

        for item in evidence:
            names = [*item.drugs, *self._extract_treatment_terms(item)]
            for raw_name in names:
                name = self._normalize_candidate_name(raw_name)
                if not self._is_candidate_name(name, profile):
                    continue

                key = name.lower()
                if key not in mentions:
                    mentions[key] = CandidateMention(name=name, evidence_ids=set(), contexts=[])

                mention = mentions[key]
                mention.evidence_ids.add(item.id)
                mention.mention_count += 1
                mention.confidence_total += item.confidence
                if len(mention.contexts) < 2:
                    mention.contexts.append(self._context_for(item))

        ranked = sorted(
            mentions.values(),
            key=lambda item: (
                self._specificity_score(item.name),
                len(item.evidence_ids),
                item.confidence_total / max(item.mention_count, 1),
                item.mention_count,
            ),
            reverse=True,
        )

        candidates: list[DrugCandidate] = []
        for mention in ranked[: self.max_literature_candidates]:
            linked_ids = sorted(mention.evidence_ids)
            avg_confidence = mention.confidence_total / max(mention.mention_count, 1)
            targets = self._targets_for(linked_ids, evidence)
            candidates.append(
                DrugCandidate(
                    name=mention.name,
                    rationale=self._rationale(profile, mention, avg_confidence),
                    mechanism=self._mechanism_hint(mention.name, mention.contexts),
                    candidate_type="literature-derived repurposing hypothesis",
                    evidence_ids=linked_ids,
                    targets=targets,
                    safety_summary=(
                        "문헌 기반 후보이므로 실제 적응증, 용량, 금기, 병용 약물, 이상반응은 openFDA/PubChem/ChEMBL 연동으로 추가 검증해야 합니다."
                    ),
                    chemistry={
                        "molecular_weight": 0,
                        "logp": 0,
                        "hbd": 0,
                        "hba": 0,
                        "feasibility": min(0.9, 0.48 + len(linked_ids) * 0.07 + avg_confidence * 0.12),
                        "novelty": 0.58 if len(linked_ids) <= 2 else 0.48,
                        "safety_risk": 0.5,
                    },
                )
            )

        return candidates

    def _extract_treatment_terms(self, item: EvidenceItem) -> list[str]:
        text = f"{item.title} {item.summary}"
        candidates: list[str] = []
        for pattern in self.treatment_patterns:
            candidates.extend(match.group(0) for match in pattern.finditer(text))

        title_candidates = re.findall(
            r"\b([A-Z][A-Za-z]+(?: [A-Z][A-Za-z]+){0,2})[- ](?:therapy|treatment|prophylaxis|prevention)\b",
            item.title,
        )
        candidates.extend(title_candidates)
        return candidates

    def _normalize_candidate_name(self, value: str) -> str:
        cleaned = re.sub(r"\s+", " ", value.replace("\u00ae", "").replace("\u2122", "")).strip(" .,:;()[]")
        lower = cleaned.lower()

        special = {
            "onabotulinumtoxina": "OnabotulinumtoxinA",
            "botulinum toxin": "Botulinum toxin",
        }
        if lower in special:
            return special[lower]

        if cleaned.isupper() or cleaned.islower():
            return cleaned[:1].upper() + cleaned[1:].lower()
        return cleaned

    def _is_candidate_name(self, name: str, profile: DiseaseProfile) -> bool:
        if len(name) < 4 or len(name) > 80:
            return False
        lowered = name.lower()
        disease_terms = {profile.disease.canonical_name.lower(), *(item.lower() for item in profile.disease.synonyms)}
        if lowered in self.blocked_terms or lowered in disease_terms:
            return False
        normalized_label = re.sub(r"[^a-z0-9]+", " ", lowered).strip()
        if any(self._broad_term_matches(normalized_label, term) for term in self.broad_class_terms):
            return False
        if any(blocked in lowered for blocked in ("study", "trial", "patient", "disease", "therapy", "review")):
            return False
        if lowered.startswith(("anti-", "non-", "pre-")) and len(name.split()) > 3:
            return False
        return any(char.isalpha() for char in name)

    def _broad_term_matches(self, normalized_label: str, broad_term: str) -> bool:
        normalized_term = re.sub(r"[^a-z0-9]+", " ", broad_term.lower()).strip()
        return (
            normalized_label == normalized_term
            or normalized_label.endswith(f" {normalized_term}")
            or normalized_term in normalized_label
        )

    def _specificity_score(self, name: str) -> int:
        lowered = name.lower()
        if any(term in lowered for term in self.broad_class_terms):
            return 0
        if re.search(r"(mab|nib|parib|tinib|zumab|ximab|umab|cept|vir|statin|triptan|gepant|ditan)$", lowered):
            return 3
        if re.search(r"(ine|one|olol|azole|afil|pril|sartan|xaban|gliflozin|cycline|mycin|platin)$", lowered):
            return 2
        return 1

    def _context_for(self, item: EvidenceItem) -> str:
        summary = item.summary[:240]
        return f"{item.title}: {summary}" if summary else item.title

    def _targets_for(self, evidence_ids: list[str], evidence: list[EvidenceItem]) -> list[str]:
        counts: Counter[str] = Counter()
        evidence_by_id = {item.id: item for item in evidence}
        for evidence_id in evidence_ids:
            item = evidence_by_id.get(evidence_id)
            if not item:
                continue
            for target in item.targets:
                if target and target.lower() not in self.blocked_terms:
                    counts[target] += 1
        return [target for target, _ in counts.most_common(5)]

    def _rationale(self, profile: DiseaseProfile, mention: CandidateMention, avg_confidence: float) -> str:
        disease = profile.disease.canonical_name
        evidence_count = len(mention.evidence_ids)
        confidence_pct = round(avg_confidence * 100)
        return (
            f"PubMed 근거 {evidence_count}건에서 {mention.name}이(가) {disease} 치료, 예방, 임상시험 또는 약물치료 문맥으로 확인되었습니다. "
            f"평균 근거 신뢰도는 약 {confidence_pct}%이며, 현재 단계에서는 확정적 효능이 아니라 재창출 검토 후보로 해석해야 합니다."
        )

    def _mechanism_hint(self, name: str, contexts: list[str]) -> str:
        text = f"{name} {' '.join(contexts)}".lower()
        if "cgrp" in text or "calcitonin gene-related peptide" in text:
            return "CGRP 경로 조절 또는 관련 신경염증/혈관 반응 조절 가능성"
        if "triptan" in text or "sumatriptan" in text or "rizatriptan" in text or "zolmitriptan" in text:
            return "세로토닌 5-HT 수용체 관련 급성 증상 조절 가능성"
        if "botulinum" in text or "toxina" in text:
            return "신경전달물질 방출 조절 및 말초/중추 감작 완화 가능성"
        if "mab" in name.lower() or "antibody" in text:
            return "표적 단백질 또는 리간드 차단을 통한 생물학적 경로 조절 가능성"
        if "gep" in name.lower() or "gepant" in text:
            return "수용체 길항 또는 신호전달 차단을 통한 증상/예방 조절 가능성"
        return "문헌에서 반복 확인된 약물치료 문맥을 바탕으로 한 기전 탐색형 후보"
