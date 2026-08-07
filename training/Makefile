DATA_PATH ?= data/fetched/data.csv
MODEL_PATH ?= models/poland_used_cars_linear_regression.joblib
TEST_SIZE ?= 0.2
RANDOM_STATE ?= 42

.PHONY: help install fetch-data train all clean

help:
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ {printf "%-16s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install training dependencies
	uv sync

fetch-data: ## Download the latest Kaggle dataset version
	uv run python -m src.kaggle

format: ## Format code with Ruff and isort
	uv run --extra dev isort .
	uv run --extra dev ruff format .

lint: ## Run Ruff lint checks
	uv run --extra dev ruff check . --fix

train: ## Train the linear regression model
	uv run python -m src.train \
		--data-path $(DATA_PATH) \
		--model-path $(MODEL_PATH) \
		--test-size $(TEST_SIZE) \
		--random-state $(RANDOM_STATE)

all: fetch-data train ## Fetch dataset and train the model

clean: ## Remove generated training artifacts
	rm -rf models/*.joblib metrics/*.json
