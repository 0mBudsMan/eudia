from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

VerdictType = Literal["in-favor", "against", "neutral"]


class Verdict(BaseModel):
    type: VerdictType
    label: str


class ResearchCase(BaseModel):
    id: str
    caseNumber: str
    title: str
    year: int
    court: str
    verdict: Verdict | None = None
    isAnalyzed: bool = False
    analysisSummary: str | None = None


class CaseBriefRequest(BaseModel):
    case_input: str = Field(..., min_length=10, description="Plain text description of the dispute")
    limit: int = Field(
        15,
        ge=1,
        le=50,
        description="Maximum number of cases to return from the analysis dataset",
    )


class CaseBriefResponse(BaseModel):
    cases: list[ResearchCase]
    verdictSummary: dict[str, int]
    antiArguments: str | None = None
    source: str


class CaseDetail(BaseModel):
    id: str
    caseNumber: str
    title: str
    year: int
    court: str
    judges: list[str]
    verdict: Verdict | None = None
    summary: str
    keyPoints: list[str]
    citations: list[str]
    relevanceScore: float
    excerpt: str | None = None


class AnalyzeCaseResponse(BaseModel):
    verdict: Verdict
    reasoning: str


class HealthResponse(BaseModel):
    status: str = "ok"
