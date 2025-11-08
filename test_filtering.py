#!/usr/bin/env python3
"""
Test script to verify the 300k character limit filtering
"""

import sys
import os
import json

# Add the strategist_workflow directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "strategist_workflow"))

from embedding import load_cases_from_json


def test_large_doc_filtering():
    """Test that documents larger than 300k characters are filtered out."""

    print("🧪 Testing 300k character limit filtering...")

    # Create a test JSON with a large document
    large_doc = "<html>" + "A" * 350000 + "</html>"  # 350k+ characters
    normal_doc = "<html>This is a normal sized document content.</html>"

    test_data = {
        "research_materials": {
            "cases": [
                {
                    "docid": 111111,
                    "title": "Normal Case",
                    "court": "Test Court",
                    "date": "2023-01-01",
                    "doc_data": {"doc": normal_doc},
                },
                {
                    "docid": 222222,
                    "title": "Large Case That Should Be Skipped",
                    "court": "Test Court",
                    "date": "2023-01-02",
                    "doc_data": {"doc": large_doc},
                },
            ]
        }
    }

    # Write test data to a temporary file
    with open("test_large_cases.json", "w") as f:
        json.dump(test_data, f)

    print(f"📄 Created test file with:")
    print(f"  - Normal case: {len(normal_doc)} characters")
    print(f"  - Large case: {len(large_doc)} characters")
    print()

    # Test the filtering
    cases = load_cases_from_json("test_large_cases.json")

    print(f"\n✅ Results:")
    print(f"  - Cases loaded: {len(cases)}")
    print(f"  - Expected: 1 case (large one should be skipped)")

    if len(cases) == 1 and "111111" in cases:
        print("🎉 SUCCESS: Large case was correctly filtered out!")
    else:
        print("❌ FAIL: Filtering did not work as expected")
        print(f"Cases found: {list(cases.keys())}")

    # Cleanup
    os.remove("test_large_cases.json")


if __name__ == "__main__":
    test_large_doc_filtering()
