install:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -e '.[dev]' && playwright install chromium

test:
	PYTHONPATH=src pytest -q

demo:
	PYTHONPATH=. python -m uvicorn demo_app.app:app --host 127.0.0.1 --port 8000

discover:
	PYTHONPATH=src python -m cua.cli discover --url http://127.0.0.1:8000 --goal "Look up member 12345 and read their current savings balance" --output evidence/discovery-artifact.json --log evidence/discovery.log

replay:
	PYTHONPATH=src python -m cua.cli replay --artifact evidence/discovery-artifact.json --url http://127.0.0.1:8000 --member-id 12345 --log evidence/replay-success.log
