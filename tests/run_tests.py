#!/usr/bin/env python3
"""
Test runner script for the AI Interview Assistant.

This script provides convenient ways to run different types of tests
with proper setup and teardown.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

def run_command(cmd, description=""):
    """Run a command and handle errors."""
    print(f"\n{'='*50}")
    if description:
        print(f"🔍 {description}")
    print(f"Running: {' '.join(cmd)}")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(cmd, check=True, cwd=Path(__file__).parent)
        print(f"✅ {description or 'Command'} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description or 'Command'} failed with exit code {e.returncode}")
        return False

def run_unit_tests():
    """Run unit tests only."""
    cmd = ["python", "-m", "pytest", "unit/", "-m", "not slow", "--cov=backend/app"]
    return run_command(cmd, "Running unit tests")

def run_integration_tests():
    """Run integration tests only."""
    cmd = ["python", "-m", "pytest", "integration/", "--cov=backend/app"]
    return run_command(cmd, "Running integration tests")

def run_all_tests():
    """Run all tests."""
    cmd = ["python", "-m", "pytest", "--cov=backend/app"]
    return run_command(cmd, "Running all tests")

def run_fast_tests():
    """Run fast tests only (excluding slow markers)."""
    cmd = ["python", "-m", "pytest", "-m", "not slow", "--cov=backend/app"]
    return run_command(cmd, "Running fast tests")

def run_with_coverage():
    """Run tests with detailed coverage report."""
    cmd = ["python", "-m", "pytest", "--cov=backend/app", "--cov-report=html", "--cov-report=term-missing"]
    return run_command(cmd, "Running tests with coverage report")

def run_specific_test(test_path):
    """Run a specific test file or test function."""
    cmd = ["python", "-m", "pytest", test_path, "-v"]
    return run_command(cmd, f"Running specific test: {test_path}")

def check_dependencies():
    """Check if required test dependencies are installed."""
    print("🔍 Checking test dependencies...")
    
    required_packages = [
        "pytest",
        "pytest-asyncio",
        "pytest-mock",
        "httpx",
        "pytest-cov",
        "factory-boy"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Please install them with:")
        print("pip install -r backend/requirements.txt")
        return False
    
    print("\n✅ All test dependencies are installed")
    return True

def main():
    parser = argparse.ArgumentParser(
        description="Run tests for AI Interview Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                    # Run all tests
  python run_tests.py --unit            # Run unit tests only
  python run_tests.py --integration     # Run integration tests only
  python run_tests.py --fast            # Run fast tests only
  python run_tests.py --coverage        # Run with detailed coverage
  python run_tests.py --check-deps      # Check dependencies
  python run_tests.py --test unit/test_llm_service.py  # Run specific test
        """
    )
    
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--fast", action="store_true", help="Run fast tests only")
    parser.add_argument("--coverage", action="store_true", help="Run with detailed coverage report")
    parser.add_argument("--check-deps", action="store_true", help="Check test dependencies")
    parser.add_argument("--test", help="Run specific test file or function")
    
    args = parser.parse_args()
    
    # Change to tests directory
    os.chdir(Path(__file__).parent)
    
    success = True
    
    if args.check_deps:
        success = check_dependencies()
    elif args.test:
        success = run_specific_test(args.test)
    elif args.unit:
        success = run_unit_tests()
    elif args.integration:
        success = run_integration_tests()
    elif args.fast:
        success = run_fast_tests()
    elif args.coverage:
        success = run_with_coverage()
    else:
        # Check dependencies first
        if not check_dependencies():
            sys.exit(1)
        
        # Run all tests by default
        success = run_all_tests()
    
    if success:
        print("\n🎉 All tests completed successfully!")
        if args.coverage or not any([args.unit, args.integration, args.fast, args.test]):
            print("📊 Coverage report generated in htmlcov/index.html")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()