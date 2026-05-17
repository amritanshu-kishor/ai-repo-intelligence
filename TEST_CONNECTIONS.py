"""
Simple Connection Test - ASCII Only
"""

import requests
import sys

print("\n" + "="*60)
print("CONNECTION TEST")
print("="*60 + "\n")

# Test 1: Parser-Workflow
print("TEST 1: Parser-Workflow (http://localhost:8000)")
try:
    response = requests.get("http://localhost:8000/health", timeout=5)
    if response.status_code == 200:
        print("[OK] Parser-workflow is running")
        print(f"     Response: {response.json()}")
    else:
        print(f"[FAIL] Status {response.status_code}")
except requests.exceptions.ConnectionError:
    print("[FAIL] Cannot connect - Parser-workflow is NOT running")
    print("       Start it with: cd parser-workflow && python main.py")
except Exception as e:
    print(f"[ERROR] {e}")

print()

# Test 2: Repo-AI
print("TEST 2: Repo-AI (http://localhost:5000)")
try:
    response = requests.get("http://localhost:5000/api/health", timeout=5)
    if response.status_code == 200:
        data = response.json()
        print("[OK] Repo-AI is running")
        print(f"     Status: {data.get('status')}")
        print(f"     Parser connection: {data.get('parser_workflow')}")
        print(f"     Active repo: {data.get('active_repository')}")
    else:
        print(f"[FAIL] Status {response.status_code}")
except requests.exceptions.ConnectionError:
    print("[FAIL] Cannot connect - Repo-AI is NOT running")
    print("       Start it with: cd repo-ai && python app.py")
except Exception as e:
    print(f"[ERROR] {e}")

print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print("\nBoth systems must be running for the platform to work.")
print("Use START_ALL_SYSTEMS.bat to launch both at once.")
print()

# Made with Bob
