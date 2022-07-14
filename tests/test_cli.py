# Copyright 2022 Block, Inc.
"""Test command-line interface."""
# pylint: disable=W0621

import argparse
from typing import Generator
from unittest import mock

import pytest

from pyfu_usb.__main__ import cli, create_parser


@pytest.fixture()
def parser() -> argparse.ArgumentParser:
    """CLI parser for testing."""
    return create_parser()


@pytest.fixture()
def mock_list_devices() -> Generator[mock.Mock, None, None]:
    """Mock pyfu_usb.__main__.list_devices"""
    with mock.patch("pyfu_usb.__main__.list_devices") as mock_obj:
        yield mock_obj


@pytest.fixture()
def mock_download() -> Generator[mock.Mock, None, None]:
    """Mock pyfu_usb.__main__.download"""
    with mock.patch("pyfu_usb.__main__.download") as mock_obj:
        yield mock_obj


def test_verbosity_opt(parser: argparse.ArgumentParser) -> None:
    """Test verbosity option works."""
    args = parser.parse_args(["--verbose"])
    assert cli(args) == 0


def test_version_opt(parser: argparse.ArgumentParser) -> None:
    """Test version option works."""
    args = parser.parse_args(["--version"])
    assert cli(args) == 0


def test_device_opt(
    parser: argparse.ArgumentParser, mock_list_devices: mock.Mock
) -> None:
    """Test device option works."""
    args = parser.parse_args(["--device", "bbbb:bbbb", "--list"])
    assert cli(args) == 0
    mock_list_devices.assert_called_with(vid=0xBBBB, pid=0xBBBB)


def test_bad_device_arg(parser: argparse.ArgumentParser) -> None:
    """Test bad device option fails."""
    args = parser.parse_args(["--device", "bbbb", "--list"])
    assert cli(args) == 1


def test_download_opt(
    parser: argparse.ArgumentParser, mock_download: mock.Mock
) -> None:
    """Test download option works."""
    fname = "some_file.bin"
    address = "80080000"
    args = parser.parse_args(["--download", fname, "--address", address])
    assert cli(args) == 0
    mock_download.assert_called_with(
        fname,
        interface=0,
        vid=None,
        pid=None,
        address=int(address, 16),
    )


def test_bad_download_opt(
    parser: argparse.ArgumentParser, mock_download: mock.Mock
) -> None:
    """Test download option fails if download API raises an exception."""
    args = parser.parse_args(["--download", "some_file.bin"])
    mock_download.side_effect = ValueError()
    assert cli(args) == 1
