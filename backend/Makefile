.PHONY: help install dev test lint format docker run-docker

VENV ?= .venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

help:
	@echo "Backend commands:"
	@echo "  make install      Create venv and install deps"
	@echo "  make dev          Run uvicorn dev server on :8080 with reload"
	@echo "  make test         Run pytest"
	@echo "  make lint         Run ruff lint"
	@echo "  make format       Run ruff format"
	@echo "  make docker       Build the production Docker image"

$(VENV):
	python3.12 -m venv $(VENV) || python3 -m venv $(VENV)
	$(PIP) install --upgrade pip

install: $(VENV)
	$(PIP) install -e ".[dev]"

dev:
	$(VENV)/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

test:
	$(VENV)/bin/pytest

lint:
	$(VENV)/bin/ruff check app tests
	$(VENV)/bin/ruff format --check app tests

format:
	$(VENV)/bin/ruff format app tests
	$(VENV)/bin/ruff check --fix app tests

docker:
	docker build -t promptwars-backend:local .

run-docker: docker
	docker run --rm -p 8080:8080 --env-file ../.env promptwars-backend:local
