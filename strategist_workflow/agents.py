from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, Sequence, TypedDict
import json
import os
import re
import tempfile
import logging

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from bs4 import BeautifulSoup

# Import the Indian Kanoon API components
from .ikanoon import IKApi, FileStorage, setup_logging
import argparse

logger = logging.getLogger(__name__)


def _int_from_env(var_name: str, default: int) -> int:
    value = os.environ.get(var_name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        logger.warning(
            "Invalid integer for environment variable %s=%s. Using default %s.",
            var_name,
            value,
            default,
        )
        return default


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ANALYSIS_RESULTS_PATH = PROJECT_ROOT / "legal_analysis_results.json"
DEFAULT_IK_TOKEN = "cda8b7c3af63ed9d26de627153494d8330737065"
MAX_LOSS_CASES = _int_from_env("LOSS_CASE_AGENT_MAX_CASES", 3)
MAX_CASE_SNIPPET_CHARS = _int_from_env("LOSS_CASE_AGENT_MAX_CHARS", 4000)

AgentResponseAdapter = Callable[[str], Dict[str, str]]


def get_analysis_results_path() -> Path:
    override = os.environ.get("LEGAL_ANALYSIS_RESULTS_FILE")
    if override:
        return Path(override).expanduser()
    return DEFAULT_ANALYSIS_RESULTS_PATH


def get_indian_kanoon_token() -> str:
    token = os.environ.get("INDIAN_KANOON_TOKEN", DEFAULT_IK_TOKEN)
    if not token:
        raise ValueError(
            "INDIAN_KANOON_TOKEN environment variable not set and no default provided"
        )
    return token


def build_ikapi_client(api_token: str, datadir: str, max_pages: int = 5) -> IKApi:
    args = argparse.Namespace(
        token=api_token,
        datadir=datadir,
        maxcites=5,
        maxcitedby=5,
        orig=False,
        maxpages=max_pages,
        pathbysrc=False,
        numworkers=5,
        addedtoday=False,
        fromdate=None,
        todate=None,
        sortby="mostrecent",
    )
    setup_logging("info")
    filestorage = FileStorage(datadir)
    return IKApi(args, filestorage)


def clean_case_text(html: str, max_chars: int = MAX_CASE_SNIPPET_CHARS) -> str:
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()
    if max_chars and len(text) > max_chars:
        return text[:max_chars] + "..."
    return text


def collect_loss_case_documents(
    results_path: Path | None = None,
    max_cases: int = MAX_LOSS_CASES,
    max_chars: int = MAX_CASE_SNIPPET_CHARS,
) -> list[dict[str, object]]:
    path = (results_path or get_analysis_results_path()).expanduser()
    if not path.is_file():
        logger.warning("Legal analysis results file not found: %s", path)
        return []

    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        logger.error("Unable to read %s: %s", path, exc)
        return []

    cases = data.get("cases", [])
    loss_cases = [
        case
        for case in cases
        if str(case.get("verdict", "")).strip().upper() == "LOSS"
    ]

    if not loss_cases:
        logger.info("No LOSS verdicts found in %s", path)
        return []

    token = get_indian_kanoon_token()
    documents: list[dict[str, object]] = []
    limit = max_cases if max_cases > 0 else len(loss_cases)

    with tempfile.TemporaryDirectory() as temp_dir:
        ikapi = build_ikapi_client(token, temp_dir)
        for case in loss_cases[:limit]:
            doc_id_value = case.get("doc_id") or case.get("docid")
            try:
                doc_id = int(doc_id_value)
            except (TypeError, ValueError):
                logger.warning("Skipping case with invalid doc_id: %s", doc_id_value)
                continue

            try:
                doc_payload = json.loads(ikapi.fetch_doc(doc_id))
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Failed to fetch doc %s: %s", doc_id, exc)
                continue

            if "errmsg" in doc_payload:
                logger.warning("Indian Kanoon error for doc %s: %s", doc_id, doc_payload)
                continue

            excerpt = clean_case_text(doc_payload.get("doc", ""), max_chars=max_chars)
            documents.append(
                {
                    "doc_id": doc_id,
                    "title": case.get("title", ""),
                    "court": case.get("court", ""),
                    "date": case.get("date", ""),
                    "verdict": case.get("verdict", ""),
                    "analysis_summary": case.get("analysis_summary", ""),
                    "excerpt": excerpt,
                    "source_url": f"https://indiankanoon.org/doc/{doc_id}/",
                }
            )

    return documents


class WorkflowState(TypedDict, total=False):
    case_input: str
    search_queries: str  # New: Generated search queries
    ik_search_results: str  # New: Aggregated Indian Kanoon results
    loss_case_documents: str
    anti_arguments: str
    research_materials: str
    precedent_insights: str
    predictive_metrics: str
    strategy_recommendation: str


@dataclass(frozen=True)
class AgentConfig:
    """Declarative configuration describing an agent's contract."""

    name: str
    requires: Sequence[str]
    provides: Sequence[str]
    description: str
    prompt_messages: Sequence[tuple[str, str]]
    response_adapter: AgentResponseAdapter | None = None
    metadata: Dict[str, str] = field(default_factory=dict)

    def build_prompt(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages(list(self.prompt_messages))


class LLMWorkflowAgent:
    """Runtime wrapper that turns an AgentConfig into a LangChain runnable."""

    def __init__(self, llm, config: AgentConfig):
        self.llm = llm
        self.config = config
        self.is_llm_agent = len(config.prompt_messages) > 0

        if self.is_llm_agent:
            self.prompt = config.build_prompt()
            self.chain = self.prompt | llm | StrOutputParser()
        else:
            self.prompt = None
            self.chain = None

    def as_node(self):
        def node(state: WorkflowState) -> WorkflowState:
            payload = self._prepare_payload(state)

            # If this is a non-LLM agent, skip the chain and go straight to adapter
            if not self.is_llm_agent:
                # For non-LLM agents, pass the raw payload values
                # The adapter will handle the actual processing
                if len(self.config.requires) == 1:
                    response = payload[self.config.requires[0]]
                else:
                    response = json.dumps(payload)
            else:
                response = self.chain.invoke(payload)

            return self._format_response(response)

        return node

    def describe(self) -> Dict[str, object]:
        return {
            "name": self.config.name,
            "requires": tuple(self.config.requires),
            "provides": tuple(self.config.provides),
            "description": self.config.description,
            "metadata": self.config.metadata,
        }

    def _prepare_payload(self, state: WorkflowState) -> Dict[str, str]:
        missing = [key for key in self.config.requires if key not in state]
        if missing:
            raise KeyError(
                f"{self.config.name} missing required inputs: {', '.join(missing)}"
            )
        return {key: state[key] for key in self.config.requires}

    def _format_response(self, raw: str) -> WorkflowState:
        adapter = self.config.response_adapter or self._default_adapter
        return adapter(raw)

    def _default_adapter(self, text: str) -> WorkflowState:
        if not self.config.provides:
            return {}
        return {self.config.provides[0]: text.strip()}


def query_generator_adapter(text: str) -> WorkflowState:
    """Parse LLM output to extract search queries as a list."""
    print(text)
    queries = []
    for line in text.strip().split("\n"):
        line = line.strip()
        # Remove bullet points, numbers, and extra whitespace
        if line and not line.startswith("#"):
            # Clean up common prefixes
            line = line.lstrip("•-*0123456789.) ")
            if line:
                queries.append(line)

    return {"search_queries": json.dumps(queries, ensure_ascii=False)}


def loss_case_loader_adapter(_: str) -> WorkflowState:
    documents = collect_loss_case_documents()
    return {"loss_case_documents": json.dumps(documents, ensure_ascii=False)}


def fetch_indian_kanoon_cases(
    queries: list[str],
    api_token: str,
    target_total: int = 1,
    max_pages_per_query: int = 5,
) -> str:
    """
    Fetch cases from Indian Kanoon API based on search queries.

    Args:
        queries: List of search queries
        api_token: Indian Kanoon API token
        target_total: Target number of total cases to fetch
        max_pages_per_query: Maximum pages to fetch per query

    Returns:
        JSON string containing aggregated results
    """
    # Setup temporary directory for data
    with tempfile.TemporaryDirectory() as temp_dir:
        ikapi = build_ikapi_client(
            api_token=api_token, datadir=temp_dir, max_pages=max_pages_per_query
        )

        # Track results
        all_results = []
        total_fetched = 0

        # Calculate cases per query
        cases_per_query = target_total // len(queries) if queries else 0
        pages_per_query = min(max_pages_per_query, (cases_per_query // 10) + 1)

        for query in queries:
            if total_fetched >= target_total:
                break

            print(f"Searching Indian Kanoon for: {query}")

            pagenum = 0
            query_results = []

            while pagenum < pages_per_query * 10 and total_fetched < target_total:
                try:
                    # Search Indian Kanoon
                    results = ikapi.search(query, pagenum, 10)
                    obj = json.loads(results)
                    # print(obj)
                    if "errmsg" in obj:
                        print(f"Error for query '{query}': {obj['errmsg']}")
                        break

                    if "docs" not in obj or len(obj["docs"]) <= 0:
                        break

                    docs = obj["docs"]
                    # print(docs)
                    print(
                        f"Found {len(docs)} results for '{query}' (page {pagenum//10})"
                    )

                    for doc in docs:
                        if total_fetched >= target_total:
                            break

                        # Fetch full document details
                        doc_json = ikapi.fetch_doc(doc["tid"])
                        doc_data = json.loads(doc_json)
                        if "errmsg" not in doc_data:
                            query_results.append(
                                {
                                    "query": query,
                                    "docid": doc["tid"],
                                    "title": doc["title"],
                                    "court": doc["docsource"],
                                    "date": doc["publishdate"],
                                    "doc_data": doc_data,
                                }
                            )
                            print(total_fetched)
                            total_fetched += 1

                    pagenum += 10

                except Exception as e:
                    print(f"Error processing query '{query}': {e}")
                    break

            all_results.extend(query_results)
            print(f"Total cases fetched so far: {total_fetched}")

        # Aggregate results
        summary = {
            "total_cases": len(all_results),
            "queries_used": queries,
            "cases": all_results,
        }
        print("DONE")
        return json.dumps(summary, ensure_ascii=False, indent=2)


def ik_search_adapter(text: str) -> WorkflowState:
    """
    Adapter that executes Indian Kanoon search.
    Note: This adapter expects the API token to be available.
    """
    # Parse queries from the input
    queries = json.loads(text)

    # Get API token from environment variable
    api_token = get_indian_kanoon_token()

    # Fetch cases
    results = fetch_indian_kanoon_cases(
        queries=queries, api_token=api_token, target_total=200, max_pages_per_query=5
    )
    print(results)
    return {"ik_search_results": results}


def default_agent_configs() -> Sequence[AgentConfig]:
    return [
        # NEW AGENT: Query Generator
        AgentConfig(
            name="query_generator",
            requires=("case_input",),
            provides=("search_queries",),
            description=(
                "Generate targeted search queries for Indian Kanoon based on case facts. "
                "Produces 5-10 specific queries to maximize relevant case retrieval."
            ),
            prompt_messages=[
                (
                    "system",
                    (
                        "You are a Legal Query Generator for Indian Kanoon searches. "
                        "Based on the case description, generate 5-10 highly specific search queries "
                        "that will find the most relevant Indian legal precedents. "
                        "Each query should focus on: key legal issues, relevant statutes/acts, "
                        "jurisdiction, case types, and important legal principles.\n\n"
                        "Return ONLY the queries, one per line, seperated by bullets."
                        "It should be atmost 5-6 words with high impact."
                        "Queries should not be startin with double quotes, and there should not be double quotes anywhere"
                    ),
                ),
                (
                    "human",
                    (
                        "Case description:\n{case_input}\n\n"
                        "Generate 5-10 specific search queries for Indian Kanoon."
                    ),
                ),
            ],
            response_adapter=query_generator_adapter,
            metadata={"topic": "query-generation"},
        ),
        # NEW AGENT: Indian Kanoon Search
        AgentConfig(
            name="indian_kanoon_search",
            requires=("search_queries",),
            provides=("ik_search_results",),
            description=(
                "Execute searches on Indian Kanoon API and retrieve up to 10,000 cases. "
                "This is a non-LLM agent that directly calls the API."
            ),
            prompt_messages=[],  # No LLM needed for this agent
            response_adapter=ik_search_adapter,
            metadata={"topic": "api-search"},
        ),
        AgentConfig(
            name="loss_case_loader",
            requires=(),
            provides=("loss_case_documents",),
            description=(
                "Load previously analyzed LOSS verdicts from legal_analysis_results.json, "
                "fetch their full text from Indian Kanoon, and surface concise excerpts."
            ),
            prompt_messages=[],
            response_adapter=loss_case_loader_adapter,
            metadata={"topic": "loss-case-ingestion"},
        ),
        AgentConfig(
            name="anti_lawyer_strategist",
            requires=("case_input", "loss_case_documents"),
            provides=("anti_arguments",),
            description=(
                "Act as opposing counsel by mining LOSS cases for winning arguments that can be "
                "turned against the user's current case."
            ),
            prompt_messages=[
                (
                    "system",
                    (
                        "You are the Anti-Lawyer representing the party opposing the user. "
                        "Given the user's case narrative and JSON describing similar cases "
                        "where that side lost (including excerpts from the winning reasoning), "
                        "extract the most decisive arguments raised by the winning parties. "
                        "Explain how each argument can be deployed to undermine the user's position. "
                        "Always cite doc_id, court, and date for every argument."
                    ),
                ),
                (
                    "human",
                    (
                        "User case description:\n{case_input}\n\n"
                        "Loss case bundle (JSON):\n{loss_case_documents}\n\n"
                        "Produce a structured memo with 3-5 numbered arguments. "
                        "For each argument, provide:\n"
                        "1) Winning Argument (cite doc_id / court / date)\n"
                        "2) How it applies against the user\n"
                        "3) Practical leverage (remedies, damages, or procedural hooks).\n"
                        "Be direct, skeptical, and assume the user's defenses are weak."
                    ),
                ),
            ],
            metadata={"topic": "anti-lawyer-analysis"},
        ),
        # user query -> prompt to generate embeddings for semantic matching
    ]
