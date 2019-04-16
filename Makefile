setup:
	./scripts/setup.sh

proto:
	python -m grpc_tools.protoc \
		--grpc_python_out=$(shell pwd)/blaze/proto \
		--python_out=$(shell pwd)/blaze/proto \
		-I $(shell pwd)/proto \
		$(shell pwd)/proto/*
	for f in blaze/proto/*_grpc.py; \
		do sed -i '' -E 's|^(import.*_pb2.*)|from . \1|' $$f; \
	done

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

.PHONY: setup proto clean lint test
