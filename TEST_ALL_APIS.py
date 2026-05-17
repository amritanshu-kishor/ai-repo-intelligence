"""
Complete API Testing Script
Tests all endpoints one by one and verifies connections
"""

import requests
import json
import time
import sys
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# API endpoints
PARSER_WORKFLOW_BASE = "http://localhost:8000"
REPO_AI_BASE = "http://localhost:5000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ {text}{Colors.RESET}")

def test_parser_workflow_health():
    """Test 1: Parser-workflow health check"""
    print_header("TEST 1: Parser-Workflow Health Check")
    
    try:
        response = requests.get(f"{PARSER_WORKFLOW_BASE}/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Parser-workflow is running")
            print_info(f"Status: {data.get('status', 'unknown')}")
            print_info(f"Response: {json.dumps(data, indent=2)}")
            return True
        else:
            print_error(f"Parser-workflow returned status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to parser-workflow at http://localhost:8000")
        print_warning("Make sure parser-workflow is running:")
        print_warning("  cd parser-workflow")
        print_warning("  python main.py")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_repo_ai_health():
    """Test 2: Repo-AI health check"""
    print_header("TEST 2: Repo-AI Health Check")
    
    try:
        response = requests.get(f"{REPO_AI_BASE}/api/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Repo-AI is running")
            print_info(f"Status: {data.get('status', 'unknown')}")
            print_info(f"Backend: {data.get('backend', 'unknown')}")
            print_info(f"Parser-workflow: {data.get('parser_workflow', 'unknown')}")
            print_info(f"Active repository: {data.get('active_repository', 'none')}")
            print_info(f"Response: {json.dumps(data, indent=2)}")
            return True
        else:
            print_error(f"Repo-AI returned status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to repo-ai at http://localhost:5000")
        print_warning("Make sure repo-ai is running:")
        print_warning("  cd repo-ai")
        print_warning("  python app.py")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_parser_workflow_endpoints():
    """Test 3: Parser-workflow specific endpoints"""
    print_header("TEST 3: Parser-Workflow Endpoints")
    
    endpoints = [
        ("/health", "GET", "Health check"),
        ("/api/repositories", "GET", "List repositories"),
    ]
    
    results = []
    for endpoint, method, description in endpoints:
        try:
            url = f"{PARSER_WORKFLOW_BASE}{endpoint}"
            print_info(f"Testing: {method} {endpoint} - {description}")
            
            if method == "GET":
                response = requests.get(url, timeout=5)
            else:
                response = requests.post(url, timeout=5)
            
            if response.status_code in [200, 404]:  # 404 is ok for empty lists
                print_success(f"{endpoint} - Status {response.status_code}")
                try:
                    data = response.json()
                    print_info(f"Response preview: {str(data)[:200]}")
                except:
                    pass
                results.append(True)
            else:
                print_error(f"{endpoint} - Status {response.status_code}")
                results.append(False)
                
        except Exception as e:
            print_error(f"{endpoint} - Error: {e}")
            results.append(False)
    
    return all(results)

def test_repo_ai_endpoints():
    """Test 4: Repo-AI specific endpoints"""
    print_header("TEST 4: Repo-AI Endpoints")
    
    endpoints = [
        ("/api/health", "GET", "Health check"),
        ("/", "GET", "Frontend page"),
    ]
    
    results = []
    for endpoint, method, description in endpoints:
        try:
            url = f"{REPO_AI_BASE}{endpoint}"
            print_info(f"Testing: {method} {endpoint} - {description}")
            
            if method == "GET":
                response = requests.get(url, timeout=5)
            else:
                response = requests.post(url, timeout=5)
            
            if response.status_code == 200:
                print_success(f"{endpoint} - Status {response.status_code}")
                if endpoint != "/":  # Don't print HTML
                    try:
                        data = response.json()
                        print_info(f"Response preview: {str(data)[:200]}")
                    except:
                        pass
                results.append(True)
            else:
                print_error(f"{endpoint} - Status {response.status_code}")
                results.append(False)
                
        except Exception as e:
            print_error(f"{endpoint} - Error: {e}")
            results.append(False)
    
    return all(results)

def test_integration():
    """Test 5: Integration between systems"""
    print_header("TEST 5: Integration Test")
    
    try:
        # Check if repo-ai can reach parser-workflow
        print_info("Checking if repo-ai can communicate with parser-workflow...")
        
        response = requests.get(f"{REPO_AI_BASE}/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            parser_status = data.get('parser_workflow', 'unknown')
            
            if parser_status == 'available':
                print_success("Integration working: repo-ai ↔ parser-workflow")
                return True
            else:
                print_error(f"Integration issue: parser_workflow status is '{parser_status}'")
                print_warning("This means repo-ai cannot reach parser-workflow")
                return False
        else:
            print_error("Cannot check integration status")
            return False
            
    except Exception as e:
        print_error(f"Integration test failed: {e}")
        return False

def test_upload_endpoint():
    """Test 6: Upload endpoint (without actual file)"""
    print_header("TEST 6: Upload Endpoint Check")
    
    try:
        # Just check if endpoint exists (will fail without file, but that's ok)
        print_info("Checking if upload endpoint exists...")
        
        response = requests.post(
            f"{REPO_AI_BASE}/api/upload-repository",
            timeout=5
        )
        
        # We expect 400 (no file) or 500, not 404
        if response.status_code in [400, 500]:
            print_success("Upload endpoint exists and is responding")
            print_info(f"Status: {response.status_code} (expected without file)")
            return True
        elif response.status_code == 404:
            print_error("Upload endpoint not found (404)")
            return False
        else:
            print_warning(f"Unexpected status: {response.status_code}")
            return True  # Endpoint exists
            
    except Exception as e:
        print_error(f"Upload endpoint test failed: {e}")
        return False

def test_query_endpoint():
    """Test 7: Query endpoint (without repository)"""
    print_header("TEST 7: Query Endpoint Check")
    
    try:
        print_info("Checking if query endpoint exists...")
        
        response = requests.post(
            f"{REPO_AI_BASE}/api/ask-query",
            json={"query": "test query"},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        # Should work even without repository (will use mock data)
        if response.status_code == 200:
            print_success("Query endpoint exists and is responding")
            data = response.json()
            print_info(f"Success: {data.get('success', False)}")
            print_info(f"Data source: {data.get('data_source', 'unknown')}")
            return True
        else:
            print_error(f"Query endpoint returned status {response.status_code}")
            try:
                print_info(f"Response: {response.json()}")
            except:
                pass
            return False
            
    except Exception as e:
        print_error(f"Query endpoint test failed: {e}")
        return False

def test_graph_endpoint():
    """Test 8: Graph endpoint (will fail without repository)"""
    print_header("TEST 8: Graph Endpoint Check")
    
    try:
        print_info("Checking if graph endpoint exists...")
        
        # Try with a dummy repository ID
        response = requests.get(
            f"{REPO_AI_BASE}/api/graph/test-repo",
            timeout=5
        )
        
        # We expect 404 or 500 (no repository), not endpoint not found
        if response.status_code in [404, 500]:
            print_success("Graph endpoint exists and is responding")
            print_info(f"Status: {response.status_code} (expected without repository)")
            try:
                data = response.json()
                print_info(f"Response: {data}")
            except:
                pass
            return True
        elif response.status_code == 200:
            print_success("Graph endpoint exists and returned data")
            return True
        else:
            print_error(f"Unexpected status: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Graph endpoint test failed: {e}")
        return False

def print_summary(results):
    """Print test summary"""
    print_header("TEST SUMMARY")
    
    total = len(results)
    passed = sum(results.values())
    failed = total - passed
    
    print(f"Total Tests: {total}")
    print(f"{Colors.GREEN}Passed: {passed}{Colors.RESET}")
    print(f"{Colors.RED}Failed: {failed}{Colors.RESET}")
    print()
    
    for test_name, result in results.items():
        status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if result else f"{Colors.RED}✗ FAIL{Colors.RESET}"
        print(f"{status} - {test_name}")
    
    print()
    
    if failed == 0:
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 ALL TESTS PASSED!{Colors.RESET}")
        print(f"{Colors.GREEN}System is ready for use.{Colors.RESET}")
    else:
        print(f"{Colors.RED}{Colors.BOLD}⚠ SOME TESTS FAILED{Colors.RESET}")
        print(f"{Colors.YELLOW}Please fix the failed tests before proceeding.{Colors.RESET}")

def main():
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("=" * 60)
    print("         COMPLETE API TESTING SUITE")
    print("         Testing All Endpoints One by One")
    print("=" * 60)
    print(f"{Colors.RESET}\n")
    
    print_info("This script will test:")
    print_info("  1. Parser-workflow health")
    print_info("  2. Repo-AI health")
    print_info("  3. Parser-workflow endpoints")
    print_info("  4. Repo-AI endpoints")
    print_info("  5. Integration between systems")
    print_info("  6. Upload endpoint")
    print_info("  7. Query endpoint")
    print_info("  8. Graph endpoint")
    print()
    
    input("Press Enter to start testing...")
    
    results = {}
    
    # Run all tests
    results["Parser-Workflow Health"] = test_parser_workflow_health()
    time.sleep(1)
    
    results["Repo-AI Health"] = test_repo_ai_health()
    time.sleep(1)
    
    results["Parser-Workflow Endpoints"] = test_parser_workflow_endpoints()
    time.sleep(1)
    
    results["Repo-AI Endpoints"] = test_repo_ai_endpoints()
    time.sleep(1)
    
    results["Integration Test"] = test_integration()
    time.sleep(1)
    
    results["Upload Endpoint"] = test_upload_endpoint()
    time.sleep(1)
    
    results["Query Endpoint"] = test_query_endpoint()
    time.sleep(1)
    
    results["Graph Endpoint"] = test_graph_endpoint()
    
    # Print summary
    print_summary(results)
    
    # Return exit code
    return 0 if all(results.values()) else 1

if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
