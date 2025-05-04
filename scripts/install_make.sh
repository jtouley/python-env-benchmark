#!/bin/bash
set -euo pipefail

SCRIPT_DIR=$(dirname "$(realpath "$0")")
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")
cd "$PROJECT_ROOT"

# Ensure make is installed
if ! command -v make &> /dev/null; then
    echo "Installing make..."
    if command -v brew &> /dev/null; then
        brew install make
    else
        echo "Error: make command not found. Please install it manually."
        exit 1
    fi
fi

# Clean previous environment if it exists
rm -rf .venv

# Time the installation
echo "Running make installation..."
START=$(date +%s.%N)

# Install dependencies using make
make install

END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "Make installation completed in $DIFF seconds"

# Show installed packages
echo "Installed packages:"
.venv/bin/pip freeze

# Output environment hash for reproducibility check
echo "Environment hash:"
.venv/bin/pip freeze | sort | md5sum