"""Python device firmware update utility (pfu-util)."""

import os
import logging
from typing import Optional

import usb

from .parser import read_bin_file, read_dfu_file
from .protocol import get_dfu_devices

logger = logging.getLogger(__name__)


def list_devices():
    """Prints a lits of devices detected in DFU mode."""
    devices = get_dfu_devices()
    if not devices:
        return

    for device in devices:
        logger.info(
            "Bus {} Device {:03d}: ID {:04x}:{:04x}".format(
                device.bus, device.address, device.idVendor, device.idProduct
            )
        )

        # TODO: Re-add
        # layout = get_memory_layout(device)
        # logger.info("Memory Layout")
        # for entry in layout:
        #     logger.info(
        #         "    0x{:x} {:2d} pages of {:3d}K bytes".format(
        #             entry["addr"],
        #             entry["num_pages"],
        #             entry["page_size"] // 1024,
        #         )
        #     )


def mass_erase(address: int):
    logger.info("Address: %X", address)


def download(
    filename,
    address: Optional[int] = None,
    mass_erase_performed: bool = False
) -> bool:
    # Parse binary file
    ext = os.path.splitext(filename)[1]
    if ext == ".bin":
        if address is None:
            logger.error("Address required for binary file.")
            return False
        else:
            memory_elements = read_bin_file(filename, address)
    elif ext == ".dfu":
        memory_elements = read_dfu_file(filename)
    else:
        logger.error("File format %s not supported.", ext)
        return False

    logger.info("Memory: %s, Address: %X", memory_elements)
