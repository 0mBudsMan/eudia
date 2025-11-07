from __future__ import annotations

from typing import Iterable, Sequence

from langgraph.graph import END, StateGraph

from .agents import LLMWorkflowAgent, WorkflowState


class LegalWorkflowOrchestrator:
    """Coordinates agent execution and exposes metadata for orchestration tooling."""

    def __init__(self, agents: Sequence[LLMWorkflowAgent]):
        self.agents = list(agents)
        if not self.agents:
            raise ValueError("At least one agent is required to build the workflow.")
        self._graph = self._compile_graph()

    def _compile_graph(self):
        graph = StateGraph(WorkflowState)
        for agent in self.agents:
            graph.add_node(agent.config.name, agent.as_node())

        graph.set_entry_point(self.agents[0].config.name)
        for current, nxt in zip(self.agents, self.agents[1:]):
            graph.add_edge(current.config.name, nxt.config.name)
        graph.add_edge(self.agents[-1].config.name, END)
        return graph.compile()

    def run(self, initial_state: WorkflowState) -> WorkflowState:
        return self._graph.invoke(initial_state)

    def blueprint(self) -> list[dict[str, object]]:
        return [agent.describe() for agent in self.agents]

    def agent_names(self) -> Iterable[str]:
        return (agent.config.name for agent in self.agents)
