# Python Dependency Management Benchmark

A comprehensive benchmarking framework for comparing Python dependency management tools: uv, poetry, pip-tools, and Makefile-based solutions.

## Overview

This project provides a controlled environment for evaluating and comparing different Python dependency management approaches. It measures:

- **Speed**: Install and lock time (cold and warm runs)
- **Reproducibility**: Environment consistency across machines/runs
- **Developer Experience (DX)**: Ease of use, error messages, common workflows
- **CI/CD Integration**: Performance in continuous integration environments
- **Extensibility/Maintainability**: Long-term maintainability

## Tools Evaluated

- **uv**: A new, extremely fast Python package installer and resolver
- **Poetry**: A modern dependency management and packaging tool
- **pip-tools**: Generate and synchronize pip requirements files
- **Makefile/Scripts**: Traditional approach using plain requirements.txt and Make

## Setup Requirements

- macOS or Linux (tested on macOS M1 and Ubuntu)
- Python 3.10+
- Recommended global tools (installed via Homebrew or apt):
  - **hyperfine**: For high-resolution benchmarking
  - **pandoc**: For report format conversion (optional)
  - **make**: For the Makefile-based approach

The project uses virtual environments to isolate dependencies:
- Each tool's installation script creates its own `.venv` environment for testing
- The main benchmarking script creates a separate `report_venv` for reporting tools

## Installation

Clone the repository and set up the benchmarking environment:

```bash
# Clone the repository
git clone https://github.com/your-username/python-dependency-benchmark.git
cd python-dependency-benchmark

# Make scripts executable
chmod +x scripts/*.sh

# Install hyperfine for high-resolution benchmarking (optional)
# On macOS:
brew install hyperfine
# On Ubuntu:
sudo apt-get install hyperfine
```

## Running Benchmarks

### Quick Comparison with Hyperfine

```bash
# Run a quick benchmark comparing all tools
hyperfine --warmup 1 \
  --prepare 'rm -rf .venv' \
  './scripts/install_make.sh' \
  './scripts/install_poetry.sh' \
  './scripts/install_piptools.sh' \
  './scripts/install_uv.sh'
```

### Comprehensive Benchmarks

```bash
# Run detailed installation benchmarks
python test_benchmark.py

# Test reproducibility
python test_reproducibility.py

# Evaluate developer experience
python evaluate_dx.py
```

### CI/CD Benchmarks

The project includes GitHub Actions workflows that run the benchmarks in a controlled CI environment. Push to the repository to trigger the workflow or run it manually from the Actions tab.

## Results

After running the benchmarks, several JSON files will be generated:

- `installation_benchmark_results.json`: Installation speed results
- `reproducibility_results.json`: Environment consistency results
- `dx_evaluation_results.json`: Developer experience evaluation
- `.pytest_benchmark_results.json`: Pytest benchmark results (import speed)

## Analyzing Results

The benchmarks automatically generate a comprehensive Markdown report:

```bash
# Generate a summary report
python generate_report.py
```

This creates:
- `benchmark_results/report.md` - A detailed Markdown report with analysis
- Charts in the `benchmark_results/` directory

If you have [pandoc](https://pandoc.org/) installed, the `run_benchmarks.sh` script will also convert the report to HTML and PDF formats.

```bash
# Install pandoc (optional)
brew install pandoc

# Convert the report manually
pandoc -s benchmark_results/report.md -o benchmark_results/report.html
```

## Project Structure

```
benchmark-python-tools/
├── pyproject.toml       # Used by both poetry and uv
├── requirements.in      # For pip-tools
├── scripts/
│   ├── install_make.sh
│   ├── install_poetry.sh
│   ├── install_uv.sh
│   └── install_piptools.sh
├── Makefile             # For manual testing
├── test_benchmark.py    # Installation benchmark
├── test_reproducibility.py # Reproducibility testing
├── evaluate_dx.py       # Developer experience evaluation
├── .github/workflows/
│   └── benchmark.yml    # CI for consistent runtime testing
└── README.md
```

## Customizing the Benchmark

You can customize the benchmark by:

1. Modifying `pyproject.toml` and `requirements.in` to test different packages
2. Adding new scenarios to the DX evaluation
3. Creating additional benchmarks for specific workflows

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- The [uv](https://github.com/astral-sh/uv) project
- [Poetry](https://python-poetry.org/)
- [pip-tools](https://github.com/jazzband/pip-tools)
- [hyperfine](https://github.com/sharkdp/hyperfine) benchmarking tool