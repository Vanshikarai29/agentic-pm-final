# AgentPM — Makefile
# Usage: make dev        → start both servers (dev mode)
#        make build      → build React + serve from FastAPI only
#        make test       → run backend tests
#        make install    → install all dependencies
#        make clean      → remove build artifacts

.PHONY: dev build test install clean

dev:
	@chmod +x start.sh && ./start.sh

build:
	@chmod +x build_and_serve.sh && ./build_and_serve.sh
	@echo ""
	@echo "Now run the single server:"
	@echo "  cd backend && source venv/bin/activate && uvicorn main:app --port 8000"

test:
	@cd backend && source venv/bin/activate && pytest tests/ -v

install:
	@cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
	@cd frontend && npm install

clean:
	@rm -rf backend/static backend/__pycache__ backend/agentic_pm.db
	@rm -rf frontend/build frontend/node_modules
	@echo "Cleaned."
