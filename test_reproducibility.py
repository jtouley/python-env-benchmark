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
import re
from pathlib import Path
from datetime import datetime

TOOLS = ["make", "poetry", "piptools", "uv"]
RESULTS_DIR = Path("benchmark_results")
RAW_DIR = RESULTS_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)


def run_command(command, cwd=None):
    """Run a shell command and return the output."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=180,  # 3-minute timeout
        )
        return {
            "command": command,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.TimeoutExpired:
        print(f"Command timed out after 180 seconds: {command}")
        return {
            "command": command,
            "returncode": -1,
            "stdout": "",
            "stderr": "Command timed out after 180 seconds",
        }


def extract_hash_from_output(stdout_text):
    """Extract an MD5 hash from command output."""
    # Look for a line with "Environment hash:" or "🔐 Environment hash:" followed by a hash
    hash_pattern = re.search(r'(?:🔐 )?Environment hash:[\r\n\s]*([a-f0-9]{32})', stdout_text)
    if hash_pattern:
        return hash_pattern.group(1)
    
    # If not found, look for any MD5 hash in the output (32 hexadecimal characters)
    hash_pattern = re.search(r'\b([a-f0-9]{32})\b', stdout_text)
    if hash_pattern:
        return hash_pattern.group(1)
    
    return None


def get_env_hash_from_venv(venv_dir):
    """Get a hash of the installed packages in the virtual environment."""
    # Account for different venv naming schemes
    venv_paths = [
        venv_dir,
        venv_dir.replace(".venv", f".venv_{os.path.basename(os.path.dirname(venv_dir))}"),
        os.path.join(os.path.dirname(venv_dir), f".venv_{os.path.basename(os.path.dirname(venv_dir))}")
    ]
    
    for path in venv_paths:
        if os.path.exists(path):
            python_path = os.path.join(path, "bin", "python")
            if os.path.exists(python_path):
                result = subprocess.run(
                    f"{python_path} -m pip freeze | sort",
                    shell=True,
                    capture_output=True,
                    text=True,
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    # Create a hash of the sorted package list
                    return hashlib.md5(result.stdout.encode()).hexdigest()
    
    return None


def test_tool_reproducibility(tool, iterations=3):
    """
    Test reproducibility of a tool by creating multiple environments
    and comparing their package hashes.
    """
    results = []
    hashes = []
    
    print(f"\n=== Testing reproducibility of {tool} ===")
    
    # Ensure directories exist
    for file in ["pyproject.toml", "requirements.in", "Makefile"]:
        if not os.path.exists(file):
            print(f"Warning: {file} does not exist")
    
    if not os.path.exists("scripts"):
        print("Warning: scripts directory does not exist")
        os.makedirs("scripts", exist_ok=True)
    
    script_path = f"scripts/install_{tool}.sh"
    if not os.path.exists(script_path):
        print(f"Warning: {script_path} does not exist")
    
    # Create multiple environments
    for i in range(iterations):
        print(f"  Iteration {i+1}/{iterations}...")
        
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Copy necessary files
            for file in ["pyproject.toml", "requirements.in", "requirements.txt", "Makefile", "README.md"]:
                if os.path.exists(file):
                    shutil.copy(file, tmp_dir)
                else:
                    # Create the file if it doesn't exist
                    with open(os.path.join(tmp_dir, file), 'w') as f:
                        if file == "requirements.txt":
                            f.write("# Core dependencies\npandas\nnumpy\nrequests\nflask\nscikit-learn\nblack\n\n# Testing\npytest\npytest-benchmark\n")
                        elif file == "requirements.in":
                            f.write("# Core dependencies\npandas\nnumpy\nrequests\nflask\nscikit-learn\nblack\n\n# Testing\npytest\npytest-benchmark\n")
                        elif file == "README.md":
                            f.write("# Python Dependency Benchmark\nTesting dependency management tools\n")
                        elif file == "pyproject.toml":
                            f.write('[build-system]\nrequires = ["poetry-core>=1.0.0"]\nbuild-backend = "poetry.core.masonry.api"\n\n[tool.poetry]\nname = "py-dependency-benchmark"\nversion = "0.1.0"\ndescription = "Benchmark for Python dependency management tools"\nauthors = ["Your Name <your.email@example.com>"]\nreadme = "README.md"\n\n[tool.poetry.dependencies]\npython = "^3.10"\npandas = "*"\nnumpy = "*"\nrequests = "*"\nflask = "*"\nscikit-learn = "*"\nblack = "*"\npytest = "*"\npytest-benchmark = "*"\n')
            
            # Create scripts directory
            os.makedirs(os.path.join(tmp_dir, "scripts"), exist_ok=True)
            dest_script_path = os.path.join(tmp_dir, "scripts", f"install_{tool}.sh")
            if os.path.exists(script_path):
                shutil.copy(script_path, dest_script_path)
                os.chmod(dest_script_path, 0o755)  # Make executable
            else:
                print(f"  Error: Cannot find {script_path}")
                continue
            
            # Run installation
            result = run_command(f"./scripts/install_{tool}.sh", cwd=tmp_dir)
            results.append(result)
            
            # PRIMARY CHANGE: First try to extract hash from command output
            env_hash = extract_hash_from_output(result["stdout"])
            
            # If not found in output, fall back to calculating it from the venv
            if not env_hash:
                # Try both standard .venv and tool-specific .venv_tool paths
                tool_specific_venv = os.path.join(tmp_dir, f".venv_{tool}")
                standard_venv = os.path.join(tmp_dir, ".venv")
                
                if os.path.exists(tool_specific_venv):
                    env_hash = get_env_hash_from_venv(tool_specific_venv)
                elif os.path.exists(standard_venv):
                    env_hash = get_env_hash_from_venv(standard_venv)
            
            hashes.append(env_hash)
            print(f"    Environment hash: {env_hash}")
    
    # Check if all hashes are the same and none are None
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
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Test reproducibility of each tool
    for tool in TOOLS:
        results[tool] = test_tool_reproducibility(tool)
    
    # Save results to a JSON file with timestamp
    results_file = RAW_DIR / f"reproducibility_results_{timestamp}.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    
    # Also save to the standard location for backward compatibility
    with open("reproducibility_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print("\n=== Reproducibility Summary ===")
    for tool, result in results.items():
        emoji = "✅" if result['reproducible'] else "❌"
        print(f"{tool}: {emoji} {'Reproducible' if result['reproducible'] else 'Not reproducible'}")
    
    print(f"\nResults saved to: {results_file}")


if __name__ == "__main__":
    main()