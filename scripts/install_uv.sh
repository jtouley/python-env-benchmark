#!/bin/bash
set -euo pipefail

SCRIPT_DIR=$(dirname "$(realpath "$0")")
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")
cd "$PROJECT_ROOT"

# Ensure uv is installed
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    if command -v brew &> /dev/null; then
        brew install uv
    else
        curl -LsSf https://astral.sh/uv/install.sh | sh
    fi
fi

# Clean previous environment if it exists
rm -rf .venv

# Create and activate virtual environment
uv venv .venv

# Display uv version
uv --version

# Time the installation
echo "Running uv installation..."
START=$(date +%s.%N)

# Install dependencies
uv pip install -r requirements.txt

END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "uv installation completed in $DIFF seconds"

# Show installed packages
echo "Installed packages:"
.venv/bin/python -m pip freeze

# Output environment hash for reproducibility check
echo "Environment hash:"
.venv/bin/pip freeze | sort | md5sum