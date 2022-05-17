"""Command-line interface (CLI) for pfu-util."""

import argparse
import logging
import os
import pkg_resources

from . import list_dfu_devices, mass_erase, write_bin, write_dfu, exit_dfu

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
    logging.basicConfig(level=log_level, stream=sys.stdout)

    if args.version:
        logger.info(pkg_resources.require("pfu_util")[0].version)
        return

    if args.list:
        list_dfu_devices()
        return

    if args.erase:
        if args.address is None:
            logger.error("Device address is required for mass erase.")
            return
        else:
            mass_erase(address)

    if args.file:
        ext = os.path.splitext(args.file)[1]
        if ext == ".bin":
            logger.debug("Writing bin file...")
            write_bin(int(args.address, 16), args.file, args.erase)

            logger.debug("Exiting DFU...")
            exit_dfu()
        elif ext == ".dfu":
            logger.debug("Writing dfu file...")
            write_dfu(args.file, args.erase)

            logger.debug("Exiting DFU...")
            exit_dfu()
        else:
            logger.error("File format %s not supported.", ext)
