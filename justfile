setup:
    uv run python -m pre_commit install --install-hooks

lint:
    uv run python -m pre_commit run --all-files

test:
    uv run pytest --log-cli-level=INFO -s tests/

coverage:
    uv run coverage run .venv/bin/pytest tests/
    uv run coverage report
