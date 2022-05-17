"""Python device firmware update utility (pfu-util)."""

from __future__ import annotations

import os
import logging
from typing import Optional, List

import usb

from . import parser, protocol

logger = logging.getLogger(__name__)


def _get_dfu_devices(
    vid: Optional[int] = None, pid: Optional[int] = None
) -> List[usb.core.Device]:
    """Get USB devices in DFU mode.

    Args:
        vid: Filter by VID if provided.
        pid: Filter by PID if provided.

    Returns:
        List of USB devices which are currently in DFU mode.
    """

    class FilterDFU(object):
        """Identify devices which are in DFU mode."""

        def __call__(self, device):
            if vid is None or vid == device.idVendor:
                if pid is None or pid == device.idProduct:
                    for cfg in device:
                        for intf in cfg:
                            return (
                                intf.bInterfaceClass == 0xFE
                                and intf.bInterfaceSubClass == 1
                            )

    return list(usb.core.find(find_all=True, custom_match=FilterDFU()))


def _get_memory_layout(device: usb.core.Device):
    cfg = device[0]
    intf = cfg[(0, 0)]
    try:
        mem_layout_str = usb.util.get_string(device, intf.iInterface)
        return parser.parse_memory_layout(mem_layout_str)
    except usb.core.USBError:
        logger.warning("Failed to retrieve string descriptor")
        return []


def list_devices(vid: Optional[int] = None, pid: Optional[int] = None):
    """Prints a lits of devices detected in DFU mode."""
    for device in _get_dfu_devices(vid=vid, pid=pid):
        logger.info(
            "Bus {} Device {:03d}: ID {:04x}:{:04x}".format(
                device.bus, device.address, device.idVendor, device.idProduct
            )
        )

        for entry in _get_memory_layout(device):
            logger.info(
                "    0x{:x} {:2d} pages of {:3d}K bytes".format(
                    entry["addr"],
                    entry["num_pages"],
                    entry["page_size"] // 1024,
                )
            )


class DeviceFirmwareUpdater:
    """TODO"""

    def __init__(
        self,
        address,
        vid: Optional[int] = None,
        pid: Optional[int] = None,
    ):
        self._address = address
        self._is_mass_erased = False

        devices = _get_dfu_devices(vid=vid, pid=pid)
        if not devices:
            raise ValueError("No devices found in DFU mode")
        elif len(devices) > 1:
            raise ValueError(
                "Too many devices in DFU mode, specify VID/PID to select one"
            )
        else:
            self._dev = devices[0]

        logger.debug("Claiming USB interface")
        protocol.claim_interface(self._dev)

        logger.debug("Clearing DFU status")
        protocol.clear_status(self._dev)

    def __del__(self):
        logger.debug("Exiting DFU")
        protocol.exit_dfu(self._dev, self._address)

        logger.debug("Releasing USB interface")
        protocol.release_interface(self._dev)

    def mass_erase(self) -> bool:
        """Erase memory space for the device.

        Returns:
            True on success, False on failure.
        """
        if self._is_mass_erased:
            logger.info("Device already erased, nothing to do")
            return True
        else:
            if protocol.mass_erase(self._dev):
                self._is_mass_erased = True
                return True
            else:
                return False

    def download(
        self,
        filename: str,
        address: Optional[int] = None,
    ) -> bool:
        # Parse binary file
        ext = os.path.splitext(filename)[1]
        if ext == ".bin":
            if address is None:
                logger.error("Address required for binary file.")
                return False
            else:
                memory_elements = parser.parse_bin_file(filename, address)
        elif ext == ".dfu":
            memory_elements = parser.parse_dfu_file(filename)
        else:
            logger.error("File format %s not supported.", ext)
            return False

        # TODO
        raise NotImplementedError
