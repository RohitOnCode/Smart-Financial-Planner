.PHONY: init test lint format ci

    init:
	python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt -r requirements-dev.txt

    test:
	pytest -q