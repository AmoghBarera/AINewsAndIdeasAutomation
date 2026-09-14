.PHONY: setup run dry-run test clean help

help:
	@echo "Available commands:"
	@echo "  make setup     - Install dependencies"
	@echo "  make run       - Run the full pipeline"
	@echo "  make dry-run   - Run the full pipeline without sending emails"
	@echo "  make test      - Run tests (requires pytest)"
	@echo "  make clean     - Remove temporary python files and pycache"

setup:
	pip install -r requirements.txt

run:
	python main.py

dry-run:
	python main.py --dry-run

test:
	python -m pytest tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
