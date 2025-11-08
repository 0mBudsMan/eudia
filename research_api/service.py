from __future__ import annotations

import glob
import json
import logging
import os
import random
from functools import lru_cache
from pathlib import Path
from bs4 import BeautifulSoup

from strategist_workflow.embedding import query_case_embeddings_db

from .models import (
    AnalyzeCaseResponse,
    CaseDetail,
    PrecedentChunk,
    PrecedentResponse,
    PrecedentSource,
    ResearchCase,
    Verdict,
)

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RESULTS_FILE = PROJECT_ROOT / "legal_analysis_results.json"
DEFAULT_CASES_DATA_DIR = PROJECT_ROOT / "cases_data"
DEFAULT_CHROMA_PATH = PROJECT_ROOT / "chroma_db"


def _env_path(var_name: str, default: Path) -> Path:
    override = os.environ.get(var_name)
    return Path(override).expanduser() if override else default


RESULTS_PATH = _env_path("LEGAL_ANALYSIS_RESULTS_FILE", DEFAULT_RESULTS_FILE)
CASES_DATA_DIR = _env_path("CASES_DATA_DIR", DEFAULT_CASES_DATA_DIR)
CHROMA_DB_PATH = _env_path("CHROMA_DB_PATH", DEFAULT_CHROMA_PATH)


def _clean_html(html: str, max_chars: int = 1500) -> str:
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    text = " ".join(text.split())
    if max_chars and len(text) > max_chars:
        return text[:max_chars] + "..."
    return text


def _safe_year(date_str: str | None) -> int:
    if not date_str:
        return 0
    try:
        return int(date_str.split("-")[0])
    except (ValueError, AttributeError):
        return 0


def _map_verdict(verdict_text: str | None) -> Verdict | None:
    if not verdict_text:
        return None
    label = verdict_text.strip().upper()
    if label == "WIN":
        return Verdict(type="in-favor", label="Win")
    if label == "LOSS":
        return Verdict(type="against", label="Loss")
    if label == "UNCLEAR":
        return Verdict(type="neutral", label="Unclear")
    return None


@lru_cache(maxsize=1)
def _load_results() -> dict:
    if not RESULTS_PATH.is_file():
        raise FileNotFoundError(
            f"legal_analysis_results.json not found at {RESULTS_PATH.resolve()}. "
            "Run the analysis pipeline or point LEGAL_ANALYSIS_RESULTS_FILE to a valid file."
        )
    with RESULTS_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def list_cases(limit: int) -> list[ResearchCase]:
    data = _load_results()
    cases = data.get("cases", [])[:limit]
    return [
        ResearchCase(
            id=str(case.get("doc_id") or case.get("docid")),
            caseNumber=str(case.get("doc_id") or case.get("docid")),
            title=case.get("title", "Unknown title"),
            year=_safe_year(case.get("date")),
            court=case.get("court", "Unknown court"),
            verdict=_map_verdict(case.get("verdict")),
            isAnalyzed=bool(_map_verdict(case.get("verdict"))),
            analysisSummary=(case.get("analysis_summary") or "")[:500],
        )
        for case in cases
    ]


def verdict_summary() -> dict[str, int]:
    data = _load_results()
    summary = data.get("verdict_summary", {})
    return {
        "wins": int(summary.get("wins", 0)),
        "losses": int(summary.get("losses", 0)),
        "unclear": int(summary.get("unclear", 0)),
    }


def _find_case(doc_id: str) -> dict:
    data = _load_results()
    for case in data.get("cases", []):
        case_id = str(case.get("doc_id") or case.get("docid"))
        if case_id == str(doc_id):
            return case
    raise ValueError(f"No case with doc_id {doc_id} in {RESULTS_PATH}")


def _extract_key_points(case: dict, max_points: int = 4) -> list[str]:
    reasoning = case.get("reasoning") or ""
    lines = [line.strip(" -*0123456789.") for line in reasoning.splitlines()]
    cleaned = [line for line in lines if line]
    if cleaned:
        return cleaned[:max_points]
    summary = case.get("analysis_summary") or ""
    if summary:
        return summary.split(". ")[:max_points]
    return ["Key points unavailable."]


def _find_case_document(doc_id: str) -> str | None:
    if not CASES_DATA_DIR.exists():
        return None
    pattern = str(CASES_DATA_DIR / "**" / f"{doc_id}.json")
    matches = glob.glob(pattern, recursive=True)
    if not matches:
        return None
    try:
        with open(matches[0], "r", encoding="utf-8") as f:
            obj = json.load(f)
    except OSError:
        return None
    return _clean_html(obj.get("doc", ""), 1800)


def case_detail(doc_id: str) -> CaseDetail:
    case = _find_case(doc_id)
    excerpt = _find_case_document(doc_id)
    return CaseDetail(
        id=str(case.get("doc_id") or doc_id),
        caseNumber=str(case.get("doc_id") or doc_id),
        title=case.get("title", "Unknown title"),
        year=_safe_year(case.get("date")),
        court=case.get("court", "Unknown court"),
        judges=[
            "Justice A. Rao",
            "Justice B. Mehta",
            "Justice C. Iyer",
        ],
        verdict=_map_verdict(case.get("verdict")),
        summary=case.get("analysis_summary", "Summary unavailable."),
        keyPoints=_extract_key_points(case),
        citations=[
            f"IK Doc {doc_id}",
            case.get("court", "Unknown court"),
            case.get("date", "Unknown date"),
        ],
        relevanceScore=0.8,
        excerpt=excerpt,
    )


def generate_anti_arguments(case_input: str, max_points: int = 3) -> str:
    data = _load_results()
    losses = [
        case
        for case in data.get("cases", [])
        if str(case.get("verdict", "")).upper() == "LOSS"
    ]
    if not losses:
        return "No loss cases available to extract counter arguments."
    bullets: list[str] = []
    for idx, case in enumerate(losses[:max_points], start=1):
        doc_id = case.get("doc_id")
        bullets.append(
            f"{idx}. Doc {doc_id} ({case.get('court')} - {case.get('date')}): "
            f"{case.get('analysis_summary', '').strip()[:280]} "
            f"→ Use this to challenge the user's narrative by stressing {case.get('user_party_identified', 'the opposing party')} exposure."
        )
    header = "Opposition talking points based on prior losses:\n"
    return header + "\n".join(bullets)


def run_precedent_rag(
    prompt: str,
    top_k: int = 5,
    collection_name: str | None = None,
) -> PrecedentResponse:
    question = (prompt or "").strip()
    if not question:
        raise ValueError("Prompt must not be empty.")

    collection = collection_name or os.environ.get("PRECEDENT_COLLECTION_NAME", "case_chunks")

    rag_result = query_case_embeddings_db(
        query=question,
        collection_name=collection,
        persist_directory=str(CHROMA_DB_PATH),
        top_k=top_k,
    )

    sources_summary = rag_result.get("sources_summary", {}) or {}
    sources = [
        PrecedentSource(
            case_id=str(case_id),
            chunks=[int(idx) for idx in sorted(indices)],
        )
        for case_id, indices in sources_summary.items()
    ]

    chunk_payload = []
    for chunk in rag_result.get("relevant_chunks", []):
        metadata = chunk.get("metadata") or {}
        chunk_payload.append(
            PrecedentChunk(
                text=chunk.get("text", ""),
                case_id=str(metadata.get("case_id", "")),
                chunk_index=int(metadata.get("chunk_index", -1)),
                similarity_score=float(chunk.get("similarity_score", 0.0)),
            )
        )

    stats = rag_result.get("collection_stats", {}) or {}

    return PrecedentResponse(
        answer=rag_result.get("answer") or "No answer generated (check GEMINI_API_KEY).",
        sources=sources,
        chunks=chunk_payload,
        collection=str(stats.get("name") or collection),
        total_chunks=stats.get("total_chunks"),
    )


def simulate_case_analysis() -> AnalyzeCaseResponse:
    choices = [
        Verdict(type="in-favor", label="In Favor"),
        Verdict(type="against", label="Against Us"),
        Verdict(type="neutral", label="Settled"),
    ]
    verdict = random.choice(choices)
    reasoning = (
        "Automated analysis suggests this precedent trends "
        f"{'toward claimant relief' if verdict.type == 'against' else 'toward defense success'}. "
        "Review procedural posture and damages discussion before citing."
    )
    return AnalyzeCaseResponse(verdict=verdict, reasoning=reasoning)
