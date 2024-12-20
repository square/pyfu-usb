# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.2] - 2024-12-20

- Remove `pylint` disable annotations.
- Remove unused imports detected when switching to `ruff`.

## [2.0.1] - 2024-10-30

- Add Python 3.8 support back - it did not need to be dropped in version 2.0.0.
- `importlib.metadata` is available in the standard library for Python 3.8 and
  higher, so it does not need to be included as a dependency in `setup.py`.

## [2.0.0] - 2024-10-21

- Drop support for Python 3.7 and 3.8.
- Migrate from `pkg_resources` to `importlib_metadata`.
- Rework `_dfuse_download` slightly: Instead of always clearing the status
  before starting the download, only do it if a pipe error is detected. In newer
  STM32 devices, clearing the status seems to make the first download fail.

## [1.0.2] - 2022-08-15

- Ignore all `USBError` exceptions when exiting DFU mode.

## [1.0.1] - 2022-07-14

- Set `long_description` of package to contents of `README.md`.

## [1.0.0] - 2022-07-14

- Initial release.
