run-full-pipeline:
	@echo "Running the full pipeline: fetch data, train model, and copy model to API, start the API container"
	$(MAKE) -C training all
	$(MAKE) -C api docker-run
	echo "Waiting for the API to start..."
	sleep 3
	$(MAKE) -C api health-check
