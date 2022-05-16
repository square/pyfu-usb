"""TODO: Add different low-level DFU USB commands here."""

import usb


def get_dfu_devices():
    """Returns a list of USB device which are currently in DFU mode.
    Additional filters (like idProduct and idVendor) can be passed in to
    refine the search.
    """

    class FilterDFU(object):
        """Identify devices which are in DFU mode."""

        def __call__(self, device):
            for cfg in device:
                for intf in cfg:
                    return (
                        intf.bInterfaceClass == 0xFE
                        and intf.bInterfaceSubClass == 1
                    )

    return list(usb.core.find(find_all=True, custom_match=FilterDFU()))


def clr_status():
    """Clears any error status (perhaps left over from a previous session)."""
    while (get_status() != __DFU_STATE_DFU_IDLE):
        __dev.ctrl_transfer(0x21, __DFU_CLRSTATUS, 0, __DFU_INTERFACE, None, __TIMEOUT)
        time.sleep(0.100)


def get_status():
    """Get the status of the last operation."""
    stat = __dev.ctrl_transfer(0xA1, __DFU_GETSTATUS, 0, __DFU_INTERFACE, 6, 20000)
    #print ("DFU Status: ", __DFU_STATUS[stat[4]])
    return stat[4]


def mass_erase():
    """Performs a MASS erase (i.e. erases the entire device."""
    # Send DNLOAD with first byte=0x41
    __dev.ctrl_transfer(0x21, __DFU_DNLOAD, 0, __DFU_INTERFACE,
                        "\x41", __TIMEOUT)

    # Execute last command
    if get_status() != __DFU_STATE_DFU_DOWNLOAD_BUSY:
        raise Exception("DFU: erase failed")

    # Check command state
    if get_status() != __DFU_STATE_DFU_DOWNLOAD_IDLE:
        raise Exception("DFU: erase failed")


def page_erase(addr):
    """Erases a single page."""
    if __verbose:
        print("Erasing page: 0x%x..." % (addr))

    # Send DNLOAD with first byte=0x41 and page address
    buf = struct.pack("<BI", 0x41, addr)
    __dev.ctrl_transfer(0x21, __DFU_DNLOAD, 0, __DFU_INTERFACE, buf, __TIMEOUT)

    # Execute last command
    if get_status() != __DFU_STATE_DFU_DOWNLOAD_BUSY:
        raise Exception("DFU: erase failed")

    # Check command state
    if get_status() != __DFU_STATE_DFU_DOWNLOAD_IDLE:

        raise Exception("DFU: erase failed")


def set_address(addr):
    """Sets the address for the next operation."""
    # Send DNLOAD with first byte=0x21 and page address
    buf = struct.pack("<BI", 0x21, addr)
    __dev.ctrl_transfer(0x21, __DFU_DNLOAD, 0, __DFU_INTERFACE, buf, __TIMEOUT)

    # Execute last command
    if get_status() != __DFU_STATE_DFU_DOWNLOAD_BUSY:
        raise Exception("DFU: set address failed")

    # Check command state
    if get_status() != __DFU_STATE_DFU_DOWNLOAD_IDLE:
        raise Exception("DFU: set address failed")


def write_memory(addr, buf, progress=None, progress_addr=0, progress_size=0):
    """Writes a buffer into memory. This routine assumes that memory has
    already been erased.
    """

    xfer_count = 0
    xfer_bytes = 0
    xfer_total = len(buf)
    xfer_base = addr

    while xfer_bytes < xfer_total:
        if __verbose and xfer_count % 512 == 0:
            print ("Addr 0x%x %dKBs/%dKBs..." % (xfer_base + xfer_bytes,
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
            raise Exception("DFU: write memory failed")

        # Check command state
        if get_status() != __DFU_STATE_DFU_DOWNLOAD_IDLE:
            raise Exception("DFU: write memory failed")

        xfer_count += 1
        xfer_bytes += chunk
