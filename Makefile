.PHONY: install test run-demo list-strategies web lint

install:
	pip install -e .

test:
	pytest tests/ -v

run-demo:
	python demo_walkthrough.py

list-strategies:
	python -m aura_safety.cli.main list-strategies

web:
	python -m aura_safety.cli.main web

lint:
	flake8 aura_safety tests --count --select=E9,F63,F7,F82 --show-source --statistics || true
