#!/bin/bash

# Check that the correct version of python is installed and on PATH
# SSPI_INSTALL_PYVERSION=$(python --version)
# echo "$SSPI_INSTALL_PYVERSION#."
# echo "$SSPI_INSTALL_PYVERSION##."
# echo $PATH

VENV=env
PYTHON=$(VENV)/bin/python3
PIP=$(VENV)/bin/pip

setup: requirements.txt
	python -m venv env
	pip install -r requirements.txt

run:
	flask run --debug

clean:
	rm -rf __pycache__
	rm -rf env

.PHONY: run, clean
