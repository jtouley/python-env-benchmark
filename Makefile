.PHONY: setup-venv install clean benchmark all

VENV_DIR = .venv
PYTHON = $(VENV_DIR)/bin/python
PIP = $(VENV_DIR)/bin/pip

all: setup-venv install

setup-venv:
	python3 -m venv $(VENV_DIR)

install: setup-venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

install-dev: install
	$(PIP) install pytest pytest-benchmark

clean:
	rm -rf $(VENV_DIR)
	rm -rf *.egg-info
	rm -rf dist
	rm -rf build
	rm -rf .pytest_cache
	rm -rf __pycache__
	rm -rf .coverage
	find . -name "*.pyc" -delete

benchmark: install-dev
	$(PYTHON) -m pytest test_benchmark.py -v

run-hyperfine:
	hyperfine --warmup 1 \
		--prepare 'rm -rf .venv' \
		'./scripts/install_make.sh' \
		'./scripts/install_poetry.sh' \
		'./scripts/install_piptools.sh' \
		'./scripts/install_uv.sh'