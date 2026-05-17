"""
Integration Layer Test Script

Tests the connection between repo-ai and parser-workflow backend.

Usage:
    python test_integration.py

Requirements:
    - parser-workflow backend running on http://127.0.0.1:8001
    - OR USE_MOCK_DATA=true in .env for fallback testing
"""

import sys
from pathlib import Path

# Add repo-ai to path
sys.path.insert(0, str(Path(__file__).parent))

from integrations.parser_connector import parser_connector, ParserUnavailableError
from integrations.fallback_handler import get_fallback_handler
from integrations.response_contracts import (
    validate_graph_data,
    validate_dependencies_data,
)
from config import MOCK_DATA_DIR, USE_MOCK_DATA


def test_health_check():
    """Test backend health check."""
    print("\n" + "=" * 60)
    print("TEST 1: Backend Health Check")
    print("=" * 60)
    
    is_healthy = parser_connector.health_check()
    
    if is_healthy:
        print("✓ Parser-workflow backend is HEALTHY")
        print("  Backend URL: http://127.0.0.1:8001")
        return True
    else:
        print("✗ Parser-workflow backend is UNAVAILABLE")
        print("  Backend URL: http://127.0.0.1:8001")
        print("  Fallback mode will be used")
        return False


def test_graph_integration(repository_id: str = "test-repo"):
    """Test graph data fetching."""
    print("\n" + "=" * 60)
    print("TEST 2: Graph Data Integration")
    print("=" * 60)
    print(f"Repository ID: {repository_id}")
    
    try:
        graph_data = parser_connector.fetch_dependency_graph(repository_id)
        
        print(f"✓ Graph data fetched successfully")
        print(f"  Nodes: {len(graph_data.get('nodes', []))}")
        print(f"  Edges: {len(graph_data.get('edges', []))}")
        print(f"  Format: {graph_data.get('format', 'unknown')}")
        
        # Validate structure
        is_valid = validate_graph_data(graph_data)
        if is_valid:
            print("✓ Graph data structure is VALID")
        else:
            print("✗ Graph data structure is INVALID")
        
        return True
        
    except ParserUnavailableError as e:
        print(f"✗ Backend unavailable: {e}")
        print("  Testing fallback...")
        
        fallback_handler = get_fallback_handler(MOCK_DATA_DIR)
        fallback_graph = fallback_handler.get_fallback_graph(repository_id)
        
        print(f"✓ Fallback graph loaded")
        print(f"  Nodes: {len(fallback_graph.get('nodes', []))}")
        print(f"  Edges: {len(fallback_graph.get('edges', []))}")
        
        return False
        
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def test_dependencies_integration(repository_id: str = "test-repo"):
    """Test dependencies data fetching."""
    print("\n" + "=" * 60)
    print("TEST 3: Dependencies Data Integration")
    print("=" * 60)
    print(f"Repository ID: {repository_id}")
    
    try:
        deps_data = parser_connector.fetch_dependencies(repository_id)
        
        print(f"✓ Dependencies data fetched successfully")
        print(f"  External: {len(deps_data.get('external', []))}")
        print(f"  Internal: {len(deps_data.get('internal', []))}")
        print(f"  Risk Flags: {len(deps_data.get('risk_flags', []))}")
        
        # Validate structure
        is_valid = validate_dependencies_data(deps_data)
        if is_valid:
            print("✓ Dependencies data structure is VALID")
        else:
            print("✗ Dependencies data structure is INVALID")
        
        return True
        
    except ParserUnavailableError as e:
        print(f"✗ Backend unavailable: {e}")
        print("  Testing fallback...")
        
        fallback_handler = get_fallback_handler(MOCK_DATA_DIR)
        fallback_deps = fallback_handler.get_fallback_dependencies(repository_id)
        
        print(f"✓ Fallback dependencies loaded")
        print(f"  External: {len(fallback_deps.get('external', []))}")
        print(f"  Internal: {len(fallback_deps.get('internal', []))}")
        
        return False
        
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def test_full_context_integration(repository_id: str = "test-repo"):
    """Test full context fetching."""
    print("\n" + "=" * 60)
    print("TEST 4: Full Context Integration")
    print("=" * 60)
    print(f"Repository ID: {repository_id}")
    
    try:
        context = parser_connector.fetch_all_context(repository_id)
        
        print(f"✓ Full context fetched")
        print(f"  Sources: {', '.join(context['metadata']['sources'])}")
        print(f"  Backend: {context['metadata']['backend']}")
        
        if context['metadata']['errors']:
            print(f"  Errors: {len(context['metadata']['errors'])}")
            for error in context['metadata']['errors']:
                print(f"    - {error}")
        
        # Check what data is available
        has_graph = context['graph_data'] is not None
        has_deps = context['dependencies'] is not None
        has_summaries = context['repository_context'].get('summaries') is not None
        
        print(f"\n  Data Availability:")
        print(f"    Graph: {'✓' if has_graph else '✗'}")
        print(f"    Dependencies: {'✓' if has_deps else '✗'}")
        print(f"    Summaries: {'✓' if has_summaries else '✗'}")
        
        return True
        
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def test_fallback_handler():
    """Test fallback handler functionality."""
    print("\n" + "=" * 60)
    print("TEST 5: Fallback Handler")
    print("=" * 60)
    
    fallback_handler = get_fallback_handler(MOCK_DATA_DIR)
    repository_id = "fallback-test-repo"
    
    # Test graph fallback
    print("\nTesting graph fallback...")
    graph = fallback_handler.get_fallback_graph(repository_id)
    print(f"✓ Graph fallback: {len(graph.get('nodes', []))} nodes")
    
    # Test dependencies fallback
    print("\nTesting dependencies fallback...")
    deps = fallback_handler.get_fallback_dependencies(repository_id)
    print(f"✓ Dependencies fallback: {len(deps.get('external', []))} external")
    
    # Test summaries fallback
    print("\nTesting summaries fallback...")
    summaries = fallback_handler.get_fallback_summaries(repository_id)
    print(f"✓ Summaries fallback: {len(summaries.get('items', []))} items")
    
    # Test graph validation and repair
    print("\nTesting graph validation...")
    invalid_graph = {"nodes": "invalid", "edges": []}
    repaired = fallback_handler.validate_and_repair_graph(invalid_graph, repository_id)
    print(f"✓ Graph repaired: {len(repaired.get('nodes', []))} nodes")
    
    return True


def test_context_builder_integration():
    """Test context_builder.py integration."""
    print("\n" + "=" * 60)
    print("TEST 6: Context Builder Integration")
    print("=" * 60)
    
    try:
        from ai.context_builder import retrieve
        from ai.intent_classifier import classify
        
        # Create a test query
        query = "What are the dependencies of module A?"
        
        # Classify intent
        print(f"Query: {query}")
        intent_result = classify(query)
        print(f"✓ Intent classified: {intent_result.get('intent', 'unknown')}")
        
        # Retrieve context
        print("\nRetrieving context...")
        context_result = retrieve(
            intent_result,
            repository_id="test-repo",
        )
        
        print(f"✓ Context retrieved")
        print(f"  Repository: {context_result.get('repository_id', 'unknown')}")
        print(f"  Intent: {context_result.get('intent', 'unknown')}")
        print(f"  Data keys: {', '.join(context_result.get('data', {}).keys())}")
        
        # Check provenance
        provenance = context_result.get('provenance', {})
        print(f"\n  Provenance:")
        print(f"    Mode: {provenance.get('mode', 'unknown')}")
        print(f"    Sources: {len(provenance.get('sources', []))}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all integration tests."""
    print("\n" + "=" * 60)
    print("REPO-AI INTEGRATION LAYER TEST SUITE")
    print("=" * 60)
    print(f"Mock Data Mode: {USE_MOCK_DATA}")
    print(f"Mock Data Dir: {MOCK_DATA_DIR}")
    
    results = []
    
    # Run tests
    results.append(("Health Check", test_health_check()))
    results.append(("Graph Integration", test_graph_integration()))
    results.append(("Dependencies Integration", test_dependencies_integration()))
    results.append(("Full Context Integration", test_full_context_integration()))
    results.append(("Fallback Handler", test_fallback_handler()))
    results.append(("Context Builder Integration", test_context_builder_integration()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests PASSED!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
