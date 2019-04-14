setup:
	./scripts/setup.sh

clean:
	find blaze tests -name "*.pyo" -exec rm -rf "{}" \+
	find blaze tests -name "*.pyc" -exec rm -rf "{}" \+
	find blaze tests -name "__pycache__"  -exec rm -rf "{}" \+
	rm -rf .coverage htmlcov .pytest_cache *.egg-info

lint:
	pylint blaze

test:
	pytest --cov=blaze tests
	coverage html

.PHONY: setup clean lint test
