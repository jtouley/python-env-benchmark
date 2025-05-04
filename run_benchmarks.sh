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
mkdir -p scripts benchmark_results benchmark_tmp
echo "✅ Created directory structure"

# Ensure all scripts are executable
chmod +x scripts/*.sh
echo "✅ Made scripts executable"

# Check for required tools
print_header "Checking dependencies"

check_command python3 "You can install Python from https://www.python.org/downloads/"
check_command pip "Should be installed with Python"

# Check for hyperfine with interactive prompt
if ! command -v hyperfine &> /dev/null; then
    echo "❌ hyperfine is not installed"
    echo "Hyperfine is recommended for accurate benchmarking."
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        read -p "Would you like to install hyperfine using Homebrew? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Installing hyperfine with Homebrew..."
            brew install hyperfine
            USE_HYPERFINE=true
        else
            USE_HYPERFINE=false
            echo "Skipping hyperfine benchmarks."
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        read -p "Would you like to install hyperfine? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Installing hyperfine with apt..."
            sudo apt update && sudo apt install -y hyperfine
            USE_HYPERFINE=true
        else
            USE_HYPERFINE=false
            echo "Skipping hyperfine benchmarks."
        fi
    else
        USE_HYPERFINE=false
        echo "Unsupported OS for automatic installation. Skipping hyperfine benchmarks."
        echo "To install manually:"
        echo "   - macOS: brew install hyperfine"
        echo "   - Ubuntu/Debian: sudo apt install hyperfine"
        echo "   - Others: see https://github.com/sharkdp/hyperfine#installation"
    fi
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
BENCHMARK_EXIT=$?

print_header "Testing reproducibility"
python test_reproducibility.py
REPRO_EXIT=$?

print_header "Evaluating developer experience" 
python evaluate_dx.py
DX_EXIT=$?

# Run hyperfine benchmarks if available
if [ "$USE_HYPERFINE" = true ]; then
    print_header "Running hyperfine benchmarks"
    
    # Ensure all required files exist
    touch requirements.txt requirements.in README.md
    
    # Prepare for hyperfine benchmark
    mkdir -p benchmark_tmp/{make,poetry,piptools,uv}
    
    # Copy necessary files to each directory
    for dir in benchmark_tmp/{make,poetry,piptools,uv}; do
        cp requirements.txt requirements.in README.md pyproject.toml Makefile $dir/
        mkdir -p $dir/scripts
        cp scripts/install_*.sh $dir/scripts/
        chmod +x $dir/scripts/*.sh
    done
    
    # Run hyperfine with --ignore-failure to ensure all tools are benchmarked
    hyperfine --warmup 1 \
        --ignore-failure \
        --export-json benchmark_results/hyperfine-results.json \
        --prepare 'rm -rf benchmark_tmp/make/.venv_make' \
        'cd benchmark_tmp/make && ./scripts/install_make.sh' \
        --prepare 'rm -rf benchmark_tmp/poetry/.venv_poetry' \
        'cd benchmark_tmp/poetry && ./scripts/install_poetry.sh' \
        --prepare 'rm -rf benchmark_tmp/piptools/.venv_piptools' \
        'cd benchmark_tmp/piptools && ./scripts/install_piptools.sh' \
        --prepare 'rm -rf benchmark_tmp/uv/.venv_uv' \
        'cd benchmark_tmp/uv && ./scripts/install_uv.sh'
    
    HYPERFINE_EXIT=$?
else
    HYPERFINE_EXIT=0
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