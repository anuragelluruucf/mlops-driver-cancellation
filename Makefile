PY ?= .venv/bin/python
.PHONY: all setup data train gate test serve smoke docker tf-check clean

all: setup data train gate test   ## one command: make

setup:
	test -d .venv || python3 -m venv .venv
	.venv/bin/pip install -q -r requirements-dev.txt

data:
	$(PY) -m src.data

train:
	$(PY) -m src.train

gate:
	$(PY) -m src.gate

test:
	$(PY) -m pytest -q

serve:
	$(PY) -m uvicorn app.main:app --port 8080

smoke:
	./scripts/smoke.sh http://localhost:8080

docker:
	docker build -t driver-cancellation-risk . && docker run --rm -p 8080:8080 driver-cancellation-risk

tf-check:
	cd terraform && terraform fmt -check && terraform init -backend=false -input=false && terraform validate

clean:
	rm -rf registry data/*.csv .pytest_cache
