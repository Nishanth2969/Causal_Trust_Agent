.PHONY: setup run seed test

setup:
	python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

run:
	export FLASK_APP=app/server.py && flask run

seed:
	python3 -m app.seed

test:
	pytest -q

