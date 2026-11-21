from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.agents.orchestrator import MediBridgeOrchestrator
from app.models.schemas import AnalysisRequest, to_plain_dict
from app.services.job_store import JobStore


class AnalysisPayload(BaseModel):
    input_text: str = Field(..., min_length=2, max_length=200)
    mode: str = Field(default="demo")
    top_k: int = Field(default=5, ge=1, le=10)


LOCAL_FRONTEND_ORIGINS = ("http://localhost:3000", "http://127.0.0.1:3000")
LOCAL_CLIENTS = {"127.0.0.1", "::1"}


def require_local_client(request: Request) -> None:
    if request.client is None or request.client.host not in LOCAL_CLIENTS:
        raise HTTPException(status_code=403, detail="Analysis is available only to local clients.")
    origin = request.headers.get("origin")
    if origin is not None and origin not in LOCAL_FRONTEND_ORIGINS:
        raise HTTPException(status_code=403, detail="Analysis is unavailable from this origin.")


# HTTPX logs complete upstream request URLs at INFO, including API-key query parameters.
logging.getLogger("httpx").setLevel(logging.WARNING)

app = FastAPI(title="메디브릿지 API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=LOCAL_FRONTEND_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1"])
analysis = APIRouter(prefix="/analysis", dependencies=[Depends(require_local_client)])

orchestrator = MediBridgeOrchestrator()
jobs = JobStore()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "medibridge-api"}


@analysis.post("")
async def create_analysis(payload: AnalysisPayload) -> dict:
    request = AnalysisRequest(input_text=payload.input_text, mode=payload.mode, top_k=payload.top_k)
    result = await orchestrator.run(request)
    job = jobs.create(result.request_id)
    jobs.complete(job.id, to_plain_dict(result))
    return {"job_id": job.id, "status": "complete", "result": to_plain_dict(result)}


@analysis.post("/run")
async def run_analysis(payload: AnalysisPayload) -> dict:
    request = AnalysisRequest(input_text=payload.input_text, mode=payload.mode, top_k=payload.top_k)
    result = await orchestrator.run(request)
    return to_plain_dict(result)


@analysis.get("/{job_id}")
async def get_analysis(job_id: str) -> dict:
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="analysis job not found")
    return to_plain_dict(job)


app.include_router(analysis)
