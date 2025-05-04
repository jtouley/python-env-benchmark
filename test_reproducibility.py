"""
Test script to evaluate reproducibility of different Python dependency management tools.
This script creates multiple environments with the same tool and checks for consistency.
"""

import os
import subprocess
import tempfile
import shutil
import json
import hashlib
from pathlib import Path

TOOLS = ["make", "poetry", "piptools", "uv"]


def run_command(command, cwd=None):
    """Run a shell command and return the output."""
    result = subprocess.run(
        command,
        shell=True,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    return {
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def get_env_hash(venv_dir):
    """Get a hash of the installed packages in the virtual environment."""
    if not os.path.exists(venv_dir):
        return None
    
    python_path = os.path.join(venv_dir, "bin", "python")
    result = subprocess.run(
        f"{python_path} -m pip freeze | sort",
        shell=True,
        capture_output=True,
        text=True,
    )
    
    if result.returncode != 0:
        return None
    
    # Create a hash of the sorted package list
    return hashlib.md5(result.stdout.encode()).hexdigest()


def test_tool_reproducibility(tool, iterations=3):
    """
    Test reproducibility of a tool by creating multiple environments
    and comparing their package hashes.
    """
    results = []
    hashes = []
    
    print(f"\n=== Testing reproducibility of {tool} ===")
    
    # Create multiple environments
    for i in range(iterations):
        print(f"  Iteration {i+1}/{iterations}...")
        
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Copy necessary files
            for file in ["pyproject.toml", "requirements.in", "Makefile"]:
                shutil.copy(file, tmp_dir)
            
            # Create scripts directory
            os.makedirs(os.path.join(tmp_dir, "scripts"), exist_ok=True)
            script_path = os.path.join(tmp_dir, "scripts", f"install_{tool}.sh")
            shutil.copy(f"scripts/install_{tool}.sh", script_path)
            os.chmod(script_path, 0o755)  # Make executable
            
            # Run installation
            result = run_command(f"./scripts/install_{tool}.sh", cwd=tmp_dir)
            results.append(result)
            
            # Get environment hash
            env_hash = get_env_hash(os.path.join(tmp_dir, ".venv"))
            hashes.append(env_hash)
            
            print(f"    Environment hash: {env_hash}")
    
    # Check if all hashes are the same
    is_reproducible = len(set(hashes)) == 1 and None not in hashes
    
    print(f"  Reproducible: {is_reproducible}")
    
    return {
        "tool": tool,
        "reproducible": is_reproducible,
        "hashes": hashes,
        "results": [
            {
                "returncode": r["returncode"],
                "error": r["stderr"] if r["returncode"] != 0 else None,
            }
            for r in results
        ],
    }


def main():
    results = {}
    
    # Test reproducibility of each tool
    for tool in TOOLS:
        results[tool] = test_tool_reproducibility(tool)
    
    # Save results to a JSON file
    with open("reproducibility_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print("\n=== Reproducibility Summary ===")
    for tool, result in results.items():
        print(f"{tool}: {'✅ Reproducible' if result['reproducible'] else '❌ Not reproducible'}")


if __name__ == "__main__":
    main()