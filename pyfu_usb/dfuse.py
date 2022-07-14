# Copyright 2022 Block, Inc.
"""Minimal DfuSe protocol implementation."""

import logging
import struct

import usb

from .dfu import download

logger = logging.getLogger(__name__)

_DFUSE_CMD_ADDR = 0x21
_DFUSE_CMD_ERASE = 0x41

DFUSE_VERSION_NUMBER = 0x11A


def set_address(dev: usb.core.Device, interface: int, address: int) -> None:
    """Sets the address for the next operation.

    Args:
        dev: USB device.
        interface: USB device interface.
        address: Device address.
    """
    download(dev, interface, 0, struct.pack("<BI", _DFUSE_CMD_ADDR, address))


def page_erase(dev: usb.core.Device, interface: int, address: int) -> None:
    """Erases a single page of device memory.

    Args:
        dev: USB device.
        interface: USB device interface.
        address: Address of page in device memory.
    """
    download(dev, interface, 0, struct.pack("<BI", _DFUSE_CMD_ERASE, address))
