# Copyright 2022 Block, Inc.
"""Minimal DFU protocol implementation."""

import logging
from typing import Optional

import usb

# Default USB request timeout
_TIMEOUT_MS = 5000

# DFU states
_DFU_STATE_DFU_IDLE = 0x02
_DFU_STATE_DFU_DOWNLOAD_IDLE = 0x05
_DFU_STATE_DFU_ERROR = 0x0A

# DFU commands
_DFU_CMD_DOWNLOAD = 1
_DFU_CMD_GETSTATUS = 3
_DFU_CMD_CLRSTATUS = 4
_DFU_STATE_LEN = 6

# USB request types
_USB_REQUEST_TYPE_SEND = 0x21
_USB_REQUEST_TYPE_RECV = 0xA1

logger = logging.getLogger(__name__)


def get_state(
    dev: usb.core.Device, interface: int, timeout_ms: int = _TIMEOUT_MS
) -> int:
    """Get device state.

    Args:
        dev: USB device.
        interface: USB device interface.
        timeout_ms: Timeout in milliseconds for USB control transfer.

    Returns:
        Device state code.

    Raises:
        RuntimeError: Device returned error state.
    """
    status = dev.ctrl_transfer(
        bmRequestType=_USB_REQUEST_TYPE_RECV,
        bRequest=_DFU_CMD_GETSTATUS,
        wValue=0,
        wIndex=interface,
        data_or_wLength=_DFU_STATE_LEN,
        timeout=timeout_ms,
    )

    state: int = status[4]

    if state == _DFU_STATE_DFU_ERROR:
        raise RuntimeError("Target device error")

    return state


def clear_status(
    dev: usb.core.Device, interface: int, timeout_ms: int = _TIMEOUT_MS
) -> None:
    """Wait for idle state and then clear device status.

    Args:
        dev: USB device.
        interface: USB device interface.
        timeout_ms: Timeout in milliseconds for USB control transfer.
    """
    dev.ctrl_transfer(
        bmRequestType=_USB_REQUEST_TYPE_SEND,
        bRequest=_DFU_CMD_CLRSTATUS,
        wValue=0,
        wIndex=interface,
        data_or_wLength=None,
        timeout=timeout_ms,
    )


def download(
    dev: usb.core.Device,
    interface: int,
    transaction: int,
    data: Optional[bytes],
    timeout_ms: int = _TIMEOUT_MS,
) -> None:
    """Download data.

    Args:
        dev: USB device.
        interface: USB device interface.
        transaction: Transaction counter.
        data: Data to download or None to indicate end of download.
        timeout_ms: Timeout in milliseconds for USB control transfer.
    """
    # Send data
    dev.ctrl_transfer(
        bmRequestType=_USB_REQUEST_TYPE_SEND,
        bRequest=_DFU_CMD_DOWNLOAD,
        wValue=transaction,
        wIndex=interface,
        data_or_wLength=data,
        timeout=timeout_ms,
    )

    # Wait for download to process
    while get_state(dev, interface, timeout_ms=timeout_ms) not in [
        _DFU_STATE_DFU_IDLE,
        _DFU_STATE_DFU_DOWNLOAD_IDLE,
    ]:
        pass


def claim_interface(dev: usb.core.Device, interface: int) -> None:
    """Claim DFU interface for USB device.

    Args:
        dev: USB device.
        interface: USB device interface.
    """
    logger.info("Claiming USB DFU interface %d", interface)
    usb.util.claim_interface(dev, interface)


def release_interface(dev: usb.core.Device) -> None:
    """Release DFU interface for USB device.

    Args:
        dev: USB device in DFU mode.
    """
    logger.info("Releasing USB DFU interface")
    usb.util.dispose_resources(dev)
