"""Python device firmware update utility (pfu-util)."""

import os
import logging

from .protocol import get_dfu_devices

logger = logging.getLogger(__name__)


def list_dfu_devices():
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
    pass


def write_bin(address: int, bin_file: str, mass_erase_performed: bool):
    if not os.path.exists(bin_file):
        logger.error("Error: Binary file %s does not exist.", bin_file)
        return


def write_dfu(dfu_file: str, mass_erase_performed: bool):
    if not os.path.exists(dfu_file):
        logger.error("Error: DFU file %s does not exist.", dfu_file)
        return


def exit_dfu(address: int):
    """Exit DFU mode, and start running the program."""

    # set jump address
    set_address(address)

    # Send DNLOAD with 0 length to exit DFU
    __dev.ctrl_transfer(0x21, __DFU_DNLOAD, 0, __DFU_INTERFACE,
                        None, __TIMEOUT)

    try:
        # Execute last command
        if get_status() != __DFU_STATE_DFU_MANIFEST:
            logger.error("Failed to reset device")

        # Release device
        usb.util.dispose_resources(__dev)
    except:
        pass


def write_page(buf, xfer_offset):
    """Writes a single page. This routine assumes that memory has already
    been erased.
    """

    xfer_base = 0x08000000

    # Set mem write address
    set_address(xfer_base+xfer_offset)

    # Send DNLOAD with fw data
    __dev.ctrl_transfer(0x21, __DFU_DNLOAD, 2, __DFU_INTERFACE, buf, __TIMEOUT)

    # Execute last command
    if get_status() != __DFU_STATE_DFU_DOWNLOAD_BUSY:
        logger.error("DFU: write memory failed")
        raise Exception("DFU: write memory failed")

    # Check command state
    if get_status() != __DFU_STATE_DFU_DOWNLOAD_IDLE:
        logger.error("DFU: write memory failed")
        raise Exception("DFU: write memory failed")

    logger.debug("Write: 0x%x " % (xfer_base + xfer_offset))


def write_memory(addr, buf, progress=None, progress_addr=0, progress_size=0):
    """Writes a buffer into memory. This routine assumes that memory has
    already been erased.
    """

    xfer_count = 0
    xfer_bytes = 0
    xfer_total = len(buf)
    xfer_base = addr

    while xfer_bytes < xfer_total:
        if xfer_count % 512 == 0:
            logger.debug("Addr 0x%x %dKBs/%dKBs..." % (xfer_base + xfer_bytes,
                                                       xfer_bytes // 1024,
                                                       xfer_total // 1024))
        if progress and xfer_count % 256 == 0:
            progress(progress_addr, xfer_base + xfer_bytes - progress_addr,
                     progress_size)

        # Set mem write address
        set_address(xfer_base+xfer_bytes)

        # Send DNLOAD with fw data
        chunk = min(64, xfer_total-xfer_bytes)
        __dev.ctrl_transfer(0x21, __DFU_DNLOAD, 2, __DFU_INTERFACE,
                            buf[xfer_bytes:xfer_bytes + chunk], __TIMEOUT)

        # Execute last command
        if get_status() != __DFU_STATE_DFU_DOWNLOAD_BUSY:
            logger.error("DFU: write memory failed")
            raise Exception("DFU: write memory failed")

        # Check command state
        if get_status() != __DFU_STATE_DFU_DOWNLOAD_IDLE:
            logger.error("DFU: write memory failed")
            raise Exception("DFU: write memory failed")

        xfer_count += 1
        xfer_bytes += chunk
