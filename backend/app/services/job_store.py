from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class AnalysisJob:
    id: str
    status: str
    progress: int = 0
    message: str = "queued"
    result: dict[str, Any] | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, AnalysisJob] = {}

    def create(self, job_id: str) -> AnalysisJob:
        job = AnalysisJob(id=job_id, status="queued")
        self._jobs[job_id] = job
        return job

    def complete(self, job_id: str, result: dict[str, Any]) -> AnalysisJob:
        job = self._jobs[job_id]
        job.status = "complete"
        job.progress = 100
        job.message = "analysis complete"
        job.result = result
        job.updated_at = datetime.now(timezone.utc).isoformat()
        return job

    def fail(self, job_id: str, message: str) -> AnalysisJob:
        job = self._jobs[job_id]
        job.status = "failed"
        job.message = message
        job.updated_at = datetime.now(timezone.utc).isoformat()
        return job

    def get(self, job_id: str) -> AnalysisJob | None:
        return self._jobs.get(job_id)
