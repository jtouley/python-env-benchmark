#!/bin/bash
set -euo pipefail
SCRIPT_DIR=$(dirname "$(realpath "$0")")
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")
cd "$PROJECT_ROOT"

echo "Cleaning old environment..."
rm -rf .venv_piptools

# Create virtual environment
python3 -m venv .venv_piptools
source .venv_piptools/bin/activate

# Ensure pip is up-to-date and pip-tools is installed
pip install --upgrade pip
pip install pip-tools

# Ensure requirements.in exists
if [ ! -f requirements.in ]; then
    echo "Creating basic requirements.in..."
    cat > requirements.in << EOF
# Core dependencies
pandas
numpy
requests
flask
scikit-learn
black

# Testing
pytest
pytest-benchmark
EOF
fi

# Time the installation
echo "Installing dependencies..."
START=$(date +%s.%N)

# Compile requirements.in to requirements.txt
echo "Compiling requirements.in to requirements.txt..."
pip-compile --output-file=requirements.txt requirements.in

# Install from compiled requirements
pip install -r requirements.txt

END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "✅ Pip-tools installation completed in $DIFF seconds"

# Show installed packages
echo "📦 Installed packages:"
pip freeze | sort

# Output environment hash for reproducibility check
echo "🔐 Environment hash:"
if command -v md5sum &> /dev/null; then
    pip freeze | sort | md5sum
else
    # For macOS which uses md5 instead of md5sum
    pip freeze | sort | md5
fi

deactivate