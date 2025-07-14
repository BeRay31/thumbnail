#!/usr/bin/env python3
import subprocess
import sys
import os

def run_tests():
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/", "-v", "--tb=short", "--disable-warnings"
    ]
    
    print("Running tests...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 50)
    
    result = subprocess.run(cmd, capture_output=False)
    
    print("\n" + "=" * 50)
    if result.returncode == 0:
        print("All tests passed!")
    else:
        print("Some tests failed!")
        
    return result.returncode

if __name__ == "__main__":
    sys.exit(run_tests())
