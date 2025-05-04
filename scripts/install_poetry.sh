#!/bin/bash
set -euo pipefail

SCRIPT_DIR=$(dirname "$(realpath "$0")")
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")
cd "$PROJECT_ROOT"

# Ensure poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "📦 Installing Poetry..."
    if command -v brew &> /dev/null; then
        brew install poetry
    else
        curl -sSL https://install.python-poetry.org | python3 -
    fi
fi

echo "🧹 Cleaning old environment..."
rm -rf .venv_poetry

echo "⚙️  Configuring Poetry to use in-project venv..."
poetry config virtualenvs.in-project true

# Ensure README exists
if [ ! -f README.md ]; then
    echo "📄 Creating basic README.md..."
    cat > README.md << EOF
# Python Dependency Benchmark
Testing Poetry dependency management
EOF
fi

# Create or ensure pyproject.toml exists
if [ ! -f pyproject.toml ]; then
    echo "📄 Creating basic pyproject.toml..."
    cat > pyproject.toml << EOF
[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"

[tool.poetry]
name = "py-dependency-benchmark"
version = "0.1.0"
description = "Benchmark for Python dependency management tools"
authors = ["Benchmark User <user@example.com>"]
readme = "README.md"

[tool.poetry.dependencies]
python = "^3.9"
pandas = "*"
numpy = "*"
requests = "*"
flask = "*"
scikit-learn = "*"
black = "*"
pytest = "*"
pytest-benchmark = "*"
EOF
fi

# Display Poetry version
poetry --version

# Time the install
echo "🚀 Installing dependencies..."
START=$(date +%s.%N)

poetry install --no-interaction --no-root

END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "✅ Poetry installation completed in $DIFF seconds"

# Show installed packages
echo "📦 Installed packages:"
poetry run pip freeze | sort

# Output environment hash
echo "🔐 Environment hash:"
if command -v md5sum &> /dev/null; then
    poetry run pip freeze | sort | md5sum
else
    poetry run pip freeze | sort | md5
fi