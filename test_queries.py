"""
OnboardBot — Test Queries
Automated testing script with 10 in-scope and 3 out-of-scope test queries.
Validates that the RAG pipeline answers correctly and handles edge cases.

Usage:
    python test_queries.py
"""

import sys
# Reconfigure standard output/error to utf-8 to avoid UnicodeEncodeError on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.vector_store import load_vector_store
from src.rag_chain import get_llm, query_rag


# ============================================================================
# TEST QUERIES DEFINITION
# ============================================================================

IN_SCOPE_QUERIES = [
    {
        "id": 1,
        "query": "What is the company's dress code policy?",
        "expected_source": "HR Handbook",
        "expected_keywords": ["smart casual", "casual friday", "business formal"],
    },
    {
        "id": 2,
        "query": "How do I set up VPN on my laptop?",
        "expected_source": "IT Setup Guide",
        "expected_keywords": ["cisco anyconnect", "vpn.nexustech.com"],
    },
    {
        "id": 3,
        "query": "How many casual leaves do I get per year?",
        "expected_source": "Leave & Attendance Policy",
        "expected_keywords": ["12", "casual leave", "15", "days"],
    },
    {
        "id": 4,
        "query": "What is the process for annual performance reviews?",
        "expected_source": "HR Handbook",
        "expected_keywords": ["goal", "review", "assessment", "rating", "self-assessment", "calibration", "performance"],
    },
    {
        "id": 5,
        "query": "How do I configure my email and Slack?",
        "expected_source": "IT Setup Guide",
        "expected_keywords": ["outlook", "slack", "nexustech.slack.com"],
    },
    {
        "id": 6,
        "query": "What is the maternity leave policy?",
        "expected_source": "Leave & Attendance Policy",
        "expected_keywords": ["26 weeks", "maternity"],
    },
    {
        "id": 7,
        "query": "What are the company's core values?",
        "expected_source": "HR Handbook",
        "expected_keywords": ["innovation", "integrity", "collaboration"],
    },
    {
        "id": 8,
        "query": "How do I set up two-factor authentication?",
        "expected_source": "IT Setup Guide",
        "expected_keywords": ["microsoft authenticator", "qr code", "2fa"],
    },
    {
        "id": 9,
        "query": "Can I carry forward unused leaves to next year?",
        "expected_source": "Leave & Attendance Policy",
        "expected_keywords": ["earned leave", "carry forward", "30"],
    },
    {
        "id": 10,
        "query": "What health insurance benefits does the company offer?",
        "expected_source": "HR Handbook",
        "expected_keywords": ["health insurance", "5,00,000", "star health"],
    },
]

OUT_OF_SCOPE_QUERIES = [
    {
        "id": 11,
        "query": "What is the company's stock price today?",
        "expected_behavior": "Should say 'I don't have that information' and suggest HR contact",
    },
    {
        "id": 12,
        "query": "Can you book a flight for my business trip?",
        "expected_behavior": "Should say 'I don't have that information' and suggest HR contact",
    },
    {
        "id": 13,
        "query": "What's the weather like tomorrow?",
        "expected_behavior": "Should say 'I don't have that information' and politely decline",
    },
]


# ============================================================================
# TEST EXECUTION
# ============================================================================

def run_tests():
    """Execute all test queries and report results."""
    
    print("\n" + "=" * 70)
    print("  [Test Suite] OnboardBot - Test Suite")
    print("  Running 10 in-scope + 3 out-of-scope queries")
    print("=" * 70)
    
    # Initialize
    try:
        vector_store = load_vector_store()
        llm = get_llm()
    except FileNotFoundError as e:
        print(f"\n[Error] {e}")
        print("Run 'python ingest.py' first to set up the vector store.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[Error] {e}")
        print("Make sure Ollama is running: 'ollama serve'")
        sys.exit(1)
    
    results = {
        "in_scope_pass": 0,
        "in_scope_fail": 0,
        "out_of_scope_pass": 0,
        "out_of_scope_fail": 0,
    }
    
    # -- In-Scope Tests --
    print(f"\n{'-' * 70}")
    print(f"  IN-SCOPE QUERIES (10 tests)")
    print(f"{'-' * 70}")
    
    for test in IN_SCOPE_QUERIES:
        print(f"\n  Test #{test['id']}: {test['query']}")
        
        start_time = time.time()
        result = query_rag(vector_store, test["query"], llm)
        elapsed = time.time() - start_time
        
        answer_lower = result["answer"].lower()
        
        # Check 1: Is it marked as in-scope?
        scope_ok = result["is_in_scope"]
        
        # Check 2: Does the answer contain expected keywords?
        keywords_found = [
            kw for kw in test["expected_keywords"]
            if kw.lower() in answer_lower
        ]
        keywords_ok = len(keywords_found) > 0
        
        # Check 3: Does it NOT say "I don't have that information"?
        no_denial = "i don't have that information" not in answer_lower
        
        passed = scope_ok and keywords_ok and no_denial
        
        if passed:
            results["in_scope_pass"] += 1
            print(f"  PASS ({elapsed:.1f}s)")
        else:
            results["in_scope_fail"] += 1
            reasons = []
            if not scope_ok:
                reasons.append("marked as out-of-scope")
            if not keywords_ok:
                reasons.append(f"missing keywords: {test['expected_keywords']}")
            if not no_denial:
                reasons.append("incorrectly denied having info")
            print(f"  FAIL ({elapsed:.1f}s) - {'; '.join(reasons)}")
        
        # Show snippet of answer
        snippet = result["answer"][:150].replace("\n", " ")
        print(f"     Answer: {snippet}...")
    
    # -- Out-of-Scope Tests --
    print(f"\n{'-' * 70}")
    print(f"  OUT-OF-SCOPE QUERIES (3 tests)")
    print(f"{'-' * 70}")
    
    for test in OUT_OF_SCOPE_QUERIES:
        print(f"\n  Test #{test['id']}: {test['query']}")
        
        start_time = time.time()
        result = query_rag(vector_store, test["query"], llm)
        elapsed = time.time() - start_time
        
        answer_lower = result["answer"].lower()
        
        # Check: Is it marked as out-of-scope OR does it say "I don't have that information"?
        is_oos = (
            not result["is_in_scope"]
            or "i don't have that information" in answer_lower
            or "i do not have that information" in answer_lower
            or "not available" in answer_lower
            or "cannot find" in answer_lower
        )
        
        if is_oos:
            results["out_of_scope_pass"] += 1
            print(f"  PASS ({elapsed:.1f}s) - Correctly identified as out-of-scope")
        else:
            results["out_of_scope_fail"] += 1
            print(f"  FAIL ({elapsed:.1f}s) - Incorrectly answered (should be out-of-scope)")
        
        # Show snippet of answer
        snippet = result["answer"][:150].replace("\n", " ")
        print(f"     Answer: {snippet}...")
    
    # -- Summary --
    print(f"\n{'=' * 70}")
    print(f"  TEST RESULTS SUMMARY")
    print(f"{'=' * 70}")
    
    total_pass = results["in_scope_pass"] + results["out_of_scope_pass"]
    total_fail = results["in_scope_fail"] + results["out_of_scope_fail"]
    total = total_pass + total_fail
    
    print(f"\n  In-Scope Queries:     {results['in_scope_pass']}/10 passed")
    print(f"  Out-of-Scope Queries: {results['out_of_scope_pass']}/3 passed")
    print(f"  {'-' * 40}")
    print(f"  Total:                {total_pass}/{total} passed ({total_pass/total*100:.0f}%)")
    
    if total_fail == 0:
        print(f"\n  ALL TESTS PASSED!")
    else:
        print(f"\n  {total_fail} test(s) failed. Review the results above.")
    
    print(f"\n{'=' * 70}\n")
    
    return total_fail == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
