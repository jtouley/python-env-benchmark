"""
Benchmark tests for evaluating Python dependency management tools.
This script measures the performance of common operations.
"""

import os
import subprocess
import time
import pytest
import json
import platform
import sys
from pathlib import Path


def get_system_info():
    """Gather system information for benchmarking context."""
    return {
        "platform": platform.system(),
        "platform_release": platform.release(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "cpus": os.cpu_count(),
    }


def run_command(command, cwd=None):
    """Run a shell command and return the output."""
    start_time = time.time()
    result = subprocess.run(
        command,
        shell=True,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    end_time = time.time()
    
    return {
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "execution_time": end_time - start_time,
    }


def test_import_dependencies(benchmark):
    """Test importing common dependencies for performance."""
    code = """
import pandas
import numpy
import requests
import flask
import sklearn
import black
    """
    
    def import_deps():
        exec(code)
    
    # Run the benchmark
    result = benchmark(import_deps)
    
    # Additional assertions can be added here
    assert result is not None


def test_installation_speed(tmp_path):
    """
    Test the installation speed of each tool.
    This is not run with pytest-benchmark as it involves subprocess calls.
    """
    results = {}
    tools = ["make", "poetry", "piptools", "uv"]
    
    for tool in tools:
        # Create a clean directory for each test
        test_dir = tmp_path / tool
        test_dir.mkdir()
        
        # Copy necessary files
        subprocess.run(f"cp pyproject.toml requirements.in Makefile {test_dir}", shell=True)
        subprocess.run(f"mkdir -p {test_dir}/scripts", shell=True)
        subprocess.run(f"cp scripts/install_{tool}.sh {test_dir}/scripts/", shell=True)
        subprocess.run(f"chmod +x {test_dir}/scripts/install_{tool}.sh", shell=True)
        
        # Run the installation
        print(f"Testing {tool} installation...")
        result = run_command(f"./scripts/install_{tool}.sh", cwd=test_dir)
        results[tool] = result
        
        print(f"{tool} completed in {result['execution_time']:.2f}s")
        
        if result["returncode"] != 0:
            print(f"Error running {tool}:")
            print(result["stderr"])
    
    # Save results to a JSON file
    with open("installation_benchmark_results.json", "w") as f:
        json.dump({
            "system_info": get_system_info(),
            "results": {k: {**v, "stdout": v["stdout"][:500] + "..." if len(v["stdout"]) > 500 else v["stdout"]} 
                      for k, v in results.items()}
        }, f, indent=2)
    
    # Print summary
    print("\nInstallation Speed Summary:")
    for tool, result in sorted(results.items(), key=lambda x: x[1]["execution_time"]):
        print(f"{tool}: {result['execution_time']:.2f}s")


if __name__ == "__main__":
    # Run the installation benchmark directly
    test_installation_speed(Path("./benchmark_tmp"))