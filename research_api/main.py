from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .models import (
    AnalyzeCaseResponse,
    CaseBriefRequest,
    CaseBriefResponse,
    CaseDetail,
    HealthResponse,
    PrecedentRequest,
    PrecedentResponse,
)
from . import service


def create_app() -> FastAPI:
    app = FastAPI(
        title="Legal Research Agent API",
        version="0.1.0",
        description="Simple FastAPI backend exposing the research agent to the Next.js frontend.",
    )

    allowed_origins = os.environ.get("RESEARCH_API_CORS", "*")
    origins = (
        ["*"]
        if allowed_origins.strip() == "*"
        else [origin.strip() for origin in allowed_origins.split(",") if origin.strip()]
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", response_model=HealthResponse)
    def healthcheck() -> HealthResponse:
        return HealthResponse()

    @app.post("/api/research/brief", response_model=CaseBriefResponse)
    def submit_case_brief(payload: CaseBriefRequest) -> CaseBriefResponse:
        try:
            cases = service.list_cases(payload.limit)
            summary = service.verdict_summary()
            anti_arguments = service.generate_anti_arguments(payload.case_input)
        except FileNotFoundError as exc:  # pragma: no cover - infrastructure guard
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        return CaseBriefResponse(
            cases=cases,
            verdictSummary=summary,
            antiArguments=anti_arguments,
            source=str(service.RESULTS_PATH),
        )

    @app.get("/api/research/cases/{doc_id}", response_model=CaseDetail)
    def fetch_case_detail(doc_id: str) -> CaseDetail:
        try:
            return service.case_detail(doc_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/research/cases/{doc_id}/analyze", response_model=AnalyzeCaseResponse)
    def analyze_case(doc_id: str) -> AnalyzeCaseResponse:  # noqa: ARG001
        return service.simulate_case_analysis()

    @app.post("/api/research/precedent", response_model=PrecedentResponse)
    def run_precedent_query(payload: PrecedentRequest) -> PrecedentResponse:
        try:
            return service.run_precedent_rag(
                prompt=payload.prompt,
                top_k=payload.top_k,
                collection_name=payload.collection_name,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        except Exception as exc:  # pragma: no cover - fallback
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    return app


app = create_app()


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run("research_api.main:app", host="0.0.0.0", port=int(os.environ.get("PORT", "8000")), reload=True)
