from __future__ import annotations

from app.models.schemas import AgentTrace, DiseaseProfile, NormalizedDisease
from app.services.demo_data import DEMO_DISEASES


class DiseaseAnalystAgent:
    name = "Disease Analyst Agent"

    async def run(self, disease: NormalizedDisease) -> tuple[DiseaseProfile, AgentTrace]:
        demo = DEMO_DISEASES.get(disease.canonical_name.lower())

        if demo:
            profile = DiseaseProfile(
                disease=disease,
                unmet_need=str(demo["unmet_need"]),
                mechanisms=list(demo["mechanisms"]),
                targets=list(demo["targets"]),
                biomarkers=list(demo["biomarkers"]),
                patient_subgroups=list(demo["patient_subgroups"]),
            )
            return profile, AgentTrace(
                agent=self.name,
                status="complete",
                summary=f"Resolved disease biology for {disease.canonical_name}.",
                metadata={"targets": len(profile.targets), "biomarkers": len(profile.biomarkers)},
            )

        profile = DiseaseProfile(
            disease=disease,
            unmet_need="External disease profile lookup is required before reliable hypothesis generation.",
            mechanisms=[],
            targets=[],
            biomarkers=[],
            patient_subgroups=[],
        )
        return profile, AgentTrace(
            agent=self.name,
            status="needs_data",
            summary="No cached disease profile found. External normalization and evidence retrieval are required.",
            metadata={"needs_external_lookup": True},
        )
