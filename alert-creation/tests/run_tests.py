#!/usr/bin/env python3
"""
Test runner script for alert-creation system

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --unit             # Run only unit tests
    python run_tests.py --integration      # Run only integration tests
    python run_tests.py --api              # Run only API tests
    python run_tests.py --coverage         # Run with coverage report
    python run_tests.py --fast             # Skip slow tests
"""

import subprocess
import sys
import argparse
import os


def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}")
    print(f"Running: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ {description} - Success")
        if result.stdout:
            print(result.stdout)
    else:
        print(f"❌ {description} - Failed")
        if result.stderr:
            print(result.stderr)
        if result.stdout:
            print(result.stdout)
        return False
    
    return True


def main():
    parser = argparse.ArgumentParser(description="Run alert-creation tests")
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    parser.add_argument("--api", action="store_true", help="Run only API tests")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--fast", action="store_true", help="Skip slow tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--file", help="Run specific test file")
    
    args = parser.parse_args()
    
    # Change to the tests directory
    test_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(test_dir)
    
    # Base pytest command
    pytest_cmd = ["python", "-m", "pytest"]
    
    # Add verbosity
    if args.verbose:
        pytest_cmd.extend(["-v", "-s"])
    
    # Add coverage if requested
    if args.coverage:
        pytest_cmd.extend([
            "--cov=../",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov"
        ])
    
    # Add test selection markers
    if args.unit:
        pytest_cmd.extend(["-m", "unit"])
    elif args.integration:
        pytest_cmd.extend(["-m", "integration"])
    elif args.api:
        pytest_cmd.extend(["-m", "api"])
    
    # Skip slow tests if requested
    if args.fast:
        pytest_cmd.extend(["-m", "not slow"])
    
    # Run specific file if provided
    if args.file:
        pytest_cmd.append(args.file)
    
    # Run the tests
    success = run_command(pytest_cmd, "Running tests")
    
    if success and args.coverage:
        print("\n📊 Coverage report generated in htmlcov/index.html")
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
