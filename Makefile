.PHONY: install run api test docker
install:
	pip install -r requirements.txt
run:
	streamlit run app/dashboard.py
api:
	uvicorn api.main:app --reload
test:
	pytest -q
docker:
	docker compose up --build

