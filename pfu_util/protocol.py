"""TODO: Add different low-level DFU USB commands here."""

import time
import struct
import logging
from typing import Optional

import usb

# USB DFU interface
__DFU_INTERFACE = 0

# USB request timeout
__TIMEOUT = 5000

# DFU commands
__DFU_DETACH = 0
__DFU_DNLOAD = 1
__DFU_UPLOAD = 2
__DFU_GETSTATUS = 3
__DFU_CLRSTATUS = 4
__DFU_GETSTATE = 5
__DFU_ABORT = 6

# DFU status
__DFU_STATE_APP_IDLE = 0x00
__DFU_STATE_APP_DETACH = 0x01
__DFU_STATE_DFU_IDLE = 0x02
__DFU_STATE_DFU_DOWNLOAD_SYNC = 0x03
__DFU_STATE_DFU_DOWNLOAD_BUSY = 0x04
__DFU_STATE_DFU_DOWNLOAD_IDLE = 0x05
__DFU_STATE_DFU_MANIFEST_SYNC = 0x06
__DFU_STATE_DFU_MANIFEST = 0x07
__DFU_STATE_DFU_MANIFEST_WAIT_RESET = 0x08
__DFU_STATE_DFU_UPLOAD_IDLE = 0x09
__DFU_STATE_DFU_ERROR = 0x0A

__DFU_STATUS = [
    "DFU_STATE_APP_IDLE",
    "DFU_STATE_APP_DETACH",
    "DFU_STATE_DFU_IDLE",
    "DFU_STATE_DFU_DOWNLOAD_SYNC",
    "DFU_STATE_DFU_DOWNLOAD_BUSY",
    "DFU_STATE_DFU_DOWNLOAD_IDLE",
    "DFU_STATE_DFU_MANIFEST_SYNC",
    "DFU_STATE_DFU_MANIFEST",
    "DFU_STATE_DFU_MANIFEST_WAIT_RESET",
    "DFU_STATE_DFU_UPLOAD_IDLE",
    "DFU_STATE_DFU_ERROR",
]

logger = logging.getLogger(__name__)


def _get_status(dev: usb.core.Device) -> int:
    """Get the status of the last operation.

    Args:
        dev: USB device in DFU mode.

    Returns:
        Status code.

    Raises:
        usb.core.USBTimeoutError: USB control transfer timeout.
    """
    stat = dev.ctrl_transfer(
        0xA1, __DFU_GETSTATUS, 0, __DFU_INTERFACE, 6, 20000
    )

    logger.debug("DFU Status: %s", __DFU_STATUS[stat[4]])
    return stat[4]


def _set_address(dev: usb.core.Device, address: int):
    """Sets the address for the next operation.

    Args:
        dev: USB device in DFU mode.
        address: Device address to jump to when exiting DFU.

    Raises:
        RuntimeError: Address could not be set.
        usb.core.USBTimeoutError: USB control transfer timeout.
    """
    # Send DNLOAD with first byte=0x21 and page address
    buf = struct.pack("<BI", 0x21, address)
    dev.ctrl_transfer(0x21, __DFU_DNLOAD, 0, __DFU_INTERFACE, buf, __TIMEOUT)

    # Execute last command
    if _get_status(dev) != __DFU_STATE_DFU_DOWNLOAD_BUSY:
        raise RuntimeError("Set address failed")

    # Check command state
    if _get_status(dev) != __DFU_STATE_DFU_DOWNLOAD_IDLE:
        raise RuntimeError("Set address failed")


def claim_interface(dev: usb.core.Device):
    """Claim DFU interface for USB device.

    Args:
        dev: USB device in DFU mode.
    """
    usb.util.claim_interface(dev, __DFU_INTERFACE)


def release_interface(dev: usb.core.Device):
    """Release DFU interface for USB device.

    Args:
        dev: USB device in DFU mode.
    """
    usb.util.dispose_resources(dev)


def clear_status(dev: usb.core.Device):
    """Clears any error status, perhaps left over from a previous session.

    Args:
        dev: USB device in DFU mode.

    Raises:
        usb.core.USBTimeoutError: USB control transfer timeout.
    """
    status = _get_status(dev)
    while (
        status != __DFU_STATE_DFU_IDLE
        and status != __DFU_STATE_DFU_DOWNLOAD_IDLE
    ):
        dev.ctrl_transfer(
            0x21, __DFU_CLRSTATUS, 0, __DFU_INTERFACE, None, __TIMEOUT
        )

        status = _get_status(dev)
        time.sleep(0.1)


def mass_erase(dev: usb.core.Device) -> bool:
    """Performs a mass erase.

    Args:
        dev: USB device in DFU mode.

    Raises:
        RuntimeError: Mass erase failed.
        usb.core.USBTimeoutError: USB control transfer timeout.
    """
    # Send DNLOAD with first byte=0x41
    dev.ctrl_transfer(0x21, __DFU_DNLOAD, 0, __DFU_INTERFACE, "\x41", __TIMEOUT)

    # Execute last command
    if _get_status(dev) != __DFU_STATE_DFU_DOWNLOAD_BUSY:
        raise RuntimeError("Mass erase failed")

    # Check command state
    if _get_status(dev) != __DFU_STATE_DFU_DOWNLOAD_IDLE:
        raise RuntimeError("Mass erase failed")

    logger.debug("DFU erased succeeded")


def exit_dfu(dev: usb.core.Device, address: int):
    """Exit DFU mode and start running the program.

    Args:
        dev: USB device in DFU mode.
        address: Device address to jump to when exiting DFU.

    Raises:
        usb.core.USBTimeoutError: USB control transfer timeout.
    """
    # Set jump address
    _set_address(dev, address)

    # Send DNLOAD with 0 length to exit DFU
    dev.ctrl_transfer(0x21, __DFU_DNLOAD, 0, __DFU_INTERFACE, None, __TIMEOUT)

    try:
        # Execute last command
        if _get_status(dev) != __DFU_STATE_DFU_MANIFEST:
            logger.warning("Failed to reset device")
    except:
        pass
