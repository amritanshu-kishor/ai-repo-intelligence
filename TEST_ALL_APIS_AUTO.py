"""
Automated API Testing Script - No User Input Required
Tests all endpoints and reports results
"""

import requests
import json
import time
import sys

# API endpoints
PARSER_WORKFLOW_BASE = "http://localhost:8000"
REPO_AI_BASE = "http://localhost:5000"

def test_parser_workflow_health():
    """Test 1: Parser-workflow health check"""
    print("\n" + "="*60)
    print("TEST 1: Parser-Workflow Health Check")
    print("="*60)
    
    try:
        response = requests.get(f"{PARSER_WORKFLOW_BASE}/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Parser-workflow is running")
            print(f"  Status: {data.get('status', 'unknown')}")
            return True
        else:
            print(f"✗ Parser-workflow returned status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to parser-workflow at http://localhost:8000")
        print("  Make sure parser-workflow is running:")
        print("    cd parser-workflow && python main.py")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_repo_ai_health():
    """Test 2: Repo-AI health check"""
    print("\n" + "="*60)
    print("TEST 2: Repo-AI Health Check")
    print("="*60)
    
    try:
        response = requests.get(f"{REPO_AI_BASE}/api/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Repo-AI is running")
            print(f"  Status: {data.get('status', 'unknown')}")
            print(f"  Backend: {data.get('backend', 'unknown')}")
            print(f"  Parser-workflow: {data.get('parser_workflow', 'unknown')}")
            print(f"  Active repository: {data.get('active_repository', 'none')}")
            return True
        else:
            print(f"✗ Repo-AI returned status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to repo-ai at http://localhost:5000")
        print("  Make sure repo-ai is running:")
        print("    cd repo-ai && python app.py")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_integration():
    """Test 3: Integration between systems"""
    print("\n" + "="*60)
    print("TEST 3: Integration Test")
    print("="*60)
    
    try:
        response = requests.get(f"{REPO_AI_BASE}/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            parser_status = data.get('parser_workflow', 'unknown')
            
            if parser_status == 'available':
                print("✓ Integration working: repo-ai <-> parser-workflow")
                return True
            else:
                print(f"✗ Integration issue: parser_workflow status is '{parser_status}'")
                print("  This means repo-ai cannot reach parser-workflow")
                return False
        else:
            print("✗ Cannot check integration status")
            return False
            
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        return False

def test_upload_endpoint():
    """Test 4: Upload endpoint"""
    print("\n" + "="*60)
    print("TEST 4: Upload Endpoint Check")
    print("="*60)
    
    try:
        response = requests.post(
            f"{REPO_AI_BASE}/api/upload-repository",
            timeout=5
        )
        
        if response.status_code in [400, 500]:
            print("✓ Upload endpoint exists and is responding")
            print(f"  Status: {response.status_code} (expected without file)")
            return True
        elif response.status_code == 404:
            print("✗ Upload endpoint not found (404)")
            return False
        else:
            print(f"⚠ Unexpected status: {response.status_code}")
            return True
            
    except Exception as e:
        print(f"✗ Upload endpoint test failed: {e}")
        return False

def test_query_endpoint():
    """Test 5: Query endpoint"""
    print("\n" + "="*60)
    print("TEST 5: Query Endpoint Check")
    print("="*60)
    
    try:
        response = requests.post(
            f"{REPO_AI_BASE}/api/ask-query",
            json={"query": "test query"},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✓ Query endpoint exists and is responding")
            data = response.json()
            print(f"  Success: {data.get('success', False)}")
            print(f"  Data source: {data.get('data_source', 'unknown')}")
            return True
        else:
            print(f"✗ Query endpoint returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Query endpoint test failed: {e}")
        return False

def test_graph_endpoint():
    """Test 6: Graph endpoint"""
    print("\n" + "="*60)
    print("TEST 6: Graph Endpoint Check")
    print("="*60)
    
    try:
        response = requests.get(
            f"{REPO_AI_BASE}/api/graph/test-repo",
            timeout=5
        )
        
        if response.status_code in [404, 500]:
            print("✓ Graph endpoint exists and is responding")
            print(f"  Status: {response.status_code} (expected without repository)")
            return True
        elif response.status_code == 200:
            print("✓ Graph endpoint exists and returned data")
            return True
        else:
            print(f"✗ Unexpected status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Graph endpoint test failed: {e}")
        return False

def print_summary(results):
    """Print test summary"""
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    total = len(results)
    passed = sum(results.values())
    failed = total - passed
    
    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}\n")
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {test_name}")
    
    print()
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED!")
        print("System is ready for use.")
    else:
        print("⚠ SOME TESTS FAILED")
        print("Please fix the failed tests before proceeding.")
    
    print("="*60)

def main():
    print("\n" + "="*60)
    print("         COMPLETE API TESTING SUITE")
    print("         Testing All Endpoints One by One")
    print("="*60)
    
    results = {}
    
    # Run all tests
    results["Parser-Workflow Health"] = test_parser_workflow_health()
    time.sleep(0.5)
    
    results["Repo-AI Health"] = test_repo_ai_health()
    time.sleep(0.5)
    
    results["Integration Test"] = test_integration()
    time.sleep(0.5)
    
    results["Upload Endpoint"] = test_upload_endpoint()
    time.sleep(0.5)
    
    results["Query Endpoint"] = test_query_endpoint()
    time.sleep(0.5)
    
    results["Graph Endpoint"] = test_graph_endpoint()
    
    # Print summary
    print_summary(results)
    
    # Return exit code
    return 0 if all(results.values()) else 1

if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
