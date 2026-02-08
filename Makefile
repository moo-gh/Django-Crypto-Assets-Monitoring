# include .env
export

SHELL=/bin/bash

.PHONY: format
format: format-python

.PHONY: lint
lint: lint-python

.PHONY: test
test: test-python

###############################
# Preparation

ENV_NAME="crypto"
PYTHON_VERSION=3.12
CONDA_ACTIVATE=source $$(conda info --base)/etc/profile.d/conda.sh ; conda activate
CONDA_DEACTIVATE=source $$(conda info --base)/etc/profile.d/conda.sh ; conda deactivate

.PHONY: install-dep
install-dep:
	@cat src/requirements.txt \
	ci/requirements.txt | \
	xargs -n 1 -L 1 \
	$$(conda info --base)/envs/${ENV_NAME}/bin/pip \
	--no-cache-dir --disable-pip-version-check install --user

.PHONY: remove-dep
remove-dep:
	@cat src/requirements.txt \
	ci/requirements.txt | \
	xargs -n 1 -L 1 \
	$$(conda info --base)/envs/${ENV_NAME}/bin/pip \
	--no-cache-dir --disable-pip-version-check uninstall -y

.PHONY: install-dev-tools
install-dev-tools:
	@make remove-dep
	@$(CONDA_DEACTIVATE) && conda env remove --name ${ENV_NAME}
	@conda create --name ${ENV_NAME} python=${PYTHON_VERSION}
	@make install-dep

###############################
# dev tools

.PHONY: format-python
format-python:
	@ci/format-python.sh

.PHONY: lint-python
lint-python:
	@MYPYPATH=src ci/lint-python.sh

.PHONY: test-python
test-python:
	@ci/test-python.sh
