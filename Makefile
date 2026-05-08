.PHONY: help install dev test lint deploy

help:
	@echo "Top-level commands:"
	@echo "  make install      Install backend + frontend deps"
	@echo "  make dev          Run backend + frontend dev servers (two terminals recommended)"
	@echo "  make test         Run all tests (backend + frontend)"
	@echo "  make lint         Lint everything"
	@echo "  make deploy       Deploy backend to Cloud Run + frontend to Firebase Hosting"

install:
	$(MAKE) -C backend install
	cd frontend && npm install

dev:
	@echo "Run in two terminals:"
	@echo "  Terminal 1: cd backend && make dev"
	@echo "  Terminal 2: cd frontend && npm run dev"

test:
	$(MAKE) -C backend test
	cd frontend && npm test --if-present

lint:
	$(MAKE) -C backend lint
	cd frontend && npm run lint --if-present

deploy:
	@echo "See README.md → Deployment section"
