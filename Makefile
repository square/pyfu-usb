VENV_DIR := .venv
VENV_PYTHON := $(VENV_DIR)/bin/python

$(VENV_DIR):
	@echo "Setting up virtual environment and pre-commit hooks..."
	@python -m venv $@
	@$(VENV_PYTHON) -m pip install --upgrade --quiet pip setuptools
	@$(VENV_PYTHON) -m pip install --upgrade --quiet --editable ".[dev]"
	@$(VENV_PYTHON) -m pre_commit install --install-hooks
	@echo "Setup complete."

.PHONY: setup
setup: | $(VENV_DIR)

.PHONY: pre_commit
pre_commit: | $(VENV_DIR)
	@export PATH=$(VENV_DIR)/bin:$$PATH; $(VENV_PYTHON) -m pre_commit run --all-files

.PHONY: test
test: | $(VENV_DIR)
	$(VENV_DIR)/bin/coverage run $(VENV_DIR)/bin/pytest -s --log-cli-level=INFO tests/

.PHONY: coverage
coverage: test
	$(VENV_DIR)/bin/coverage report

.PHONY: wheel
wheel: | $(VENV_DIR)
	$(VENV_PYTHON) setup.py bdist_wheel

.PHONY: clean
clean:
	@rm -rf $(VENV_DIR) *.egg-info/ dist/ build/ .pytest_cache/
