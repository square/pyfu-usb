# Copyright 2022 Block, Inc.
"""Test download."""
# pylint: disable=R0913,W0613,W0621

import math
import pathlib
from typing import Generator
from unittest import mock

import pytest

from pyfu_usb import download
from pyfu_usb.descriptor import DfuDescriptor
from pyfu_usb.dfu import _DFU_STATE_DFU_IDLE
from pyfu_usb.dfuse import DFUSE_VERSION_NUMBER


@pytest.fixture()
def binary_file_size() -> int:
    """Size of fake binary file."""
    return 1 << 17


@pytest.fixture()
def binary_file(binary_file_size: int, tmp_path: pathlib.Path) -> str:
    """Fake binary file."""
    bin_file = tmp_path / "test.bin"
    with open(bin_file, "wb") as handle:
        handle.write(binary_file_size * b"\xBB")
    return str(bin_file)


@pytest.fixture()
def mock_get_dfu_devices() -> Generator[mock.Mock, None, None]:
    """Mock pyfu_usb._get_dfu_devices."""
    with mock.patch("pyfu_usb._get_dfu_devices") as mock_obj:
        yield mock_obj


@pytest.fixture()
def mock_get_dfu_desc() -> Generator[mock.Mock, None, None]:
    """Mock pyfu_usb.descriptor.get_dfu_descriptor."""
    with mock.patch("pyfu_usb.descriptor.get_dfu_descriptor") as mock_obj:
        yield mock_obj


@pytest.fixture()
def mock_usb_claim() -> Generator[mock.Mock, None, None]:
    """Mock usb.util.claim_interface."""
    with mock.patch("usb.util.claim_interface") as mock_obj:
        yield mock_obj


@pytest.fixture()
def mock_usb_dispose() -> Generator[mock.Mock, None, None]:
    """Mock usb.util.dispose_resources."""
    with mock.patch("usb.util.dispose_resources") as mock_obj:
        yield mock_obj


@pytest.fixture()
def mock_dfu() -> Generator[mock.Mock, None, None]:
    """Mock pyfu_usb.dfu."""
    with mock.patch("pyfu_usb.dfu") as mock_obj:
        yield mock_obj


def test_download_bad_file() -> None:
    """Test downloading fails if a non-existent binary file is provided."""
    with pytest.raises(FileNotFoundError):
        download("banana.bin")

    with pytest.raises(IsADirectoryError):
        download(".")


def test_download_no_devices(
    binary_file: str,
    mock_get_dfu_devices: mock.Mock,
) -> None:
    """Test downloading fails if no devices are found in DFU mode."""
    mock_get_dfu_devices.return_value = []
    with pytest.raises(RuntimeError):
        download(binary_file)


def test_download_too_many_devices(
    binary_file: str,
    mock_get_dfu_devices: mock.Mock,
    mock_usb_device: mock.Mock,
) -> None:
    """Test downloading fails if more than 1 device is found in DFU mode."""
    mock_get_dfu_devices.return_value = [mock_usb_device, mock_usb_device]
    with pytest.raises(RuntimeError):
        download(binary_file)


def test_download_dfuse_no_address(
    binary_file: str,
    mock_get_dfu_devices: mock.Mock,
    mock_usb_device: mock.Mock,
    mock_get_dfu_desc: mock.Mock,
    mock_usb_claim: mock.Mock,
    mock_usb_dispose: mock.Mock,
) -> None:
    """Test downloading to a DfuSe device with no address fails."""
    mock_get_dfu_devices.return_value = [mock_usb_device]
    mock_get_dfu_desc.return_value = DfuDescriptor(
        bmAttributes=0x00,
        wDetachTimeOut=0x100,
        wTransferSize=1024,
        bcdDFUVersion=DFUSE_VERSION_NUMBER,
    )
    with pytest.raises(ValueError):
        download(binary_file)


def test_download_dfu_happy_path(
    binary_file: str,
    mock_get_dfu_devices: mock.Mock,
    mock_usb_device: mock.Mock,
    mock_get_dfu_desc: mock.Mock,
    mock_usb_claim: mock.Mock,
    mock_usb_dispose: mock.Mock,
) -> None:
    """Test downloading to a DFU device does not raise any errors."""
    mock_get_dfu_devices.return_value = [mock_usb_device]

    mock_get_dfu_desc.return_value = DfuDescriptor(
        bmAttributes=0x00,
        wDetachTimeOut=0x100,
        wTransferSize=1024,
        bcdDFUVersion=0x00,
    )

    # Mocks return value used in dfu.get_state
    mock_usb_device.ctrl_transfer.return_value = [
        0,
        0,
        0,
        0,
        _DFU_STATE_DFU_IDLE,
        0,
    ]

    download(binary_file)


def test_download_dfuse_happy_path(
    binary_file: str,
    mock_get_dfu_devices: mock.Mock,
    mock_usb_device: mock.Mock,
    mock_get_dfu_desc: mock.Mock,
    mock_usb_claim: mock.Mock,
    mock_usb_dispose: mock.Mock,
    mock_usb_get_string: mock.Mock,
) -> None:
    """Test downloading to a DfuSe device does not raise any errors."""
    mock_get_dfu_devices.return_value = [mock_usb_device]

    mock_get_dfu_desc.return_value = DfuDescriptor(
        bmAttributes=0x00,
        wDetachTimeOut=0x100,
        wTransferSize=1024,
        bcdDFUVersion=DFUSE_VERSION_NUMBER,
    )

    # Mocks return value used in dfu.get_state
    mock_usb_device.ctrl_transfer.return_value = [
        0,
        0,
        0,
        0,
        _DFU_STATE_DFU_IDLE,
        0,
    ]

    # STM32F2 memory layout string
    mock_usb_get_string.return_value = "/0x08000000/04*016Kg,01*064Kg,07*128Kg"

    download(binary_file, address=0x8000000)


def test_download_dfu_call_count(
    binary_file_size: int,
    binary_file: str,
    mock_get_dfu_devices: mock.Mock,
    mock_usb_device: mock.Mock,
    mock_get_dfu_desc: mock.Mock,
    mock_dfu: mock.Mock,
) -> None:
    """Test that DFU download makes the expected number of USB transfers."""
    mock_get_dfu_devices.return_value = [mock_usb_device]

    dfu_desc = DfuDescriptor(
        bmAttributes=0x00,
        wDetachTimeOut=0x100,
        wTransferSize=1024,
        bcdDFUVersion=0x00,
    )
    mock_get_dfu_desc.return_value = dfu_desc

    download(binary_file)

    # Add one for final download to end transaction
    exp_xfers = math.ceil(binary_file_size / dfu_desc.wTransferSize) + 1

    assert mock_dfu.download.call_count == exp_xfers
