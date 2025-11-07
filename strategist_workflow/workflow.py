from __future__ import annotations

from typing import Sequence

from .agents import AgentConfig, LLMWorkflowAgent, WorkflowState, default_agent_configs
from .orchestrator import LegalWorkflowOrchestrator


def build_agents(llm, configs: Sequence[AgentConfig] | None = None) -> list[LLMWorkflowAgent]:
    configs = list(configs or default_agent_configs())
    return [LLMWorkflowAgent(llm, config) for config in configs]


def build_orchestrator(
    llm,
    configs: Sequence[AgentConfig] | None = None,
) -> LegalWorkflowOrchestrator:
    agents = build_agents(llm, configs=configs)
    return LegalWorkflowOrchestrator(agents)
