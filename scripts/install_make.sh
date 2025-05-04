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

echo "Cleaning old environment..."
rm -rf .venv_make

# Ensure requirements.txt exists
if [ ! -f requirements.txt ]; then
    echo "Creating basic requirements.txt..."
    cat > requirements.txt << EOF
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

# Create a custom Makefile for our benchmark
cat > Makefile.benchmark << EOF
.PHONY: setup-venv install clean benchmark all

VENV_DIR = .venv_make
PYTHON = \$(VENV_DIR)/bin/python
PIP = \$(VENV_DIR)/bin/pip

all: setup-venv install

setup-venv:
	python3 -m venv \$(VENV_DIR)

install: setup-venv
	\$(PIP) install --upgrade pip
	\$(PIP) install -r requirements.txt

clean:
	rm -rf \$(VENV_DIR)
EOF

# Display make version
make --version

# Time the installation
echo "Installing dependencies..."
START=$(date +%s.%N)

# Run make install using our benchmark-specific Makefile
make -f Makefile.benchmark install

END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "✅ Make installation completed in $DIFF seconds"

# Show installed packages
echo "📦 Installed packages:"
.venv_make/bin/pip freeze | sort

# Output environment hash for reproducibility check
echo "🔐 Environment hash:"
if command -v md5sum &> /dev/null; then
    .venv_make/bin/pip freeze | sort | md5sum
else
    # For macOS which uses md5 instead of md5sum
    .venv_make/bin/pip freeze | sort | md5
fi