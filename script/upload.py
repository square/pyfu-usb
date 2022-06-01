# Copyright 2022 Square, Inc.

import os
import json

import twine.cli

_SQUARE_PYPI_URL = "https://nexus3.sqcorp.co/repository/pypi-square-devicesoftware/"
_SQUARE_PYPI_USERNAME = os.environ.get("SQUARE_PYPI_USERNAME", "USERNAME")
_SQUARE_PYPI_PASSWORD = os.environ.get("SQUARE_PYPI_PASSWORD", "PASSWORD")
_PROJECT_NAME = os.environ.get('PROJECT_NAME', '')
_SECRETS_PATH = os.environ.get(
    "SECRETS_PATH", os.path.join(os.sep, "data", "pods", _PROJECT_NAME, "secrets")
)
_SECRET_JSON = os.path.join(
    _SECRETS_PATH, "kochiku-worker-pypi-square-devicesoftware.json"
)


def get_credentials():
    if os.path.exists(_SECRET_JSON):
        print("Reading credentials from secret file: %s" % _SECRET_JSON)
        with open(_SECRET_JSON, "r") as f:
            data = json.loads(f.read())
            return data.get("username"), data.get("password")
    elif os.path.exists(_SECRETS_PATH):
        print("Secrets found: %r" % os.listdir(_SECRETS_PATH))
    else:
        print("Secrets path does not exist: %r" % _SECRETS_PATH)
    print("Reading credentials from environment.")
    return _SQUARE_PYPI_USERNAME, _SQUARE_PYPI_PASSWORD


def main():
    username, password = get_credentials()

    args = [
        "upload",
        "-r",
        "squarepypi",
        "--repository-url",
        _SQUARE_PYPI_URL,
        "-u",
        username,
        "-p",
        password,
        "--skip-existing",
        "software/dist/*",
    ]
    try:
        twine.cli.dispatch(args)
    except Exception as e:
        if "Repository does not allow updating assets" in str(e):
            print("Skipping package upload.  Already exists.")
        else:
            raise e


if __name__ == "__main__":
    main()
