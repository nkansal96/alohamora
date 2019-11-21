setup:
	./scripts/setup.sh

http2push:
	docker build -t http2push -f tools/capture_har/Dockerfile .

tree_diff:
	docker build -t tree_diff -f tools/tree_diff/Dockerfile .

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

format:
	black --line-length 120 --target-version py36 --exclude '.*_pb2.*' blaze tests scripts

check-format:
	black --line-length 120 --target-version py36 --exclude '.*_pb2.*' --check blaze tests scripts

test:
	pytest --cov=blaze -p no:warnings
	coverage html

test-ci:
	CI=true pytest --cov=blaze -p no:warnings

.PHONY: setup proto clean lint format check-format test test-ci
