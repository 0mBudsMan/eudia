#!/usr/bin/env python3
"""
Debug script to test verdict analysis
"""

import sys
import os

# Add the strategist_workflow directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "strategist_workflow"))

from embedding import (
    load_cases_from_json,
    create_legal_case_embeddings,
    query_case_embeddings_db,
)


def debug_verdict_analysis():
    """Debug the verdict analysis process."""

    print("🔍 DEBUGGING VERDICT ANALYSIS")
    print("=" * 50)

    # Load cases
    cases = load_cases_from_json("output.json")
    print(f"Loaded {len(cases)} cases")

    if not cases:
        print("❌ No cases found!")
        return

    # Get first case for testing
    first_case_id = list(cases.keys())[0]
    print(f"Testing with case: {first_case_id}")

    # Create embeddings
    print("\n🔧 Creating embeddings...")
    create_legal_case_embeddings(cases, "debug_collection")

    # Test the verdict query directly
    verdict_query = """
    Who won this case? What was the final judgment and ruling? 
    Which party prevailed and what was decided in favor of whom? 
    What was the court's decision regarding the plaintiff and defendant?
    What relief was granted or denied? Who was the successful party?
    """

    print(f"\n🔍 Testing verdict query for case {first_case_id}")
    print(f"Query: {verdict_query[:100]}...")

    # Query the specific case
    results = query_case_embeddings_db(
        verdict_query, "debug_collection", top_k=5, filter_case_ids=[first_case_id]
    )

    print(f"\n📊 Query Results:")
    print(f"- Found {len(results.get('relevant_chunks', []))} relevant chunks")

    # Print the analysis
    analysis = results.get("answer", "")
    print(f"\n📝 LLM Analysis:")
    print("-" * 60)
    print(analysis)
    print("-" * 60)

    # Test verdict extraction
    from embedding import extract_simple_verdict

    verdict = extract_simple_verdict(analysis)
    print(f"\n⚖️ Extracted Verdict: {verdict}")

    # Show some context from relevant chunks
    print(f"\n📚 Sample Context (first 2 chunks):")
    for i, chunk in enumerate(results.get("relevant_chunks", [])[:2]):
        print(f"\nChunk {i+1}:")
        print(f"- Similarity: {chunk['similarity_score']:.3f}")
        print(f"- Text: {chunk['text'][:300]}...")


if __name__ == "__main__":
    debug_verdict_analysis()
