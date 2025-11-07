from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from strategist_workflow import (
    DEFAULT_CASE_FACTS,
    DEFAULT_MODEL,
    build_llm,
    build_orchestrator,
)


def load_case_facts(facts: str | None, facts_file: str | None) -> str:
    if facts and facts_file:
        raise ValueError("Provide either --facts or --facts-file, not both.")
    if facts_file:
        path = Path(facts_file)
        if not path.is_file():
            raise FileNotFoundError(f"No such facts file: {path}")
        return path.read_text(encoding="utf-8").strip()
    if facts:
        return facts.strip()
    return DEFAULT_CASE_FACTS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the legal strategy workflow using Gemini via LangGraph."
    )
    parser.add_argument("--facts", help="Plain text description of the case facts.")
    parser.add_argument("--facts-file", help="Path to a file containing the case facts.")
    parser.add_argument(
        "--api-key",
        help="Gemini API key; overrides the GOOGLE_API_KEY environment variable.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Gemini model name to use.",
    )
    parser.add_argument(
        "--show-blueprint",
        action="store_true",
        help="Print the agent execution blueprint for orchestration planning.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    try:
        case_input = load_case_facts(args.facts, args.facts_file)
    except (ValueError, FileNotFoundError) as exc:
        print(f"Error loading facts: {exc}", file=sys.stderr)
        sys.exit(2)

    try:
        llm = build_llm(args.api_key, args.model)
    except RuntimeError as exc:
        print(f"{exc}", file=sys.stderr)
        sys.exit(1)

    orchestrator = build_orchestrator(llm=llm)

    if args.show_blueprint:
        print(json.dumps(orchestrator.blueprint(), indent=2))

    final_state = orchestrator.run({"case_input": case_input})

    print("=== Legal Strategy Workflow Output ===")
    print("\n--- Research Materials ---")
    print(final_state.get("research_materials", "").strip())
    output_text = []
    output_text.append("=== Legal Strategy Workflow Output ===")
    output_text.append("\n--- Research Materials ---")
    output_text.append(final_state.get("research_materials", "").strip())
    final_output = "\n".join(output_text).strip()
    # print to terminal
    print(final_output)
    # also write to file
    out_path = Path("./output.txt")
    out_path.write_text(final_output + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
