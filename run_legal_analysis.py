#!/usr/bin/env python3
"""
Legal Case Analysis Script
Uses the enhanced embedding.py functionality
"""

import sys
import os

# Add the strategist_workflow directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "strategist_workflow"))

from embedding import analyze_legal_cases, save_analysis_results


def main():
    """Run legal case analysis."""

    print("🏛️  LEGAL CASE ANALYZER")
    print("=" * 50)

    # Configuration - customize these as needed
    USER_QUERY = """Client is a regional medical device supplier being sued for delayed delivery of
critical hospital equipment. The plaintiff alleges breach of contract and seeks
reimbursement for expedited replacements, lost revenue during the delay period,
and reputational harm with partner hospitals. Jurisdiction is Illinois federal
court; the supply agreement contains limitation-of-liability and force majeure
clauses.
"""
    USER_CONTEXT = """
Client is a regional medical device supplier being sued for delayed delivery of
critical hospital equipment. The plaintiff alleges breach of contract and seeks
reimbursement for expedited replacements, lost revenue during the delay period,
and reputational harm with partner hospitals. Jurisdiction is Illinois federal
court; the supply agreement contains limitation-of-liability and force majeure
clauses."""
    JSON_FILE = "output.json"
    OUTPUT_FILE = "legal_analysis_results.json"
    TOP_CASES = 10

    print(f"📋 Query: {USER_QUERY}")
    print(f"👤 Context: {USER_CONTEXT}")
    print(f"📁 Input: {JSON_FILE}")
    print(f"📁 Output: {OUTPUT_FILE}")
    print(f"🔢 Top cases: {TOP_CASES}")
    print()

    try:
        # Run complete analysis
        results = analyze_legal_cases(
            json_file_path=JSON_FILE,
            user_query=USER_QUERY,
            user_context=USER_CONTEXT,
            top_k=TOP_CASES,
        )

        # Save results
        save_analysis_results(results, OUTPUT_FILE)

        # Display summary
        print("\n" + "=" * 80)
        print("🎉 ANALYSIS COMPLETED!")
        print("=" * 80)
        print(f"📊 Total cases analyzed: {results['total_cases_analyzed']}")
        print(f"🏆 Wins: {results['verdict_summary']['wins']}")
        print(f"❌ Losses: {results['verdict_summary']['losses']}")
        print(f"❓ Unclear: {results['verdict_summary']['unclear']}")
        print(f"📁 Results saved to: {OUTPUT_FILE}")

        print(f"\n📋 TOP 3 CASES:")
        print("-" * 60)
        for case in results["cases"][:3]:
            verdict_emoji = (
                "🏆"
                if case["verdict"] == "WIN"
                else "❌" if case["verdict"] == "LOSS" else "❓"
            )
            print(f"{verdict_emoji} {case['title'][:50]}...")
            print(
                f"   Court: {case['court']} | Date: {case['date']} | Verdict: {case['verdict']}"
            )

            # Show user party identification if available
            if (
                "user_party_identified" in case
                and case["user_party_identified"] != "Unknown"
            ):
                print(f"   User represents: {case['user_party_identified']}")

            print()

        if results["total_cases_analyzed"] > 3:
            print(
                f"... and {results['total_cases_analyzed'] - 3} more cases (see {OUTPUT_FILE} for details)"
            )

    except Exception as e:
        print(f"\n❌ Error occurred: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
