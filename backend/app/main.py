from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.agents.orchestrator import MediBridgeOrchestrator
from app.models.schemas import AnalysisRequest, to_plain_dict
from app.services.job_store import JobStore


class AnalysisPayload(BaseModel):
    input_text: str = Field(..., min_length=2, max_length=200)
    mode: str = Field(default="demo")
    top_k: int = Field(default=5, ge=1, le=10)


app = FastAPI(title="메디브릿지 API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = MediBridgeOrchestrator()
jobs = JobStore()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "medibridge-api"}


@app.post("/analysis")
async def create_analysis(payload: AnalysisPayload) -> dict:
    request = AnalysisRequest(input_text=payload.input_text, mode=payload.mode, top_k=payload.top_k)
    result = await orchestrator.run(request)
    job = jobs.create(result.request_id)
    jobs.complete(job.id, to_plain_dict(result))
    return {"job_id": job.id, "status": "complete", "result": to_plain_dict(result)}


@app.post("/analysis/run")
async def run_analysis(payload: AnalysisPayload) -> dict:
    request = AnalysisRequest(input_text=payload.input_text, mode=payload.mode, top_k=payload.top_k)
    result = await orchestrator.run(request)
    return to_plain_dict(result)


@app.get("/analysis/{job_id}")
async def get_analysis(job_id: str) -> dict:
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="analysis job not found")
    return to_plain_dict(job)
