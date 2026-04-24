.PHONY: install quality format test check data api dashboard

install:
	python -m pip install -r requirements-dev.txt

quality:
	ruff check .
	black --check .

format:
	ruff check --fix .
	black .

test:
	python -m pytest

check: quality test

data:
	python -m app.generate_data

api:
	uvicorn app.api.main:app --reload

dashboard:
	streamlit run app/dashboard.py

