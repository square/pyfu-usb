# Copyright 2022 Block, Inc.
"""Python USB Firmware Updater (pyfu-usb).

- List connected DFU devices using `list_devices`. If a device implements
  the DfuSe protocol (e.g. STM32), the memory layout will be listed as well.
- Download binary files to DFU devices using `download`. If a device implements
  the DfuSe protocol (e.g. STM32), an `address` must be provided which is the
  beginning of the binary file in device memory.
"""

import logging
import os
from typing import Dict, List, Optional

import usb
from rich.progress import Progress, TaskID

from . import descriptor, dfu, dfuse

_BYTES_PER_KILOBYTE = 1024

logger = logging.getLogger(__name__)


def _make_progress_bar(progress: Progress, total: int) -> Optional[TaskID]:
    """Create task for rich progress bar, but only if logging level is not
    DEBUG since they would conflict on the output.

    Args:
        progress: rich progress bar.

    Returns:
        Task for rich progress bar or None if logging level is DEBUG.
    """
    if logger.getEffectiveLevel() != logging.DEBUG:
        return progress.add_task(
            "[blue]Downloading firmware",
            total=total,
            start_task=False,
        )

    return None


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

    class FilterDFU:  # pylint: disable=too-few-public-methods
        """Identify devices which are in DFU mode."""

        def __call__(self, device: usb.core.Device) -> bool:
            if vid is None or vid == device.idVendor:
                if pid is None or pid == device.idProduct:
                    for cfg in device:
                        for intf in cfg:
                            if (
                                intf.bInterfaceClass == 0xFE
                                and intf.bInterfaceSubClass == 1
                            ):
                                return True
            return False

    return list(usb.core.find(find_all=True, custom_match=FilterDFU()))


def _dfuse_download(
    dev: usb.core.Device,
    interface: int,
    data: bytes,
    xfer_size: int,
    start_address: int,
) -> None:
    """Download data to DfuSe device.

    Args:
        dev: USB device in DFU mode.
        interface: USB device interface.
        data: Binary data to download.
        xfer_size: Transfer size to use when downloading.
        start_address: Start address of data in device memory.
    """
    # Clear status, possibly leftover from previous transaction
    dfu.clear_status(dev, interface)

    for segment_num, segment in enumerate(
        descriptor.get_memory_layout(dev, interface)
    ):
        for page_num in range(segment.num_pages):
            page_addr = segment.addr + page_num * segment.page_size
            if start_address <= page_addr <= start_address + len(data):
                logger.info(
                    "Erasing page 0x%X of size %d in segment %d",
                    page_addr,
                    segment.page_size,
                    segment_num,
                )

                dfuse.page_erase(dev, interface, page_addr)

    # Download data
    with Progress() as progress:
        task = _make_progress_bar(progress, len(data))

        bytes_downloaded = 0
        while bytes_downloaded < len(data):
            chunk_size = min(xfer_size, len(data) - bytes_downloaded)
            chunk = data[bytes_downloaded : bytes_downloaded + chunk_size]

            dfuse.set_address(dev, interface, start_address + bytes_downloaded)

            logger.debug(
                "Downloading %d bytes (total: %d bytes)",
                chunk_size,
                bytes_downloaded,
            )

            # Unclear why 2 is needed for DfuSe vs. a counter for DFU
            dfu.download(dev, interface, 2, chunk)

            bytes_downloaded += chunk_size
            if task is not None:
                progress.update(task, advance=chunk_size)

    # Set jump address
    dfuse.set_address(dev, interface, start_address)

    # End with empty download
    try:
        dfu.download(dev, interface, 0, None)
    except usb.core.USBError as err:
        if "Pipe error" in str(err):
            logger.warning("Ignoring pipe error when reading final status")
        else:
            raise err


def _dfu_download(
    dev: usb.core.Device, interface: int, data: bytes, xfer_size: int
) -> None:
    """Download data to DFU device.

    Args:
        dev: USB device in DFU mode.
        interface: USB device interface.
        data: Binary data to download.
        xfer_size: Transfer size to use when downloading.
    """
    # Download data
    with Progress() as progress:
        task = _make_progress_bar(progress, len(data))

        transaction = 0
        bytes_downloaded = 0
        while bytes_downloaded < len(data):
            chunk_size = min(xfer_size, len(data) - bytes_downloaded)
            chunk = data[bytes_downloaded : bytes_downloaded + chunk_size]

            logger.debug(
                "Downloading %d bytes (total: %d bytes)",
                chunk_size,
                bytes_downloaded,
            )

            dfu.download(dev, interface, transaction, chunk)

            transaction += 1
            bytes_downloaded += chunk_size
            if task is not None:
                progress.update(task, advance=chunk_size)

    # End with empty download
    try:
        dfu.download(dev, interface, 0, None)
    except usb.core.USBError as err:
        if "Pipe error" in str(err):
            logger.warning("Ignoring pipe error when reading final status")
        else:
            raise err


def list_devices(vid: Optional[int] = None, pid: Optional[int] = None) -> None:
    """List devices detected in DFU mode. For DfuSe devices, the memory layout
    will be listed as well.

    Args:
        vid: Vendor ID to narrow the search for DFU devices.
        pid: Product ID to narrow the search for DFU devices.
    """
    for device in _get_dfu_devices(vid=vid, pid=pid):
        logger.info(
            "Bus {} Device {:03d}: ID {:04x}:{:04x}".format(
                device.bus, device.address, device.idVendor, device.idProduct
            )
        )

        for cfg in device:
            for intf in cfg:
                for segment in descriptor.get_memory_layout(
                    device,
                    intf.bInterfaceNumber,
                    alternate_index=intf.alternate_index,
                ):
                    if segment.page_size > _BYTES_PER_KILOBYTE:
                        page_size = segment.page_size // _BYTES_PER_KILOBYTE
                        page_char = "K"
                    else:
                        page_size = segment.page_size
                        page_char = ""

                    logger.info(
                        "    0x{:x} {:2d} pages of {:3d}{:s} bytes".format(
                            segment.addr,
                            segment.num_pages,
                            page_size,
                            page_char,
                        )
                    )


def download(
    filename: str,
    interface: int = 0,
    vid: Optional[int] = None,
    pid: Optional[int] = None,
    address: Optional[int] = None,
) -> None:
    """Download a file to the DFU device defined by vid:pid. If vid:pid is not
    provided and only one DFU device is present, that device will be used.

    Args:
        filename: Binary file to download.
        interface: USB device interface.
        vid: Vendor ID to narrow the search for DFU devices.
        pid: Product ID to narrow the search for DFU devices.
        address: Base address to jump to in memory. This is required for DfuSe.

    Raises:
        ValueError: Could not read DFU device USB descriptor.
        ValueError: Address not provided for DfuSe device.
        RuntimeError: Could not locate DFU device.
    """
    logger.info("Downloading binary file: %s", filename)
    with open(filename, "rb") as fin:
        data = fin.read()

    devices = _get_dfu_devices(vid=vid, pid=pid)

    if not devices:
        raise RuntimeError("No devices found in DFU mode")

    if len(devices) > 1:
        raise RuntimeError(
            f"Too many devices in DFU mode ({len(devices)}). List devices for "
            "more info and specify vid:pid to filter."
        )

    dev = devices[0]

    try:
        dfu.claim_interface(dev, interface)

        dfu_desc = descriptor.get_dfu_descriptor(dev)
        if dfu_desc is None:
            raise ValueError("No DFU descriptor, is this a valid DFU device?")

        if dfu_desc.bcdDFUVersion == dfuse.DFUSE_VERSION_NUMBER:
            if address is None:
                raise ValueError("Must provide address for DfuSe")
            _dfuse_download(
                dev, interface, data, dfu_desc.wTransferSize, address
            )
        else:
            _dfu_download(dev, interface, data, dfu_desc.wTransferSize)
    finally:
        dfu.release_interface(dev)
