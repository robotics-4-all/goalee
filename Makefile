.PHONY: clean clean-test clean-pyc clean-build docs help lint format test coverage dist install release
.DEFAULT_GOAL := help

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -fr .ruff_cache/
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache

lint: ## check style with ruff
	ruff check goalee/ tests/

format: ## format code with ruff
	ruff format goalee/ tests/

test: ## run tests with pytest
	pytest tests/ -v

coverage: ## check code coverage with pytest
	coverage run -m pytest tests/
	coverage report -m
	coverage html

docs: ## generate Sphinx HTML documentation, including API docs
	rm -f docs/goalee.rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs/ goalee
	$(MAKE) -C docs clean
	$(MAKE) -C docs html

release: dist ## package and upload a release
	twine upload dist/*

dist: clean ## builds source and wheel package
	python -m build
	ls -l dist

install: ## install the package in development mode
	pip install -e ".[dev,test]"
