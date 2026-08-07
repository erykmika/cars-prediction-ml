run-full-pipeline:
	@echo "Running the full pipeline: fetch data, train model, and copy model to API, start the API + DB stack"
	$(MAKE) -C training all
	$(MAKE) -C api docker-compose-up
	@echo "Waiting for the API to start..."
	sleep 10
	$(MAKE) -C api health-check

docker-compose-up:
	$(MAKE) -C api docker-compose-up

docker-compose-down:
	$(MAKE) -C api docker-compose-down

docker-compose-logs:
	$(MAKE) -C api docker-compose-logs

format-all:
	@echo "Formatting all code"
	$(MAKE) -C training format
	$(MAKE) -C api format

lint-all:
	@echo "Linting all code"
	$(MAKE) -C training lint
	$(MAKE) -C api lint

check-all:
	@echo "Checking (formatting and linting) all code"
	$(MAKE) -C training format
	$(MAKE) -C training lint
	$(MAKE) -C api format
	$(MAKE) -C api lint
	$(MAKE) -C api test
