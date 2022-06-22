# Copyright 2022 Block, Inc.
"""Get DFU related info from USB device descriptors."""

import dataclasses
import logging
import re
from typing import List, Optional

import usb

logger = logging.getLogger(__name__)

_DFU_DESCRIPTOR_LEN = 9
_DFU_DESCRIPTOR_ID = 0x21


# pylint: disable=invalid-name
@dataclasses.dataclass
class DfuDescriptor:
    """DFU descriptor."""

    # NOTE: Alternate naming convention used to match DFU spec
    bmAttributes: int
    wDetachTimeOut: int
    wTransferSize: int
    bcdDFUVersion: int


@dataclasses.dataclass
class DfuSeMemoryLayout:
    """Memory layout for DfuSe device."""

    addr: int
    last_addr: int
    size: int
    num_pages: int
    page_size: int


def get_dfu_descriptor(dev: usb.core.Device) -> Optional[DfuDescriptor]:
    """Find and parse the DFU descriptor for a USB device.

    Args:
        dev: USB device.

    Returns:
        `DfuDescriptor` or None if not found.
    """
    for cfg in dev:
        for intf in cfg:
            # pyusb does not seem to automatically parse DFU descriptors
            dfu_desc = intf.extra_descriptors
            if (
                len(dfu_desc) == _DFU_DESCRIPTOR_LEN
                and dfu_desc[1] == _DFU_DESCRIPTOR_ID
            ):
                desc = DfuDescriptor(
                    bmAttributes=dfu_desc[2],
                    wDetachTimeOut=dfu_desc[4] << 8 | dfu_desc[3],
                    wTransferSize=dfu_desc[6] << 8 | dfu_desc[5],
                    bcdDFUVersion=dfu_desc[8] << 8 | dfu_desc[7],
                )
                logger.debug("DFU descriptor: %s", desc)
                return desc
    return None


# pylint: disable=too-many-locals
def get_memory_layout(
    device: usb.core.Device,
    interface: int,
    alternate_index: int = 0,
) -> List[DfuSeMemoryLayout]:
    """Get the DfuSe memory layout for a USB device.

    Args:
        dev: USB device.
        interface: USB device interface.
        alternate_index: USB device alternate index for interface.

    Returns:
        List of `DfuSeMemoryLayout`, one for each "segment" in device memory.
    """
    # Get memory layout string - Assumes cfg 0 is used which is safe since USB
    # devices rarely have more than one configuration.
    intf = device[0][(interface, alternate_index)]
    try:
        mem_layout_str = usb.util.get_string(device, intf.iInterface).split("/")
    except usb.core.USBError:
        logger.warning("Failed to get string descriptor, not a DfuSe device?")
        return []

    # Parse memory layout string
    addr = int(mem_layout_str[1], 0)
    segments = mem_layout_str[2].split(",")
    seg_re = re.compile(r"(\d+)\*(\d+)(.)(.)")

    mem_layout = []
    for segment in segments:
        seg_match = seg_re.match(segment)
        assert seg_match is not None

        num_pages = int(seg_match.groups()[0], 10)
        page_size = int(seg_match.groups()[1], 10)
        multiplier = seg_match.groups()[2]

        if multiplier == "K":
            page_size *= 1024
        if multiplier == "M":
            page_size *= 1024 * 1024
        if multiplier == " ":
            page_size *= 1

        # TODO: Figure out the meaning of the final character in the page
        # description. For STM32F2, flash memory is "g" and for other regions
        # like OTP, Option Bytes, and Device Feature are "e". This may indicate
        # access permissions, like read-only ("e") or read-write ("g")?
        # page_code = seg_match.groups()[3]

        size = num_pages * page_size
        last_addr = addr + size - 1

        mem_layout.append(
            DfuSeMemoryLayout(
                addr=addr,
                last_addr=last_addr,
                size=size,
                num_pages=num_pages,
                page_size=page_size,
            )
        )

        addr += size

    return mem_layout
