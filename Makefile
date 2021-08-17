.PHONY: usage clean setup test build

PY37=3.7.10
PY38=3.8.8
PY39=3.9.2

usage:
	@echo "No target selected"

clean:
	rm -rf dist coverage.xml results.unit.xml .coverage .tox
	find . -type d -name __pycache__ -exec rm -rv {} +

setup:
	pyenv install ${PY37} --skip-existing
	pyenv install ${PY38} --skip-existing
	pyenv install ${PY39} --skip-existing
	pyenv local ${PY37} ${PY38} ${PY39}

test: setup
	poetry run tox

build: setup
	poetry build

install: build
	pip install . --use-feature=in-tree-build
