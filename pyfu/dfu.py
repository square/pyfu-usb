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
        0xA1, _DFU_CMD_GETSTATUS, 0, interface, 6, timeout_ms
    )

    state: int = status[4]

    if state == _DFU_STATE_DFU_ERROR:
        raise RuntimeError("Device error")

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
    dev.ctrl_transfer(0x21, _DFU_CMD_CLRSTATUS, 0, interface, None, timeout_ms)


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
        0x21,
        _DFU_CMD_DOWNLOAD,
        transaction,
        interface,
        data,
        timeout_ms,
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
