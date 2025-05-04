#!/bin/bash
set -euo pipefail

# Helper functions
print_header() {
    echo "========================================"
    echo "  $1"
    echo "========================================"
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        echo "❌ $1 could not be found. Please install it."
        if [ "$2" != "" ]; then
            echo "   $2"
        fi
        return 1
    fi
    return 0
}

# Create directory structure
mkdir -p scripts benchmark_results

# Ensure all scripts are executable
chmod +x scripts/*.sh

# Check for required tools
print_header "Checking dependencies"

check_command python3 "You can install Python from https://www.python.org/downloads/"
check_command pip "Should be installed with Python"

if ! check_command hyperfine "For macOS: brew install hyperfine, For Ubuntu: sudo apt install hyperfine"; then
    USE_HYPERFINE=false
    echo "ℹ️ Hyperfine not found. Will skip hyperfine benchmarks."
    echo "   To install on macOS: brew install hyperfine"
    echo "   To install on Ubuntu: sudo apt install hyperfine"
else
    USE_HYPERFINE=true
    echo "✅ Hyperfine found"
fi

# Set up virtual environment for the reporting tools
print_header "Setting up reporting environment"

# Create and activate virtual environment for reporting
REPORT_VENV="report_venv"
if [ -d "$REPORT_VENV" ]; then
    echo "Using existing virtual environment at $REPORT_VENV"
else
    echo "Creating new virtual environment at $REPORT_VENV"
    python3 -m venv $REPORT_VENV
fi

# Activate the virtual environment
source $REPORT_VENV/bin/activate

# Install Python dependencies for reporting
echo "Installing dependencies for reporting tools"
pip install --upgrade pip
pip install pandas matplotlib pytest pytest-benchmark

# Run the benchmarks
print_header "Running installation benchmarks"
python test_benchmark.py

print_header "Testing reproducibility"
python test_reproducibility.py

print_header "Evaluating developer experience"
python evaluate_dx.py

# Run hyperfine benchmarks if available
if [ "$USE_HYPERFINE" = true ]; then
    print_header "Running hyperfine benchmarks"
    hyperfine --warmup 1 \
        --export-json benchmark_results/hyperfine-results.json \
        --prepare 'rm -rf .venv' \
        './scripts/install_make.sh' \
        './scripts/install_poetry.sh' \
        './scripts/install_piptools.sh' \
        './scripts/install_uv.sh'
fi

# Generate the report
print_header "Generating benchmark report"
python generate_report.py

# Deactivate the virtual environment
deactivate

echo ""
echo "✅ Benchmarks completed!"
echo "   View the report at: benchmark_results/report.md"

# Optionally convert Markdown to other formats if pandoc is available
if command -v pandoc &> /dev/null; then
    print_header "Converting report to other formats"
    
    # Convert to HTML
    pandoc -s benchmark_results/report.md -o benchmark_results/report.html
    echo "   HTML report: benchmark_results/report.html"
    
    # Convert to PDF if available
    if pandoc --version | grep -q '+latex'; then
        pandoc benchmark_results/report.md -o benchmark_results/report.pdf
        echo "   PDF report: benchmark_results/report.pdf"
    fi
else
    echo ""
    echo "ℹ️ Tip: Install pandoc to convert the report to HTML/PDF:"
    echo "   brew install pandoc"
fi