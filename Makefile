.PHONY: install pre-build build black pycodestyle update-wiki

## @CI_actions Installs the checked out version of the code to your poetry managed venv
install:
	poetry install --without dev

install-dev:
	poetry install 

## @CI_actions Runs code quality checks
pre-build: black unit-tests
	rm setup.py || echo "There was no setup.py"
	poetry show --no-dev | awk '{print "poetry add "$$1"=="$$2}' | sort | sh

## @CI_actions Builds the project into an sdist
build:
	poetry build -f sdist

## @Code_quality Runs black on the checked out code
black:
	poetry run black **/*.py

## @Code_quality Runs pycodestyle on the the checked out code
pycodestyle:
	poetry run pycodestyle --statistics -qq uk_bin_collection

## @Testing runs unit tests
integration-tests:
	# Ensure directory exists
	mkdir -p build/$(matrix)/integration-test-results

	# Turn off "exit on error" so we can capture the code
	set +e; \
	if [ -z "$(councils)" ]; then \
		poetry run pytest uk_bin_collection/tests/step_defs/ \
			-n logical \
			--junit-xml=build/$(matrix)/integration-test-results/junit.xml; \
	else \
		poetry run pytest uk_bin_collection/tests/step_defs/ \
			-k "$(councils)" \
			-n logical \
			--junit-xml=build/$(matrix)/integration-test-results/junit.xml; \
	fi; \
	RESULT=$$?; \
	set -e; \
	
	# Double-check that the file exists (in case of a really early crash)
	if [ ! -f build/$(matrix)/integration-test-results/junit.xml ]; then \
		echo "<testsuite tests='0'></testsuite>" \
		     > build/$(matrix)/integration-test-results/junit.xml; \
	fi; \
	
	exit $$RESULT

generate-test-map-test-results:
	poetry run python uk_bin_collection/tests/generate_map_test_results.py build/integration-test-results/junit.xml > build/integration-test-results/test_results.json

parity-check:
	poetry run python uk_bin_collection/tests/council_feature_input_parity.py $(repo) $(branch)

unit-tests:
	poetry run coverage erase
	- poetry run coverage run --append --omit "*/tests/*" -m pytest -vv -s --log-cli-level=DEBUG uk_bin_collection/tests custom_components/uk_bin_collection/tests --ignore=uk_bin_collection/tests/step_defs/ 
	poetry run coverage xml

update-wiki:
	poetry run python wiki/generate_wiki.py
