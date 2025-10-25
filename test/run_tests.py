#!/usr/bin/env python3
"""Test runner for all API endpoints."""

import sys
import subprocess
from pathlib import Path

def run_tests():
    """Run all tests and generate coverage report."""
    print("🧪 Running comprehensive API tests...")
    print("=" * 50)
    
    # Test files to run
    test_files = [
        "test_api_endpoints.py",
        "test_user_endpoints.py", 
        "test_membership_endpoints.py"
    ]
    
    # Run tests with coverage
    cmd = [
        "python", "-m", "pytest",
        "-v",
        "--cov=src",
        "--cov-report=html",
        "--cov-report=term-missing",
        "--tb=short"
    ] + test_files
    
    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent, check=True)
        print("\n✅ All tests passed!")
        print("📊 Coverage report generated in htmlcov/index.html")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Tests failed with exit code {e.returncode}")
        return False

def run_specific_test(test_file: str):
    """Run a specific test file."""
    print(f"🧪 Running {test_file}...")
    print("=" * 50)
    
    cmd = ["python", "-m", "pytest", "-v", test_file]
    
    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent, check=True)
        print(f"\n✅ {test_file} passed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {test_file} failed with exit code {e.returncode}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific test file
        test_file = sys.argv[1]
        success = run_specific_test(test_file)
    else:
        # Run all tests
        success = run_tests()
    
    sys.exit(0 if success else 1)
