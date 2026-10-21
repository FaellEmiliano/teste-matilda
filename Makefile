.PHONY: setup backend frontend test build
setup:
	python -m venv .venv
	.venv/bin/pip install -r backend/requirements.txt
	cd frontend && npm ci
backend:
	.venv/bin/python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload
frontend:
	cd frontend && npm run dev
test:
	.venv/bin/python -m pytest backend/tests -q
build:
	cd frontend && npm run build
