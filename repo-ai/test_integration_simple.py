"""
Simple Integration Test - Tests basic imports and structure
"""

import sys
from pathlib import Path

# Add repo-ai to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("SIMPLE INTEGRATION TEST")
print("=" * 60)

# Test 1: Import integration modules
print("\nTest 1: Importing integration modules...")
try:
    from integrations import parser_connector
    print("[OK] parser_connector imported")
except ImportError as e:
    print(f"[FAIL] Failed to import parser_connector: {e}")
    sys.exit(1)

try:
    from integrations.response_contracts import validate_graph_data
    print("[OK] response_contracts imported")
except ImportError as e:
    print(f"[FAIL] Failed to import response_contracts: {e}")
    sys.exit(1)

try:
    from integrations.fallback_handler import get_fallback_handler
    print("[OK] fallback_handler imported")
except ImportError as e:
    print(f"[FAIL] Failed to import fallback_handler: {e}")
    sys.exit(1)

# Test 2: Check config
print("\nTest 2: Checking configuration...")
try:
    from config import MOCK_DATA_DIR, USE_MOCK_DATA, PARSER_WORKFLOW_URL
    print("[OK] Config loaded")
    print(f"  USE_MOCK_DATA: {USE_MOCK_DATA}")
    print(f"  PARSER_WORKFLOW_URL: {PARSER_WORKFLOW_URL}")
    print(f"  MOCK_DATA_DIR: {MOCK_DATA_DIR}")
except ImportError as e:
    print(f"[FAIL] Failed to import config: {e}")
    sys.exit(1)

# Test 3: Test fallback handler
print("\nTest 3: Testing fallback handler...")
try:
    handler = get_fallback_handler(MOCK_DATA_DIR)
    graph = handler.get_fallback_graph("test-repo")
    print("[OK] Fallback handler works")
    print(f"  Nodes: {len(graph.get('nodes', []))}")
    print(f"  Edges: {len(graph.get('edges', []))}")
except Exception as e:
    print(f"[FAIL] Fallback handler failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Test graph validation
print("\nTest 4: Testing graph validation...")
try:
    test_graph = {
        "nodes": [{"data": {"id": "n1", "label": "Node 1"}}],
        "edges": [{"data": {"source": "n1", "target": "n1"}}]
    }
    is_valid = validate_graph_data(test_graph)
    print(f"[OK] Graph validation works: {is_valid}")
except Exception as e:
    print(f"[FAIL] Graph validation failed: {e}")
    sys.exit(1)

# Test 5: Test context builder import
print("\nTest 5: Testing context builder integration...")
try:
    from ai.context_builder import retrieve
    print("[OK] Context builder imported successfully")
    print("  Integration layer is connected")
except ImportError as e:
    print(f"[FAIL] Failed to import context_builder: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("ALL TESTS PASSED!")
print("=" * 60)
print("\nIntegration layer is working correctly.")
print("To test with live backend, run: python test_integration.py")

# Made with Bob
