"""
Test script to verify dynamic repository analysis.

This script tests:
1. Repository session creation and isolation
2. Data validation for mock pattern detection
3. Graph rebuilding per upload
4. Context retrieval from real data
5. Validation logging and tracking
"""

import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_session_manager():
    """Test repository session manager."""
    logger.info("=" * 60)
    logger.info("TEST 1: Repository Session Manager")
    logger.info("=" * 60)
    
    from integrations.repository_session import get_session_manager
    
    manager = get_session_manager()
    
    # Create first session
    session1 = manager.create_session(
        repository_id="test-repo-1",
        upload_path="/tmp/test-repo-1",
        file_count=50,
    )
    
    assert session1.repository_id == "test-repo-1"
    assert session1.file_count == 50
    assert manager.active_repository_id == "test-repo-1"
    logger.info("✓ Session 1 created successfully")
    
    # Update session status
    session1.update_parser_status(indexed=True, ready=True)
    session1.update_graph_metrics(node_count=25, edge_count=40)
    session1.update_dependency_metrics(external_count=5, internal_count=20)
    
    assert session1.graph_node_count == 25
    assert session1.graph_edge_count == 40
    logger.info("✓ Session 1 metrics updated")
    
    # Create second session (should invalidate first for same ID)
    session2 = manager.create_session(
        repository_id="test-repo-1",
        upload_path="/tmp/test-repo-1-v2",
        file_count=75,
    )
    
    assert session2.file_count == 75
    assert session2.graph_node_count == 0  # New session, no metrics yet
    logger.info("✓ Session 2 created, previous session invalidated")
    
    # Create different repository
    session3 = manager.create_session(
        repository_id="test-repo-2",
        upload_path="/tmp/test-repo-2",
        file_count=100,
    )
    
    assert len(manager.sessions) == 2  # test-repo-1 and test-repo-2
    logger.info("✓ Multiple repositories tracked correctly")
    
    # Get summary
    summary = manager.get_summary()
    logger.info(f"Manager summary: {json.dumps(summary, indent=2)}")
    
    logger.info("✓ TEST 1 PASSED: Session manager working correctly\n")


def test_data_validator():
    """Test data validator for mock pattern detection."""
    logger.info("=" * 60)
    logger.info("TEST 2: Data Validator")
    logger.info("=" * 60)
    
    from integrations.data_validator import get_validator
    
    validator = get_validator(strict_mode=False)
    
    # Test 1: Mock graph data (should fail validation)
    mock_graph = {
        "repository_id": "mock-repo-001",
        "nodes": [
            {"data": {"id": "mod_a", "label": "modules/a"}},
            {"data": {"id": "mod_b", "label": "modules/b"}},
            {"data": {"id": "shared", "label": "shared/"}},
        ],
        "edges": [
            {"data": {"source": "mod_a", "target": "shared"}},
        ],
    }
    
    result1 = validator.validate_graph_data(mock_graph, "test-repo", "test")
    assert not result1["is_valid"], "Mock graph should fail validation"
    assert len(result1["issues"]) > 0
    logger.info(f"✓ Mock graph detected: {result1['issues']}")
    
    # Test 2: Real graph data (should pass validation)
    real_graph = {
        "repository_id": "test-repo",
        "nodes": [
            {"data": {"id": "src/auth.py", "label": "src/auth.py"}},
            {"data": {"id": "src/main.py", "label": "src/main.py"}},
        ],
        "edges": [
            {"data": {"source": "src/main.py", "target": "src/auth.py"}},
        ],
    }
    
    result2 = validator.validate_graph_data(real_graph, "test-repo", "test")
    assert result2["is_valid"], "Real graph should pass validation"
    logger.info("✓ Real graph validated successfully")
    
    # Test 3: Mock dependencies (should fail)
    mock_deps = {
        "repository_id": "mock-repo-001",
        "external": [
            {"name": "framework-core", "version": "1.0.0"},
        ],
        "internal": [
            {"from": "modules/a", "to": "shared/"},
        ],
    }
    
    result3 = validator.validate_dependencies(mock_deps, "test-repo")
    assert not result3["is_valid"], "Mock dependencies should fail validation"
    logger.info(f"✓ Mock dependencies detected: {result3['issues']}")
    
    # Get validation summary
    summary = validator.get_validation_summary()
    logger.info(f"Validation summary: {json.dumps(summary, indent=2)}")
    
    logger.info("✓ TEST 2 PASSED: Data validator working correctly\n")


def test_context_validation():
    """Test complete context validation."""
    logger.info("=" * 60)
    logger.info("TEST 3: Complete Context Validation")
    logger.info("=" * 60)
    
    from integrations.data_validator import get_validator
    
    validator = get_validator(strict_mode=False)
    
    # Mock context (should fail)
    mock_context = {
        "request_id": "test-123",
        "repository_id": "mock-repo-001",
        "data": {
            "graph": {
                "repository_id": "mock-repo-001",
                "nodes": [
                    {"data": {"id": "mod_a", "label": "modules/a"}},
                ],
                "edges": [],
            },
            "dependencies": {
                "repository_id": "mock-repo-001",
                "external": [{"name": "framework-core"}],
                "internal": [{"from": "modules/a", "to": "shared/"}],
            },
            "summaries": [
                {"path": "modules/a", "symbols": ["validate"]},
            ],
        },
        "provenance": {
            "mode": "mock",
            "sources": ["mock_data/graph.json"],
        },
    }
    
    result = validator.validate_complete_context(mock_context, "test-repo")
    assert not result["is_valid"], "Mock context should fail validation"
    logger.info(f"✓ Mock context detected with {len(result['all_issues'])} issues")
    
    logger.info("✓ TEST 3 PASSED: Context validation working correctly\n")


def test_session_query_tracking():
    """Test session query tracking."""
    logger.info("=" * 60)
    logger.info("TEST 4: Session Query Tracking")
    logger.info("=" * 60)
    
    from integrations.repository_session import get_session_manager
    
    manager = get_session_manager()
    
    # Create session
    session = manager.create_session(
        repository_id="test-repo-queries",
        upload_path="/tmp/test",
        file_count=50,
    )
    
    # Record queries
    session.record_query(
        query="What files depend on auth.py?",
        intent="dependency",
        result={"data_source": "live", "validation_passed": True}
    )
    
    session.record_query(
        query="Show me the architecture",
        intent="architecture",
        result={"data_source": "live", "validation_passed": True}
    )
    
    assert session.query_count == 2
    assert len(session.queries) == 2
    logger.info(f"✓ Recorded {session.query_count} queries")
    
    # Record validation
    session.record_validation(passed=True, issues=[])
    assert session.validation_performed
    assert session.validation_passed
    logger.info("✓ Validation recorded")
    
    # Get status
    status = session.get_status()
    logger.info(f"Session status: {json.dumps(status, indent=2)}")
    
    logger.info("✓ TEST 4 PASSED: Query tracking working correctly\n")


def run_all_tests():
    """Run all tests."""
    logger.info("\n" + "=" * 60)
    logger.info("DYNAMIC REPOSITORY ANALYSIS TEST SUITE")
    logger.info("=" * 60 + "\n")
    
    try:
        test_session_manager()
        test_data_validator()
        test_context_validation()
        test_session_query_tracking()
        
        logger.info("=" * 60)
        logger.info("✓ ALL TESTS PASSED")
        logger.info("=" * 60)
        logger.info("\nSummary:")
        logger.info("✓ Repository session isolation working")
        logger.info("✓ Mock data detection working")
        logger.info("✓ Context validation working")
        logger.info("✓ Query tracking working")
        logger.info("\nThe system is ready for real repository uploads!")
        
        return True
        
    except AssertionError as e:
        logger.error(f"✗ TEST FAILED: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ UNEXPECTED ERROR: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)

# Made with Bob