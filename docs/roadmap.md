# Development Roadmap

## Week 1

- Confirm proposal structure and target disease demo cases.
- Build repository skeleton.
- Implement disease normalization, demo evidence, and base schemas.
- Validate key public API shapes.

## Week 2

- Implement FastAPI backend.
- Add PubMed, ClinicalTrials.gov, PubChem, ChEMBL, and openFDA adapters.
- Add PostgreSQL schema and cache-first evidence store.

## Week 3

- Implement LangGraph-based orchestration.
- Connect Orchestrator, Disease, Evidence, Hypothesis, Safety, Clinical, and Critic agents.
- Add job status and progress tracking.

## Week 4

- Implement scoring engine and citation validator.
- Add chemistry property review with optional RDKit integration.
- Add safety feasibility summary from public labels and adverse-event sources.

## Week 5

- Build Next.js dashboard.
- Add agent timeline, evidence map, candidate ranking, safety review, clinical draft, and critic report.
- Add demo cache mode for stable judging.

## Week 6

- Fix demo cases and evaluation set.
- Prepare gold-case validation table.
- Polish proposal, screenshots, and final demo script.
