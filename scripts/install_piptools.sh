#!/bin/bash
set -euo pipefail

SCRIPT_DIR=$(dirname "$(realpath "$0")")
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")
cd "$PROJECT_ROOT"

# Clean previous environment if it exists
rm -rf .venv

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install pip-tools
pip install pip-tools

# Compile requirements if requirements.txt doesn't exist or is older than requirements.in
if [ ! -f requirements.txt ] || [ requirements.in -nt requirements.txt ]; then
    echo "Compiling requirements.txt from requirements.in..."
    pip-compile --output-file=requirements.txt requirements.in
fi

# Display pip-tools version
pip-compile --version

# Time the installation
echo "Running pip-tools installation..."
START=$(date +%s.%N)

# Install dependencies
pip install -r requirements.txt

END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "pip-tools installation completed in $DIFF seconds"

# Show installed packages
echo "Installed packages:"
pip freeze

# Output environment hash for reproducibility check
echo "Environment hash:"
pip freeze | sort | md5sum