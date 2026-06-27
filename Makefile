run-full-pipeline:
	@echo "Running the full pipeline: fetch data, train model, and copy model to API, start the API container"
	$(MAKE) -C training all
	$(MAKE) -C api docker-run
