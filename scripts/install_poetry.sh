#!/bin/bash
set -euo pipefail

SCRIPT_DIR=$(dirname "$(realpath "$0")")
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")
cd "$PROJECT_ROOT"

# Ensure poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "Installing poetry..."
    if command -v brew &> /dev/null; then
        brew install poetry
    else
        curl -sSL https://install.python-poetry.org | python3 -
    fi
fi

# Clean previous environment if it exists
rm -rf .venv

# Configure poetry to create virtualenv in project directory
poetry config virtualenvs.in-project true

# Display poetry version
poetry --version

# Time the installation
echo "Running poetry installation..."
START=$(date +%s.%N)

# Install dependencies
poetry install

END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "Poetry installation completed in $DIFF seconds"

# Show installed packages
echo "Installed packages:"
poetry run pip freeze

# Output environment hash for reproducibility check
echo "Environment hash:"
poetry run pip freeze | sort | md5sum

# Generate lock file if it doesn't exist
if [ ! -f poetry.lock ]; then
    echo "Creating poetry.lock file..."
    poetry lock
fi