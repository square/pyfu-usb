# Copyright 2022 Block, Inc.
"""Common unit test fixtures."""

from typing import Generator
from unittest import mock

import pytest


@pytest.fixture()
def mock_usb_device() -> Generator[mock.Mock, None, None]:
    """Mock usb.core.Device."""
    with mock.patch("usb.core.Device", spec=True) as mock_obj:
        yield mock_obj


@pytest.fixture()
def mock_usb_get_string() -> Generator[mock.Mock, None, None]:
    """Mock usb.util.get_string."""
    with mock.patch("usb.util.get_string") as mock_obj:
        yield mock_obj
