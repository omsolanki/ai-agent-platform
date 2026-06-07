.PHONY: install dev test docker-up docker-down lint example

install:
	pip install -r requirements.txt

dev:
	uvicorn app.api.main:app --reload --port 8000

test:
	pytest tests/ -v

docker-up:
	cd docker && docker-compose up -d

docker-down:
	cd docker && docker-compose down

lint:
	ruff check app/ tests/

example:
	python examples/run_workflow.py

diagrams:
	chmod +x diagrams/render.sh && ./diagrams/render.sh
