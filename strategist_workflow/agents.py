from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Sequence, TypedDict
import json
import os
import tempfile
import logging

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

# Import the Indian Kanoon API components
from .ikanoon import IKApi, FileStorage, setup_logging
import argparse


AgentResponseAdapter = Callable[[str], Dict[str, str]]


class WorkflowState(TypedDict, total=False):
    case_input: str
    search_queries: str  # New: Generated search queries
    ik_search_results: str  # New: Aggregated Indian Kanoon results
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
    for line in text.strip().split('\n'):
        line = line.strip()
        # Remove bullet points, numbers, and extra whitespace
        if line and not line.startswith('#'):
            # Clean up common prefixes
            line = line.lstrip('•-*0123456789.) ')
            if line:
                queries.append(line)
    
    return {
        "search_queries": json.dumps(queries, ensure_ascii=False)
    }


def fetch_indian_kanoon_cases(
    queries: list[str], 
    api_token: str, 
    target_total: int = 1,
    max_pages_per_query: int = 5
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
        # Create args object for IKApi
        args = argparse.Namespace(
            token=api_token,
            datadir=temp_dir,
            maxcites=5,
            maxcitedby=5,
            orig=False,
            maxpages=max_pages_per_query,
            pathbysrc=False,
            numworkers=5,
            addedtoday=False,
            fromdate=None,
            todate=None,
            sortby='mostrecent'
        )
        
        # Setup logging
        setup_logging('info')
        
        # Initialize API
        filestorage = FileStorage(temp_dir)
        ikapi = IKApi(args, filestorage)
        
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
                    if 'errmsg' in obj:
                        print(f"Error for query '{query}': {obj['errmsg']}")
                        break
                    
                    if 'docs' not in obj or len(obj['docs']) <= 0:
                        break
                    
                    docs = obj['docs']
                    # print(docs)
                    print(f"Found {len(docs)} results for '{query}' (page {pagenum//10})")
                    
                    for doc in docs:
                        if total_fetched >= target_total:
                            break
                        
                        # Fetch full document details
                        doc_json = ikapi.fetch_doc(doc['tid'])
                        doc_data = json.loads(doc_json)
                        if 'errmsg' not in doc_data:
                            query_results.append({
                                'query': query,
                                'docid': doc['tid'],
                                'title': doc['title'],
                                'court': doc['docsource'],
                                'date': doc['publishdate'],
                                'doc_data': doc_data
                            })
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
            'total_cases': len(all_results),
            'queries_used': queries,
            'cases': all_results
        }
        print("DONE")
        return summary


def ik_search_adapter(text: str) -> WorkflowState:
    """
    Adapter that executes Indian Kanoon search.
    Note: This adapter expects the API token to be available.
    """
    # Parse queries from the input
    queries = json.loads(text)
    
    # Get API token from environment variable
    api_token = "cda8b7c3af63ed9d26de627153494d8330737065"
    if not api_token:
        raise ValueError("INDIAN_KANOON_TOKEN environment variable not set")
    
    # Fetch cases
    results = fetch_indian_kanoon_cases(
        queries=queries,
        api_token=api_token,
        target_total=1,
        max_pages_per_query=5
    )
    print(results)
    return {
        "ik_search_results": results,
        "research_materials": results,
    }


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
    ]
