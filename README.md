# 메디브릿지

메디브릿지는 근거 기반 약물 재창출 가설 생성과 초기 임상 가능성 검토를 지원하는 해커톤 MVP입니다.

The product direction is intentionally conservative: it is not a diagnostic, prescribing, or automated drug approval system. It is a research decision-support workflow that connects disease context, public evidence, existing drugs, safety signals, and a critic review into a traceable report.

## MVP Architecture

```text
frontend/ Next.js dashboard
backend/  FastAPI API plus modular agent pipeline
docs/     architecture and development plan
```

Runtime shape:

```text
Next.js Frontend
  -> FastAPI Backend
    -> Orchestrator Agent
      -> Disease Analyst Agent
      -> Evidence Retrieval Agent
        -> PubMed Provider
        -> ScienceON Korean Paper Provider
        -> Evidence Merger
      -> Repurposing Hypothesis Agent
      -> Approval Status Agent
      -> Safety and Feasibility Agent
      -> Clinical Design Agent
      -> Critic Agent
    -> PostgreSQL + pgvector
    -> Public APIs: PubMed/NCBI, ScienceON, ClinicalTrials.gov, PubChem, ChEMBL, openFDA
```

## Current Development State

This first scaffold includes:

- A pure-Python agent pipeline that can run without external API keys.
- PubMed evidence retrieval with optional ScienceON domestic paper retrieval.
- Evidence provider merging with duplicate detection and cross-source confidence adjustment.
- Cache-first service interfaces for future PostgreSQL integration.
- Candidate scoring, citation validation, and critic review.
- A Next.js dashboard shell wired for `POST /analysis`.
- Database schema draft for PostgreSQL + pgvector.

## API Keys

Create `.env` from `.env.example`. ScienceON is optional; when the key is missing, the backend skips the domestic provider and continues with PubMed.

```powershell
NCBI_API_KEY=...
NCBI_EMAIL=...
SCIENCEON_API_KEY=...
SCIENCEON_API_URL=https://openapi.ndsl.kr/itemsearch.do
SCIENCEON_TICKET=ARTI
```

## Local Backend Smoke Test

Use the bundled Codex Python runtime if system Python is not installed:

```powershell
C:\Users\bumji\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest discover -s backend\tests
```

To run the FastAPI app after installing dependencies:

```powershell
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

## Local Frontend

After installing dependencies:

```powershell
cd frontend
pnpm install
pnpm dev
```

Open `http://localhost:3000`.
