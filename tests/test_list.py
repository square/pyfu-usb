# Copyright 2022 Block, Inc.
"""Test list."""

from unittest import mock

from pyfu_usb import list_devices


def test_list_devices(
    mock_usb_device: mock.Mock,
    mock_usb_get_string: mock.Mock,
) -> None:
    """Test list_devices."""
    # STM32F2 memory layout string
    mock_usb_get_string.return_value = "/0x08000000/04*016Kg,01*064Kg,07*128Kg"

    with mock.patch("usb.core.find", spec=True) as mock_usb_find:
        mock_usb_find.return_value = [mock_usb_device]
        mock_usb_device.bus = 1
        mock_usb_device.address = 2
        mock_usb_device.idVendor = 0xBBBB
        mock_usb_device.idProduct = 0xBBBB
        list_devices()
