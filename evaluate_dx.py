"""
Developer Experience (DX) evaluation script for Python dependency management tools.
This script evaluates common operations and captures error messages and behaviors.
"""

import os
import subprocess
import json
import tempfile
import shutil
from pathlib import Path

# Test scenarios for developer experience evaluation
DX_SCENARIOS = [
    {
        "name": "add_dependency",
        "description": "Add a new dependency",
        "commands": {
            "poetry": "poetry add pyyaml",
            "piptools": "echo 'pyyaml' >> requirements.in && pip-compile requirements.in && pip install -r requirements.txt",
            "uv": "uv pip install pyyaml",
            "make": "echo 'pyyaml' >> requirements.txt && make install"
        }
    },
    {
        "name": "remove_dependency",
        "description": "Remove a dependency",
        "commands": {
            "poetry": "poetry remove black",
            "piptools": "sed -i.bak '/black/d' requirements.in && pip-compile requirements.in && pip install -r requirements.txt",
            "uv": "uv pip uninstall -y black",
            "make": "sed -i.bak '/black/d' requirements.txt && make install"
        }
    },
    {
        "name": "install_specific_version",
        "description": "Install a specific version of a package",
        "commands": {
            "poetry": "poetry add requests==2.25.1",
            "piptools": "echo 'requests==2.25.1' >> requirements.in && pip-compile requirements.in && pip install -r requirements.txt",
            "uv": "uv pip install requests==2.25.1",
            "make": "echo 'requests==2.25.1' >> requirements.txt && make install"
        }
    },
    {
        "name": "resolve_conflict",
        "description": "Resolve a dependency conflict",
        "commands": {
            "poetry": "poetry add flask==2.0.0 werkzeug==2.0.0",
            "piptools": "echo 'flask==2.0.0' >> requirements.in && echo 'werkzeug==2.0.0' >> requirements.in && pip-compile requirements.in || echo 'Conflict detected'",
            "uv": "uv pip install flask==2.0.0 werkzeug==2.0.0 || echo 'Conflict detected'",
            "make": "echo 'flask==2.0.0' >> requirements.txt && echo 'werkzeug==2.0.0' >> requirements.txt && make install || echo 'Conflict detected'"
        }
    },
    {
        "name": "error_messages",
        "description": "Test error message clarity with invalid package",
        "commands": {
            "poetry": "poetry add nonexistentpackage123456789",
            "piptools": "echo 'nonexistentpackage123456789' >> requirements.in && pip-compile requirements.in",
            "uv": "uv pip install nonexistentpackage123456789",
            "make": "echo 'nonexistentpackage123456789' >> requirements.txt && make install"
        }
    },
    {
        "name": "upgrade_all",
        "description": "Upgrade all dependencies",
        "commands": {
            "poetry": "poetry update",
            "piptools": "pip-compile --upgrade requirements.in && pip install -r requirements.txt",
            "uv": "uv pip install --upgrade -r requirements.txt",
            "make": "pip install --upgrade -r requirements.txt"
        }
    }
]


def run_command(command, cwd=None, capture_error=True):
    """Run a shell command and return the output."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=120,  # 2 minutes timeout
        )
        return {
            "command": command,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        return {
            "command": command,
            "returncode": -1,
            "stdout": "",
            "stderr": "Command timed out after 120 seconds",
            "success": False,
        }
    except Exception as e:
        if capture_error:
            return {
                "command": command,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "success": False,
            }
        else:
            raise


def prepare_environment(tool, tmp_dir):
    """Prepare the environment for a tool."""
    # Copy necessary files
    for file in ["pyproject.toml", "requirements.in", "Makefile"]:
        if os.path.exists(file):
            shutil.copy(file, tmp_dir)
    
    # Create scripts directory
    os.makedirs(os.path.join(tmp_dir, "scripts"), exist_ok=True)
    script_path = os.path.join(tmp_dir, "scripts", f"install_{tool}.sh")
    shutil.copy(f"scripts/install_{tool}.sh", script_path)
    os.chmod(script_path, 0o755)  # Make executable
    
    # Run installation
    return run_command(f"./scripts/install_{tool}.sh", cwd=tmp_dir)


def evaluate_tool_dx(tool):
    """Evaluate the developer experience of a tool."""
    results = {
        "tool": tool,
        "scenarios": []
    }
    
    print(f"\n=== Evaluating DX for {tool} ===")
    
    # Create a temporary directory for this tool
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Prepare environment
        setup_result = prepare_environment(tool, tmp_dir)
        
        if not setup_result["success"]:
            print(f"  ❌ Failed to set up environment for {tool}")
            print(f"  Error: {setup_result['stderr']}")
            results["setup_error"] = setup_result["stderr"]
            return results
        
        # Run each scenario
        for scenario in DX_SCENARIOS:
            print(f"  Running scenario: {scenario['name']}")
            
            # Get the command for this tool
            command = scenario["commands"].get(tool)
            if not command:
                print(f"  ⚠️ No command defined for {tool} in scenario {scenario['name']}")
                continue
            
            # Activate the virtual environment if needed
            if "pip-compile" in command or "pip install" in command:
                if tool != "poetry":  # Poetry handles its own venv activation
                    command = f"source .venv/bin/activate && {command}"
            
            # Run the command
            result = run_command(command, cwd=tmp_dir)
            
            # Add result to the list
            scenario_result = {
                "name": scenario["name"],
                "description": scenario["description"],
                "command": command,
                "success": result["success"],
                "returncode": result["returncode"],
                "error": result["stderr"] if not result["success"] else None,
                "output": result["stdout"][:500] + "..." if len(result["stdout"]) > 500 else result["stdout"],
            }
            
            results["scenarios"].append(scenario_result)
            
            print(f"    {'✅ Success' if result['success'] else '❌ Failed'}")
    
    return results