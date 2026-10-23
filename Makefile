.PHONY: help install start-target stop-target backend frontend demo test

PYTHON := .tools/uv run --directory backend python3
PYTEST := .tools/uv run --directory backend pytest

help:
	@echo "CyberRanger Commands:"
	@echo "  make install       - Install backend and frontend dependencies"
	@echo "  make start-target  - Start local DVWA container via OrbStack"
	@echo "  make stop-target   - Stop local DVWA container"
	@echo "  make backend       - Start FastAPI backend server (port 8000)"
	@echo "  make frontend      - Start Vite frontend dev server (port 5173)"
	@echo "  make test          - Run backend automated test suite"
	@echo "  make demo          - Run 20-round end-to-end autonomous session"

install:
	@echo "Setting up backend..."
	cd backend && ../.tools/uv sync
	@echo "Setting up frontend..."
	cd frontend && npm install

start-target:
	@docker rm -f dvwa 2>/dev/null || true
	@docker run -d --name dvwa --platform linux/amd64 -p 127.0.0.1:8080:80 vulnerables/web-dvwa
	@echo "Waiting for DVWA container initialization..."
	@sleep 5

stop-target:
	@docker stop dvwa 2>/dev/null || true

test:
	$(PYTEST) tests/ -v

backend:
	$(PYTHON) -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

frontend:
	cd frontend && npm run dev

demo:
	$(PYTHON) scripts/demo.py --rounds 20 $(if $(SEED),--seed $(SEED),) $(if $(filter 1 true,$(NO_LLM)),--no-llm,)
