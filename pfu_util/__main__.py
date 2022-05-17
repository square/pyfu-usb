"""Command-line interface (CLI) for pfu-util."""

import argparse
import logging
import os
import pkg_resources
import sys

from . import list_devices, mass_erase, download

logger = logging.getLogger(__name__)


def main():
    """CLI entry-point."""
    parser = argparse.ArgumentParser(
        description="Python device firmware update utility."
    )
    parser.add_argument(
        "-D",
        "--download",
        dest="file",
        help="Write firmware from <file> into device",
        required=False,
    )
    parser.add_argument(
        "-d",
        "--device",
        dest="device",
        help="Specify vendor and product ID of DFU device as <vid>:<pid>",
        required=False,
    )
    parser.add_argument(
        "-a",
        "--address",
        dest="address",
        help="Specify device address in hex for binary download or mass erase",
        required=False,
    )
    parser.add_argument(
        "-m",
        "--mass-erase",
        dest="erase",
        help="Erase the whole DFU device",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-l",
        "--list",
        dest="list",
        help="List available DFU devices",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-V",
        "--version",
        dest="version",
        help="Print the version number",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        help="Print verbose debug statements",
        action="store_true",
        default=False,
    )

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, stream=sys.stdout, format="%(message)s")

    if args.version:
        logger.info(pkg_resources.require("pfu_util")[0].version)
        return 0

    if args.list:
        list_devices()
        return 0

    # Convert address from hex-string to integer
    if args.address:
        args.address = int(args.address, 16)

    if args.erase:
        if args.address is None:
            logger.error("Device address is required for mass erase.")
            return -1
        else:
            mass_erase(args.address)

    if args.file:
        if not download(args.file, args.address, args.erase):
            logger.error("DFU download failed.")
            return -1

    return 0
