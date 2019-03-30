setup:
	./setup.sh

clean:
	find blaze tests -name "*.pyo" -exec rm -rf "{}" \+
	find blaze tests -name "*.pyc" -exec rm -rf "{}" \+
	find blaze tests -name "__pycache__"  -exec rm -rf "{}" \+

test:
	pytest tests

.PHONY: setup clean test
