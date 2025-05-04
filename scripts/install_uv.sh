#!/bin/bash
set -euo pipefail

SCRIPT_DIR=$(dirname "$(realpath "$0")")
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")
cd "$PROJECT_ROOT"

echo "Cleaning old environment..."
rm -rf .venv_uv
uv venv .venv_uv

source .venv_uv/bin/activate

# Manually install pip if missing
if ! command -v pip &> /dev/null; then
    echo "Bootstrapping pip..."
    curl -sS https://bootstrap.pypa.io/get-pip.py | python
fi

# Ensure requirements.txt exists
if [ ! -f requirements.txt ]; then
    echo "Generating basic requirements.txt..."
    cat > requirements.txt << EOF
pandas
numpy
requests
flask
scikit-learn
black
pytest
pytest-benchmark
EOF
fi

echo "Installing dependencies..."
START=$(date +%s.%N)
pip install -r requirements.txt
END=$(date +%s.%N)

DIFF=$(echo "$END - $START" | bc)
echo "✅ uv installation completed in $DIFF seconds"

echo "📦 Installed packages:"
pip freeze | sort

echo "🔐 Environment hash:"
if command -v md5sum &> /dev/null; then
    pip freeze | sort | md5sum
else
    pip freeze | sort | md5
fi

deactivate