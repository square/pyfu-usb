"""Parse data files for DFU."""

import logging
import re
import struct
import tempfile
import zlib

logger = logging.getLogger(__name__)


def _named(values, names):
    """Creates a dict with `names` as fields, and `values` as values."""
    return dict(zip(names.split(), values))


def _consume(fmt, data, names):
    """Parses the struct defined by `fmt` from `data`, stores the parsed fields
    into a named tuple using `names`. Returns the named tuple, and the data
    with the struct stripped off."""
    size = struct.calcsize(fmt)
    return _named(struct.unpack(fmt, data[:size]), names), data[size:]


def _cstring(string):
    """Extract a null-terminated string from a byte array."""
    return string.decode("utf-8").split("\0", 1)[0]


def _compute_crc(data):
    """Computes the CRC32 value for the data passed in."""
    return 0xFFFFFFFF & -zlib.crc32(data) - 1


def parse_memory_layout(mem_layout_str: str):
    """Parse the memory layout for a DFU device.

    Args:
        mem_layout_str: Memory layout string from `usb.util.get_string`.

    Returns:
        An array which identifies the memory layout. Each entry of the array
        will contain a dictionary with the following keys:
            addr        - Address of this memory segment
            last_addr   - Last address contained within the memory segment.
            size        - Size of the segment, in bytes
            num_pages   - Number of pages in the segment
            page_size   - Size of each page, in bytes
    """
    mem_layout = mem_layout_str.split("/")
    addr = int(mem_layout[1], 0)
    segments = mem_layout[2].split(",")
    seg_re = re.compile(r"(\d+)\*(\d+)(.)(.)")
    result = []
    for segment in segments:
        seg_match = seg_re.match(segment)
        num_pages = int(seg_match.groups()[0], 10)
        page_size = int(seg_match.groups()[1], 10)
        multiplier = seg_match.groups()[2]
        if multiplier == "K":
            page_size *= 1024
        if multiplier == "M":
            page_size *= 1024 * 1024
        size = num_pages * page_size
        last_addr = addr + size - 1
        result.append(
            _named(
                (addr, last_addr, size, num_pages, page_size),
                "addr last_addr size num_pages page_size",
            )
        )
        addr += size
    return result

def parse_bin_file(filename: str, address: str):
    """Reads a BIN file and parses the individual elements from the file.

    Args:
        filename: BIN file.
        address: The address that the element data should be written to.

    Returns:
        An array of elements. Each element is a dictionary with the
        following keys:
            num     - The element index
            address - The address that the element data should be written to.
            size    - The size of the element data.
            data    - The element data.
        If an error occurs while parsing the file, then None is returned.
    """
    logger.info('File: "%s"' % filename)
    try:
        with open(filename, 'rb') as fin:
            data = fin.read()

    except OSError:
        logger.error("PARSE ERROR")
        return

    elements = []
    element = {"num": 0, "address": address, "size": len(data), "data": data}
    elements.append(element)

    return elements



def parse_dfu_file(filename: str):
    """Reads a DFU file and parses the individual elements from the file.

    Args:
        filename: DFU file.

    Returns:
        An array of elements. Each element is a dictionary with the
        following keys:
            num     - The element index
            address - The address that the element data should be written to.
            size    - The size of the element data.
            data    - The element data.
        If an error occurs while parsing the file, then None is returned.
    """
    logger.info("File: {}".format(filename))
    with open(filename, "rb") as fin:
        data = fin.read()
    crc = _compute_crc(data[:-4])
    elements = []

    # Decode the DFU Prefix
    #
    # <5sBIB
    #   <   little endian
    #   5s  char[5]     signature   "DfuSe"
    #   B   uint8_t     version     1
    #   I   uint32_t    size        Size of the DFU file (not including suffix)
    #   B   uint8_t     targets     Number of targets
    dfu_prefix, data = _consume(
        "<5sBIB", data, "signature version size targets"
    )
    logger.info(
        "    %(signature)s v%(version)d, image size: %(size)d, "
        "targets: %(targets)d" % dfu_prefix
    )
    for target_idx in range(dfu_prefix["targets"]):
        # Decode the Image Prefix
        #
        # <6sBI255s2I
        #   <   little endian
        #   6s      char[6]     signature   "Target"
        #   B       uint8_t     altsetting
        #   I       uint32_t    named       bool indicating if a name was used
        #   255s    char[255]   name        name of the target
        #   I       uint32_t    size        size of image (not incl prefix)
        #   I       uint32_t    elements    Number of elements in the image
        img_prefix, data = _consume(
            "<6sBI255s2I",
            data,
            "signature altsetting named name " "size elements",
        )
        img_prefix["num"] = target_idx
        if img_prefix["named"]:
            img_prefix["name"] = _cstring(img_prefix["name"])
        else:
            img_prefix["name"] = ""
        logger.info(
            "    %(signature)s %(num)d, alt setting: %(altsetting)s, "
            'name: "%(name)s", size: %(size)d, elements: %(elements)d'
            % img_prefix
        )

        target_size = img_prefix["size"]
        target_data, data = data[:target_size], data[target_size:]
        for elem_idx in range(img_prefix["elements"]):
            # Decode target prefix
            #   <   little endian
            #   I   uint32_t    element address
            #   I   uint32_t    element size
            elem_prefix, target_data = _consume("<2I", target_data, "addr size")
            elem_prefix["num"] = elem_idx
            logger.info(
                "      %(num)d, address: 0x%(addr)08x, size: %(size)d"
                % elem_prefix
            )
            elem_size = elem_prefix["size"]
            elem_data = target_data[:elem_size]
            target_data = target_data[elem_size:]
            elem_prefix["data"] = elem_data
            elements.append(elem_prefix)

        if len(target_data):
            logger.error("target %d PARSE ERROR" % target_idx)

    # Decode DFU Suffix
    #   <   little endian
    #   H   uint16_t    device  Firmware version
    #   H   uint16_t    product
    #   H   uint16_t    vendor
    #   H   uint16_t    dfu     0x11a   (DFU file format version)
    #   3s  char[3]     ufd     'UFD'
    #   B   uint8_t     len     16
    #   I   uint32_t    crc32
    dfu_suffix = _named(
        struct.unpack("<4H3sBI", data[:16]),
        "device product vendor dfu ufd len crc",
    )
    logger.info(
        "    usb: %(vendor)04x:%(product)04x, device: 0x%(device)04x, "
        "dfu: 0x%(dfu)04x, %(ufd)s, %(len)d, 0x%(crc)08x" % dfu_suffix
    )
    if crc != dfu_suffix["crc"]:
        logger.error("CRC ERROR: computed crc32 is 0x%08x" % crc)
        return
    data = data[16:]
    if data:
        logger.error("PARSE ERROR")
        return

    return elements
