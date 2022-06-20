.PHONY: venv
	python -m venv .venv
	@echo "Source .venv/bin/activate now"
	@echo "Then pip install -rrequirements.txt"

.PHONY: test
test:
	python -m unittest

.PHONY: coverage
coverage:
	python -m coverage run -m test_zipimport64
	python -m coverage run -m test_zipimport64_compression
	python -m coverage report

.PHONY: format
format:
	ufmt format test_zipimport64.py test_zipimport64_compression.py testdata/create.py
