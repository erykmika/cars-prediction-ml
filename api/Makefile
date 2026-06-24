IMAGE_NAME ?= cars-prediction-api
CONTAINER_NAME ?= cars-prediction-api
PORT ?= 8000
MODEL_PATH ?= models/poland_used_cars_linear_regression.joblib

.PHONY: help install test lint format docker-build docker-run docker-stop

help:
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ {printf "%-16s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install local development dependencies
	uv sync --extra dev

test: ## Run the test suite
	uv run --extra dev pytest -q

lint: ## Run Ruff lint checks
	uv run --extra dev ruff check .

format: ## Format code with Ruff and isort
	isort .
	uv run --extra dev ruff format .

docker-build: ## Build the Docker image
	docker build -t $(IMAGE_NAME) .

docker-run: docker-build ## Run the API container
	docker run --rm \
		--name $(CONTAINER_NAME) \
		-p $(PORT):8000 \
		-e MODEL_PATH=$(MODEL_PATH) \
		$(IMAGE_NAME)

docker-stop: ## Stop the running API container
	-docker stop $(CONTAINER_NAME)
