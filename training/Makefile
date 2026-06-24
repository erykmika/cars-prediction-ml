DATA_PATH ?= data/data.csv
MODEL_PATH ?= models/poland_used_cars_linear_regression.joblib
API_MODEL_DIR ?= ../api/models
API_MODEL_PATH ?= $(API_MODEL_DIR)/poland_used_cars_linear_regression.joblib
TEST_SIZE ?= 0.2
RANDOM_STATE ?= 42

.PHONY: help install fetch-data train copy-model all clean

help:
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ {printf "%-16s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install training dependencies
	uv sync

fetch-data: ## Download the latest Kaggle dataset version
	uv run python -m src.kaggle

format: ## Format code with Ruff and isort
	isort .
	uv run --extra dev ruff format .

lint: ## Run Ruff lint checks
	uv run --extra dev ruff check .

train: ## Train the linear regression model
	uv run python -m src.train \
		--data-path $(DATA_PATH) \
		--model-path $(MODEL_PATH) \
		--test-size $(TEST_SIZE) \
		--random-state $(RANDOM_STATE)

copy-model: ## Copy the trained model artifact into the API models directory
	mkdir -p $(API_MODEL_DIR)
	cp $(MODEL_PATH) $(API_MODEL_PATH)

all: train copy-model ## Train and publish the model to the API

clean: ## Remove generated training artifacts
	rm -rf models/*.joblib metrics/*.json
