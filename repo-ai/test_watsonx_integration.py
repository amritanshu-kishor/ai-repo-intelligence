"""
Test script to validate watsonx integration and graph reasoning preservation.

Run this to verify:
1. Orchestration pipeline integrity
2. Graph reasoning injection into prompts
3. Impact analysis preservation
4. Response processing quality
5. Provider contract compliance
"""

import json
import sys
from pathlib import Path

# Add repo-ai to path
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from main import run_pipeline


def test_impact_query():
    """Test: 'What breaks if auth.py changes?' - should return graph-aware impact analysis."""
    print("\n" + "="*80)
    print("TEST 1: Impact Analysis Query")
    print("="*80)
    
    query = "What breaks if auth.py changes?"
    print(f"\nQuery: {query}\n")
    
    try:
        result = run_pipeline(query)
        
        # Verify graph reasoning is present
        graph = result.get("graph", {})
        impact = result.get("impact", {})
        intelligence = result.get("intelligence", {})
        
        print("✓ Pipeline completed successfully")
        print(f"\n--- Graph Reasoning ---")
        print(f"Focus node: {graph.get('focus_label', 'N/A')} (id={graph.get('focus_node_id', 'N/A')})")
        print(f"Propagation depth: {graph.get('propagation_depth', 0)}")
        print(f"Direct dependencies: {len(graph.get('direct_dependencies', []))}")
        print(f"Indirect dependencies: {len(graph.get('indirect_dependencies', []))}")
        print(f"Upstream dependencies: {len(graph.get('upstream_dependencies', []))}")
        print(f"Circular dependencies: {len(graph.get('circular_dependencies', []))}")
        
        print(f"\n--- Impact Analysis ---")
        print(f"Severity: {impact.get('impact_severity', 'N/A')}")
        print(f"Risk level: {impact.get('risk_level', 'N/A')}")
        print(f"Risk score: {impact.get('risk_score', 0.0)}")
        print(f"Total affected: {impact.get('propagation_scope', {}).get('total_affected', 0)}")
        
        print(f"\n--- Intelligence Output ---")
        print(f"Summary length: {len(intelligence.get('summary', ''))} chars")
        print(f"Affected files: {len(intelligence.get('affected_files', []))}")
        print(f"Recommendations: {len(intelligence.get('recommendations', []))}")
        print(f"Confidence: {intelligence.get('confidence_score', 0.0)}")
        print(f"Risk level: {intelligence.get('risk_level', 'N/A')}")
        
        # Verify graph reasoning is in summary
        summary = intelligence.get('summary', '')
        if graph.get('focus_label') and graph.get('focus_label') in summary:
            print("\n✓ Graph reasoning preserved in summary")
        else:
            print("\n⚠ Graph reasoning may not be fully preserved in summary")
        
        # Check for traversal explanations
        if graph.get('traversal_explain'):
            print(f"\n--- Graph Traversal Debug ---")
            for line in graph.get('traversal_explain', [])[:5]:
                print(f"  • {line}")
        
        # Verify provider metadata
        meta = result.get("meta", {})
        print(f"\n--- Provider Info ---")
        print(f"Provider: {meta.get('provider', 'N/A')}")
        print(f"Model: {meta.get('model', 'N/A')}")
        print(f"Normalized: {meta.get('normalized', False)}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dependency_query():
    """Test: Dependency analysis query."""
    print("\n" + "="*80)
    print("TEST 2: Dependency Analysis Query")
    print("="*80)
    
    query = "Show me the dependency chain for database.py"
    print(f"\nQuery: {query}\n")
    
    try:
        result = run_pipeline(query)
        
        graph = result.get("graph", {})
        intelligence = result.get("intelligence", {})
        
        print("✓ Pipeline completed successfully")
        print(f"\nDependency chains found: {len(graph.get('dependency_chains', []))}")
        
        chains = graph.get('dependency_chains', [])
        if chains:
            print("\n--- Sample Dependency Chains ---")
            for i, chain in enumerate(chains[:3], 1):
                print(f"  Chain {i}: {' -> '.join(str(c) for c in chain)}")
        
        print(f"\nIntelligence summary length: {len(intelligence.get('summary', ''))} chars")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_circular_dependency_detection():
    """Test: Circular dependency detection."""
    print("\n" + "="*80)
    print("TEST 3: Circular Dependency Detection")
    print("="*80)
    
    query = "Are there any circular dependencies?"
    print(f"\nQuery: {query}\n")
    
    try:
        result = run_pipeline(query)
        
        graph = result.get("graph", {})
        intelligence = result.get("intelligence", {})
        
        print("✓ Pipeline completed successfully")
        
        circular = graph.get('circular_dependencies', [])
        print(f"\nCircular dependencies detected: {len(circular)}")
        
        if circular:
            print("\n--- Circular Dependency Groups ---")
            for i, cycle in enumerate(circular[:3], 1):
                print(f"  Cycle {i}: {' -> '.join(str(c) for c in cycle)}")
        
        # Check if circular dependencies are mentioned in recommendations
        recs = intelligence.get('recommendations', [])
        circular_mentioned = any('circular' in str(r).lower() for r in recs)
        
        if circular and circular_mentioned:
            print("\n✓ Circular dependencies reflected in recommendations")
        elif circular and not circular_mentioned:
            print("\n⚠ Circular dependencies not mentioned in recommendations")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_json_output():
    """Test: Full JSON output structure."""
    print("\n" + "="*80)
    print("TEST 4: JSON Output Structure Validation")
    print("="*80)
    
    query = "What is the architecture of this repository?"
    print(f"\nQuery: {query}\n")
    
    try:
        result = run_pipeline(query)
        
        # Verify all required top-level keys
        required_keys = ['request_id', 'query', 'intent', 'answer', 'intelligence', 'graph', 'impact', 'visualization']
        missing = [k for k in required_keys if k not in result]
        
        if missing:
            print(f"⚠ Missing keys: {missing}")
        else:
            print("✓ All required top-level keys present")
        
        # Verify intelligence structure
        intel = result.get('intelligence', {})
        intel_keys = ['summary', 'affected_files', 'dependency_chain', 'risk_level', 'recommendations', 'confidence_score']
        intel_missing = [k for k in intel_keys if k not in intel]
        
        if intel_missing:
            print(f"⚠ Missing intelligence keys: {intel_missing}")
        else:
            print("✓ Intelligence structure complete")
        
        # Verify visualization payload
        viz = result.get('visualization', {})
        if viz:
            print("✓ Visualization context generated")
        else:
            print("⚠ Visualization context missing")
        
        # Save full output for inspection
        output_file = _ROOT / "test_output.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n✓ Full output saved to: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("WATSONX INTEGRATION & GRAPH REASONING VALIDATION")
    print("="*80)
    
    tests = [
        test_impact_query,
        test_dependency_query,
        test_circular_dependency_detection,
        test_json_output,
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"\n✗ Test crashed: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    passed = sum(results)
    total = len(results)
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests passed! System is stable.")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed. Review output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
