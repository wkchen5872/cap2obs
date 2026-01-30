.PHONY: install build test clean

install:
	pip install -e .

test:
	pytest tests/

build:
	@chmod +x scripts/build.sh
	./scripts/build.sh

clean:
	rm -rf build dist *.spec .pytest_cache .coverage htmlcov cap2obs.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} +
