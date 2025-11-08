from __future__ import annotations

from typing import Literal, Optional, List

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


class PrecedentRequest(BaseModel):
    prompt: str = Field(..., min_length=5, description="Question or case narrative to run against precedents")
    top_k: int = Field(5, ge=1, le=20, description="Number of RAG chunks to retrieve")
    collection_name: Optional[str] = Field(
        None,
        description="Optional Chroma collection override (defaults to PRECEDENT_COLLECTION_NAME or 'case_chunks')",
    )


class PrecedentSource(BaseModel):
    case_id: str
    chunks: List[int]


class PrecedentChunk(BaseModel):
    text: str
    case_id: str
    chunk_index: int
    similarity_score: float


class PrecedentResponse(BaseModel):
    answer: str
    sources: List[PrecedentSource]
    chunks: List[PrecedentChunk]
    collection: str
    total_chunks: Optional[int] = None
